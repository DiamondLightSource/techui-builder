# The devcontainer should use the developer target and run as root with podman
# or docker with user namespaces.
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION} AS developer

# Add any system dependencies for the developer/build environment here
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz vim \
    && rm -rf /var/lib/apt/lists/*
# Install uv using the official installer script
RUN curl -LsSf https://astral.sh/uv/install.sh | \
    env UV_INSTALL_DIR="/usr/local/bin" sh
RUN wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq \
    && chmod +x /usr/local/bin/yq


# Configure environment
ENV UV_CHECK_UPDATE=false
# Configure UV to use system Python
# ENV UV_SYSTEM_PYTHON=1

# Creates virtual environment
RUN uv venv --seed venv
ENV VIRTUAL_ENV=/venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH

# The build stage installs the context into the venv
FROM developer AS build
COPY . /context
WORKDIR /context

# install dependencies and project into the local packages directory
RUN touch dev-requirements.txt && uv pip install -c dev-requirements.txt .

# The runtime stage copies the built venv into a slim runtime container
FROM python:${PYTHON_VERSION}-slim AS runtime
# Add apt-get system dependecies for runtime here if needed
COPY --from=build /venv/ /venv/
ENV VIRTUAL_ENV=/venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH

# change this entrypoint if it is not the same as the repo
ENTRYPOINT ["techui-builder"]
CMD ["--version"]
