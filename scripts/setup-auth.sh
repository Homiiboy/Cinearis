#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v openssl >/dev/null; then
  echo "OpenSSL fehlt. Bitte auf dem Host installieren." >&2
  exit 1
fi
mkdir -p config
read -r -p 'Cinearis-Benutzername [cinearis]: ' username
username="${username:-cinearis}"
if [[ ! "$username" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
  echo "Ungültiger Benutzername" >&2
  exit 1
fi
read -r -s -p 'Cinearis-Passwort (mind. 12 Zeichen): ' password
printf '\n'
if (( ${#password} < 12 )); then
  echo "Bitte mindestens 12 Zeichen verwenden." >&2
  exit 1
fi
hash="$(printf '%s' "$password" | openssl passwd -apr1 -stdin)"
printf '%s:%s\n' "$username" "$hash" > config/nginx.htpasswd
chmod 600 config/nginx.htpasswd
unset password hash
echo "Benutzer eingerichtet: $username. Zugang liegt in config/nginx.htpasswd."
