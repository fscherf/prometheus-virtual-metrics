FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSIONS="3.9 3.10 3.11 3.12 3.13"
ARG PYTHON_VERSION="3.13"

ENV PYTHONUNBUFFERED=1

RUN apt update && \
	apt install -y --no-install-recommends \
		software-properties-common \
		make \
		bash \
		git \
		curl \
		wget \
		iputils-ping && \
	add-apt-repository ppa:deadsnakes/ppa && \
	apt update && \
	for version in ${PYTHON_VERSIONS}; do \
		apt install -y --no-install-recommends \
			python${version} \
			python${version}-dev \
			python${version}-venv && \
		python${version} -m ensurepip --upgrade \
	; done && \
	ln -s $(which python${PYTHON_VERSION}) /usr/local/bin/python3 && \
	python${PYTHON_VERSION} -m pip install \
		build \
		twine \
		tox \
		rlpython \
	&& rm -rf /var/lib/apt/lists/*
