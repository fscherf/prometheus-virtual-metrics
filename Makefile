IMAGE_NAME=python
PYTHON3=python3.13
PYPIRC=~/.pypirc.fscherf

.PHONY: test-ci test server doc doc-server \
	docker-build docker-logs docker-shell \
	python-build \
	_pypi-upload _doc-upload

define DOCKER_COMPOSE_RUN
	docker compose run \
		-it \
		--user=$$(id -u):$$(id -g) \
		--remove-orphans \
		--service-ports \
		$1 \
		${IMAGE_NAME} \
		$2 \
		${args}
endef


# dev
test-ci:
	$(call DOCKER_COMPOSE_RUN,,tox)

test:
	$(call DOCKER_COMPOSE_RUN,,tox -e ${PYTHON3})

server:
	$(call DOCKER_COMPOSE_RUN,,tox -e server)

doc:
	$(call DOCKER_COMPOSE_RUN,,tox -e doc)

doc-server:
	$(call DOCKER_COMPOSE_RUN,,tox -e doc-server)

grip:
	$(call DOCKER_COMPOSE_RUN,,tox -e grip)


# docker
docker-build:
	docker compose build ${args} ${IMAGE_NAME}

docker-logs:
	docker compose logs -f --no-log-prefix ${IMAGE_NAME}

docker-shell:
	$(call DOCKER_COMPOSE_RUN,,/bin/bash)


# python
python-build:
	rm -rf build dist *.egg-info && \
	$(call DOCKER_COMPOSE_RUN,,python3 -m build)


# release
_pypi-upload:
	$(call DOCKER_COMPOSE_RUN,-v ${PYPIRC}:/.pypirc,twine upload --config-file /.pypirc dist/*)

_doc-upload:
	rsync -avh --recursive --delete \
		doc/site/* pages.fscherf.de:/var/www/virtual/fscherf/pages.fscherf.de/prometheus-virtual-metrics
