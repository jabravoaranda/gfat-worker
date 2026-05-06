#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gfat-worker/repo}"
ENV_FILE="${ENV_FILE:-/opt/gfat-worker/.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-compose.prod.yml}"
BRANCH="${BRANCH:-main}"
REMOTE="${REMOTE:-origin}"

cd "$APP_DIR"

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing environment file: $ENV_FILE" >&2
    echo "Create it from .env.example before deploying." >&2
    exit 1
fi

previous_commit="$(git rev-parse HEAD)"
target_ref="${1:-$REMOTE/$BRANCH}"

echo "Fetching $REMOTE..."
git fetch --prune "$REMOTE"

echo "Current commit: $previous_commit"
echo "Deploy target:   $target_ref"

git checkout --detach "$target_ref"
new_commit="$(git rev-parse HEAD)"
echo "$previous_commit" > .deploy-previous-commit

echo "Building and starting containers..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build --remove-orphans

echo "Waiting for API health..."
api_bind="$(grep -E '^API_BIND=' "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
api_port="$(grep -E '^API_PORT=' "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
api_bind="${api_bind:-127.0.0.1}"
api_port="${api_port:-8000}"

deadline=$((SECONDS + 90))
until curl -fsS "http://${api_bind}:${api_port}/" >/dev/null; do
    if [ "$SECONDS" -ge "$deadline" ]; then
        echo "API did not become healthy. Rolling back to $previous_commit." >&2
        git checkout --detach "$previous_commit"
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build --remove-orphans
        exit 1
    fi
    sleep 3
done

echo "Deployment OK: $new_commit"
