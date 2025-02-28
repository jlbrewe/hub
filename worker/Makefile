# Shortcut to refer to programs in the virtual environment during development
VE := venv/bin

# Python command to use for venv setup
PYTHON ?= python3

# Build virtual environment (Python and Node packages)
venv: requirements.txt requirements-dev.txt package.json
	$(PYTHON) -m venv venv
	$(VE)/pip3 install -r requirements.txt
	$(VE)/pip3 install -r requirements-dev.txt
	touch venv
	npm install

# Format code
format: venv
	$(VE)/black .
	$(VE)/isort .

# Lint code
lint: venv
	$(VE)/black --check .
	$(VE)/isort --check .
	$(VE)/flake8
	$(VE)/mypy --config-file pyproject.toml --exclude venv .
	$(VE)/pydocstyle --match-dir='^(?!venv)'

# Run tests
test: venv
	$(VE)/pytest --ignore=node_modules --ignore venv --ignore projects

# Run tests with coverage
cover: venv
	$(VE)/pytest --ignore=node_modules  --ignore venv --ignore projects \
	             --cov=. --cov-report term --cov-report html --cov-report xml

# Run smoke tests
smoke: build
	# Tests to ensure that Encoda runs OK within the `hub-worker` Docker container
	# See https://github.com/stencila/hub/issues/987 for an example of a bug
	# that this is meant to catch.

	# Can convert to some common formats
	docker run --rm stencila/hub-worker \
		encoda convert "Hello" --from md temp.md temp.ipynb temp.html temp.docx

	# Can convert to formats that rely on Puppeteer
	docker run --rm stencila/hub-worker \
		encoda convert --debug "Hello" --from md temp.png temp.pdf


# Run `celery worker` during development to check configuration.
# Falls back to using RPC result backend, add
# 	CACHE_URL=redis://stencila:password@localhost:6379/0
# to use Redis instead
# Uses timestamp to generate unique hostnames for workers.
# Uses low concurrency for testing of queuing.
run: venv
	BROKER_URL=amqp://stencila:password@localhost:5672/stencila \
	CACHE_URL=redis://stencila:password@localhost:6379/0 \
	WORKER_CONCURRENCY=3 \
	$(VE)/celery --app=worker worker \
		--loglevel DEBUG \
		--hostname worker-$$(date +'%s')@%h \
		--heartbeat-interval 60

# Build Docker image
build:
	docker build --tag stencila/hub-worker .

build-groundsman:
	cd jobs/session && docker build --tag stencila/hub-groundsman -f groundsman.Dockerfile .

# Run Docker image during development
run-docker: build
	docker run --rm -it --network=host \
		--env BROKER_URL=amqp://stencila:password@localhost:5672/stencila \
		--env CACHE_URL=redis://stencila:password@localhost:6379/0 \
		--env STORAGE_ROOT=/storage \
		-v $$PWD/../storage/data:/storage:rw \
		stencila/hub-worker

# Clean up venv and cached files
clean:
	rm -rf venv
	find . | grep -E "(__pycache__|\.pyc$$)" | xargs rm -rf
