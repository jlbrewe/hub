"""
Module that defines the interface between the `manager` (i.e Django) and the `broker` (i.e. RabbitMQ).

Defines three functions involved in a job's lifecycle:

- `dispatch_job` - send a job to a queue
- `update_job` - update the status of a job by checking it's (intermediate) result
- `check_job` - for a parent job, trigger any child jobs, and / or update it's status
- `cancel_job` - remove job from the queue, or terminate it if already started

"""
import datetime
import logging
import time

from celery import Celery, signature
from celery.result import AsyncResult
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from jobs.models import Job, JobMethod, JobStatus, Queue, Worker

logger = logging.getLogger(__name__)

# Setup the Celery app
app = Celery("manager", broker=settings.BROKER_URL, backend=settings.CACHE_URL)
app.conf.update(
    # By default Celery will keep on trying to connect to the broker forever
    # This overrides that. Initially try again immediately, then add 0.5 seconds for each
    # subsequent try (with a maximum of 3 seconds).
    # See https://github.com/celery/celery/issues/4296
    broker_transport_options={
        "max_retries": 10,
        "interval_start": 0,
        "interval_step": 0.5,
        "interval_max": 3,
    },
    # Needed to ensure STARTED state is emitted
    task_track_started=True,
)


def dispatch_job(job: Job) -> Job:
    """
    Send a job to a queue.

    Decides which queue a job should be sent to and sends it.
    The queue can depend upon both the project and the account (either the
    account that the project is linked to, or the default account of the job
    creator).
    """
    if not JobMethod.is_member(job.method):
        raise ValueError("Unknown job method '{}'".format(job.method))

    if job.method in settings.JOB_METHODS_STAFF_ONLY and (
        not job.creator or not job.creator.is_staff
    ):
        raise PermissionDenied

    if JobMethod.is_compound(job.method):
        children = job.children.all().order_by("id")
        if len(children) == 0:
            # If there are no children (e.g. a pull job for a project with no sources)
            # then job is immediately finished
            job.runtime = 0
            job.is_active = False
            job.status = JobStatus.SUCCESS.value
        else:
            if job.method == JobMethod.parallel.value:
                # Dispatch all child jobs simultaneously
                for child in children:
                    dispatch_job(child)
            else:
                # Dispatch the first child; subsequent children
                # will be status WAITING and will get dispatched later
                # on update of the parent.
                for index, child in enumerate(children):
                    if index == 0:
                        dispatch_job(child)
                    else:
                        child.is_active = True
                        child.status = JobStatus.WAITING.value
                        child.save()

            job.is_active = True
            job.status = JobStatus.DISPATCHED.value
    else:
        # Find queues that have active workers on them
        # order by descending priority
        queues = list(
            Queue.objects.filter(
                workers__in=Worker.objects.filter(
                    # Has not finished
                    finished__isnull=True,
                    # Has been updated in the last x minutes
                    updated__gte=timezone.now() - datetime.timedelta(minutes=15),
                ),
            ).order_by("priority")
        )

        # Fallback to the default Stencila queue
        # Apart from anything else having this fallback is useful in development
        # because if means that the `overseer` service does not need to be running
        # in order keep track of the numbers of workers listening on each queue
        # (during development `worker`s listen to the default queue)
        if len(queues) == 0:
            logger.warning("No queues found with active workers")
            queue, _ = Queue.get_or_create(
                account_name="stencila", queue_name="default"
            )
        else:
            if job.creator is None or job.project is None:
                # Jobs created by anonymous users go on the lowest
                # priority queue
                priority = 1
            else:
                # The priority of other jobs is determined by the
                # account tier of the project
                priority = job.project.account.tier.id
            queue = queues[min(len(queues), priority) - 1]

        # Add the job's project id, key and secrets to it's kwargs.
        # Doing this here ensures it is done for all jobs
        # and avoids putting the secrets in the job's `params` field.
        kwargs = dict(**job.params) if job.params else {}
        kwargs["project"] = job.project.id if job.project else None
        kwargs["key"] = job.key
        kwargs["secrets"] = job.secrets

        # Send the job to the queue
        task = signature(
            job.method, kwargs=kwargs, queue=queue.name, task_id=str(job.id), app=app,
        )
        task.apply_async()

        job.queue = queue
        job.is_active = True
        job.status = JobStatus.DISPATCHED.value

    job.save()
    return job


def update_job(job: Job, data={}, force: bool = False) -> Job:
    """
    Update a job.

    This method is triggered by a PATCH request from the
    `overseer` service. It updates the status, and other fields of
    the job, and if the job has a parent, updates it's status too.

    See https://stackoverflow.com/a/38267978 for important considerations
    in using AsyncResult.
    """
    # Avoid unnecessary update
    if not job.is_active and not force:
        return job

    was_active = job.is_active

    if JobMethod.is_compound(job.method):
        # Update the status of compound jobs based on children
        status = job.status
        is_active = False
        all_previous_succeeded = True
        any_previous_failed = False
        for child in job.get_children():
            # If the child has a 'higher' status then update the
            # status of the compound job
            status = JobStatus.highest([status, child.status])

            # If the child is still waiting then...
            if child.status == JobStatus.WAITING.value:
                # If all previous have succeeded, dispatch it
                if all_previous_succeeded:
                    dispatch_job(child)
                # If any previous have failed, cancel it
                elif any_previous_failed:
                    cancel_job(child)

            if child.status != JobStatus.SUCCESS.value:
                all_previous_succeeded = False
            if child.status == JobStatus.FAILURE.value:
                any_previous_failed = True

            # If the child is still active then the compound job is active
            if child.is_active:
                is_active = True

        job.is_active = is_active
        job.status = JobStatus.RUNNING.value if is_active else status

    else:
        status = data.get("status")
        assert status

        # Do not do anything if the new status is lower rank than the
        # existing status. This can exist for example when a job is
        # terminated (the SUCCESS state is sent after TERMINATED)
        if JobStatus.rank(status) < JobStatus.rank(job.status):
            return job

        # Update fields sent by `overseer` service, including `status`
        for key, value in data.items():
            setattr(job, key, value)

        def async_result():
            return AsyncResult(str(job.id), app=app)

        # If job succeeded then get the result if we haven't already
        if status == JobStatus.SUCCESS.value and job.result is None:
            response = None
            attempts = 0
            while not response and attempts < 5:
                try:
                    response = async_result().get(timeout=30)
                except Exception:
                    # Catch all errors, but log them. Occasional
                    # errors encountered in prod include ResponseError and TimeoutError
                    logger.warning(
                        "Error getting async result",
                        exc_info=True,
                        extra=dict(id=job.id, method=job.method, attempts=attempts),
                    )
                    time.sleep(1)
                    attempts += 1

            if response:
                job.result = response.get("result")
                job.log = response.get("log")
            else:
                logger.error(
                    "Unable to get async result",
                    extra=dict(id=job.id, method=job.method, attempts=attempts),
                )
                job.status = JobStatus.FAILURE.value
                job.error = dict(
                    type="RuntimeError", message="Unable to get result of job"
                )

        # If job failed then get the error
        # For FAILURE, `info` is the raised Exception
        elif status == JobStatus.FAILURE.value:
            info = async_result().info
            if info:
                job.error = dict(type=type(info).__name__, message=str(info))

        # If the job has just ended then mark it as inactive
        if JobStatus.has_ended(status):
            job.is_active = False

    # If the job is no longer active clear its secrets and run its callback
    if was_active and not job.is_active:
        job.secrets = None
        job.run_callback()

    # Save before updating parent (and then this again)
    job.save()

    # If the job has a parent then update it too
    if job.parent:
        update_job(job.parent)

    return job


def cancel_job(job: Job) -> Job:
    """
    Cancel a job.

    This uses Celery's terminate options which will kill the worker child process.
    This is not normally recommended but in this case is OK because there is only
    one task per process.
    See `worker/worker.py` for the reasoning for using `SIGUSR1`.
    See https://docs.celeryproject.org/en/stable/userguide/workers.html#revoke-revoking-tasks
    """
    if job.is_active:
        if JobMethod.is_compound(job.method):
            for child in job.children.all():
                cancel_job(child)
        else:
            app.control.revoke(str(job.id), terminate=True, signal="SIGUSR1")
        job.status = JobStatus.CANCELLED.value
        job.is_active = False
        job.secrets = None
        job.save()
    return job
