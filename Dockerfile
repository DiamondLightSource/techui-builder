# The developer stage is used as a devcontainer including dev versions
# of the build dependencies
FROM ghcr.io/diamondlightsource/ubuntu-devcontainer:noble AS developer
# RUN apt-get update -y && apt-get install -y --no-install-recommends \
#     libevent-dev \
#     libreadline-dev

# The build stage makes some assets using the developer tools
FROM developer AS build
# Copy only dependency files first
COPY pyproject.toml uv.lock /assets/
WORKDIR /assets

ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /assets/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# The runtime stage installs runtime deps then copies in built assets
# This time we remove the apt lists to save disk space
FROM ubuntu:noble AS runtime
# RUN apt-get update -y && apt-get install -y --no-install-recommends \
#     libevent-2.1-7t64 \
#     libreadline8 \
#     && rm -rf /var/lib/apt/lists/*
COPY --from=build /assets /

# We need to keep the venv at the same absolute path as in the build stage
COPY --from=build /assets/.venv/ .venv/
ENV PATH=.venv/bin:$PATH

# Change this entrypoint if it is not the same as the repo
ENTRYPOINT ["techui-builder"]
CMD ["--version"]
