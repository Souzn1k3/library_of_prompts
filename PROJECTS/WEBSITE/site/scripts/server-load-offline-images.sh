#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${1:-$(pwd)}"
IMAGES_DIR="$ROOT_DIR/images"

if [[ ! -d "$IMAGES_DIR" ]]; then
  echo "Images directory not found: $IMAGES_DIR" >&2
  exit 1
fi

for image_tar in "$IMAGES_DIR"/*.tar; do
  echo "[offline] loading $image_tar"
  docker load -i "$image_tar"
done

if [[ ! -f "$ROOT_DIR/.env" && -f "$ROOT_DIR/.env.example" ]]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

docker compose -f "$ROOT_DIR/docker-compose.yml" --env-file "$ROOT_DIR/.env" up -d
docker compose -f "$ROOT_DIR/docker-compose.yml" --env-file "$ROOT_DIR/.env" ps
