# The devcontainer should use the developer target and run as root with podman
# or docker with user namespaces.
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION} AS developer

# Add any system dependencies for the developer/build environment here
RUN apt-get update && apt upgrade -y && rm -rf /var/lib/apt/lists/*
RUN wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq \
    && chmod +x /usr/bin/yq

COPY . ./
COPY src/phoebus_guibuilder ./phoebus_guibuilder
RUN touch README.md

# # Set up a virtual environment and put it in PATH
# RUN python -m venv /venv
# ENV PATH=/venv/bin:$PATH

# # The build stage installs the context into the venv
# FROM developer AS build
# COPY . /context
# WORKDIR /context
# RUN touch dev-requirements.txt && pip install -c dev-requirements.txt .

# # The runtime stage copies the built venv into a slim runtime container
# FROM python:${PYTHON_VERSION}-slim AS runtime
# # Add apt-get system dependecies for runtime here if needed
# COPY --from=build /venv/ /venv/
# ENV PATH=/venv/bin:$PATH

# change this entrypoint if it is not the same as the repo
ENTRYPOINT ["phoebus-guibuilder"]
CMD ["--version"]
