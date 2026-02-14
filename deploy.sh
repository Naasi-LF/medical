#!/usr/bin/env bash
set -euo pipefail

branch="${1:-}"

if [[ -n "$branch" ]]; then
  git pull origin "$branch"
else
  git pull
fi

docker compose up -d --build
docker compose ps
