pip install --upgrade pip
pdm python install
pdm venv create --force
pdm use -f .venv
pdm install -G dev
