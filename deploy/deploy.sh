#!/usr/bin/env sh
set -eu

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repository_root"

if [ ! -f .env ]; then
  echo "Missing .env. Copy .env.example to .env and review it before deploying." >&2
  exit 1
fi

docker compose config --quiet
docker compose build --pull
docker compose up -d --remove-orphans
docker compose ps
