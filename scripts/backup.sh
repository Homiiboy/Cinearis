#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
destination="backups/cinearis-$stamp.sql.gz"
# PostgreSQL runs with the Compose-defined credentials inside the container.
docker compose exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl' | gzip -9 > "$destination"
gzip -t "$destination"
chmod 600 "$destination"
echo "Backup: $destination"
