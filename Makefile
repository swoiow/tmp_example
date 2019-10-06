initvenv:
    python3 -m venv .venv

# Docker
build:
    docker build -t auth-server . --no-cache --pull