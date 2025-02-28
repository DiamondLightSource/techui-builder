# The devcontainer should use the developer target and run as root with podman
# or docker with user namespaces.
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION} AS developer

# Add any system dependencies for the developer/build environment here
RUN apt-get update && apt upgrade -y && rm -rf /var/lib/apt/lists/*
# Install PDM using the official installer script
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq \
    && chmod +x /usr/bin/yq

# The build stage installs the context into the venv
FROM developer AS build
# install uv
RUN pip install -U uv
# disable update check
ENV UV_CHECK_UPDATE=false
# copy files
# * means it will only try to copy uv.lock if it exists already
COPY pyproject.toml uv.lock* README.md LICENSE /project/
COPY src/ /project/src

# install dependencies and project into the local packages directory
WORKDIR /project
RUN uv sync --dev --no-editable

# The runtime stage copies the built venv into a slim runtime container
FROM python:${PYTHON_VERSION}-slim AS runtime
# Add apt-get system dependecies for runtime here if needed
COPY --from=build /project/.venv/ /project/.venv
ENV PATH="/project/.venv/bin:$PATH"

# change this entrypoint if it is not the same as the repo
ENTRYPOINT ["phoebus-guibuilder"]
CMD ["--version"]
