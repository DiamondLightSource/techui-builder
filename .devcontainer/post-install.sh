pip install --upgrade pip
pdm python install
pdm venv create --force --name guibuilder
pdm use --venv guibuilder
pdm install -G dev
