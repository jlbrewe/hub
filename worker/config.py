"""Module for worker and job configuration."""

import os

STORAGE_ROOT = os.environ.get(
    "STORAGE_ROOT", os.path.join(os.path.dirname(__file__), "..", "storage", "data")
)

NODE_MODULES = os.environ.get(
    "NODE_MODULES", os.path.join(os.path.dirname(__file__), "node_modules")
)


def get_working_dir(project: int):
    """
    Get the path to a project's working directory.

    Most jobs are done within the context of a project's
    working directory. This method translates a project integer id
    into a local filesystem path on the worker. This allows
    for workers to customize where the projects are stored.
    """
    return os.path.join(
        os.environ.get("WORKING_ROOT", os.path.join(STORAGE_ROOT, "working")),
        str(project),
    )


def get_snapshot_dir(project: int, snapshot: str) -> str:
    """
    Get the path to a project snapshot directory.

    Snapshots may be on a different filesystem from the project
    working directories.
    """
    return os.path.join(
        os.environ.get("SNAPSHOT_ROOT", os.path.join(STORAGE_ROOT, "snapshots")),
        str(project),
        snapshot,
    )


def get_content_root() -> str:
    """
    Get the root of the content storage.
    """
    return os.environ.get("CONTENT_ROOT", os.path.join(STORAGE_ROOT, "content"))


def get_node_modules_bin(name: str) -> str:
    """
    Get the path to a "bin" script installed in the configured `node_modules`.
    """
    return os.path.join(NODE_MODULES, ".bin", name)


def get_node_modules_path(subpath: str) -> str:
    """
    Get the path to a file within the configured `node_modules`.
    """
    return os.path.join(NODE_MODULES, subpath)
