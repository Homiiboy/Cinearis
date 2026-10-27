#!/usr/bin/env sh
set -eu
mkdir -p config
if ! command -v openssl >/dev/null 2>&1; then
  echo "OpenSSL fehlt. Bitte installieren." >&2
  exit 1
fi
printf 'Cinearis-Benutzername [cinearis]: '
read -r username
username=${username:-cinearis}
case "$username" in *[!a-zA-Z0-9_.-]*|'') echo "Ungültiger Benutzername"; exit 1;; esac
printf 'Passwort (Eingabe sichtbar): '
read -r password
if [ "${#password}" -lt 12 ]; then echo "Passwort muss mindestens 12 Zeichen haben."; exit 1; fi
hash=$(printf '%s' "$password" | openssl passwd -apr1 -stdin)
printf '%s:%s\n' "$username" "$hash" > config/nginx.htpasswd
chmod 600 config/nginx.htpasswd
unset password hash
echo "Zugangsdaten in config/nginx.htpasswd gespeichert (nicht ins Git-Repository)."
