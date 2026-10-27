# Cinearis v1.0.0 – Release-Checkliste

**Status: Release Candidate, ungetestet auf ZimaOS.** Nicht als produktionsreif einstufen, bevor alle Prüfungen bestanden sind.

- [ ] `docker compose config` erfolgreich
- [ ] `docker compose up -d --build` erfolgreich
- [ ] nginx-Basic-Auth verweigert Zugriffe ohne Kennwort
- [ ] HTTPS über Reverse-Proxy eingerichtet, bevor Zugriff außerhalb des lokalen Netzes erfolgt
- [ ] `/api/health` nur mit Anmeldung erreichbar und zeigt Datenbankverbindung
- [ ] Filme, Serien und Anime manuell hinzufügen und suchen
- [ ] OCR mit PNG/JPEG/WEBP sowie optionale Vision-Bilderkennung
- [ ] Dublettenvermeidung und TMDB/AniList-Zuordnung
- [ ] Episoden und Specials speichern
- [ ] Jellyfin-Scan, Staffel-/Episodenabgleich, keine Veränderung in Jellyfin
- [ ] Instagram-Screenshot-Import und Quellenhistorie
- [ ] Insights ohne Test-/Dummy-Werte
- [ ] ForgeCore-Export JSON/CSV im Browser herunterladen und prüfen
- [ ] Optionale direkte ForgeCore-1.8.5-Merkliste mit TMDB-Testtitel prüfen (monitored=false, kein Download)
- [ ] PWA-Installation im Browser; HTTPS bzw. localhost nötig für Service Worker
- [ ] `bash scripts/backup.sh` erstellt gültigen Dump
- [ ] Restore-Übung mit separater Test-Datenbank
- [ ] Datenpersistenz nach `docker compose down && docker compose up -d`
- [ ] `python -m unittest discover -s tests -v` im Backend erfolgreich
- [ ] `npm run build` im Frontend erfolgreich
- [ ] Mobile Layout, Login und Bild-Upload testen
- [ ] API-Tokens in `.env`, keine Secrets im Git-Verlauf

**Bekannte Grenzen:** Direkter ForgeCore-Watchlist-Vertrag aus v1.8.5 wurde im Repository geprüft, aber die reale Verbindung mit deinem Server ist noch nicht verifiziert; CSV/JSON bleiben als Fallback. Instagram-Links werden nicht gescrapt. Keine Mehrbenutzerverwaltung. Der lokale Jellyfin-Snapshot ist möglicherweise veraltet. Automatisierte Datenbankmigrationen werden noch durch einfache Schema-Erweiterungen abgedeckt. PWA speichert nur die App-Shell, keine Mediendaten offline.
