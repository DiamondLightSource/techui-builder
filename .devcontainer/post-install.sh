pip install --upgrade pip
pip install $([ -f dev-requirements.txt ] && echo '-c dev-requirements.txt') -e '.[dev]'
pre-commit install
poetry install
poetry env use 3
