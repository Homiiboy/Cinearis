# Cinearis v0.1.0 – Installation (ZimaOS / Linux)

## Voraussetzungen
- Docker und Docker Compose Plugin
- Freier TCP-Port 8088 (oder eigener Port in `.env`)
- Internetzugang für das erstmalige Herunterladen der Container-Images

## Start
```bash
git clone https://github.com/Homiiboy/Cinearis.git
cd Cinearis
cp .env.example .env
# Wichtig: POSTGRES_PASSWORD in .env auf ein starkes Passwort ändern!
docker compose up -d --build
docker compose ps
```

Öffne `http://<DEINE-SERVER-IP>:8088` im Browser.

## Funktion prüfen
```bash
curl http://localhost:8088/api/live
curl http://localhost:8088/api/health
curl http://localhost:8088/api/dashboard
docker compose logs --tail=100 backend
```
Die Gesundheitsabfrage zeigt `database: connected`, sobald die Verbindung zur PostgreSQL-Datenbank funktioniert.

## Aktualisieren
```bash
git pull
docker compose up -d --build
```

## Stoppen / Daten behalten
```bash
docker compose down
```
**Achtung:** `docker compose down -v` löscht das Datenbank-Volume samt Inhalt.

## Lokale Entwicklung
Backend: Python 3.12, virtuelle Umgebung anlegen, `pip install -r backend/requirements.txt` und `uvicorn app.main:app --reload` aus `backend/` ausführen. Ohne `DATABASE_URL` wird SQLite genutzt.

Frontend: `cd frontend && npm install && npm run dev`. Vite leitet `/api` an localhost:8000 weiter.

## Sicherheitsgrenzen von Phase 1
- Die Anwendung ist noch **ohne Benutzeranmeldung**. Nur im vertrauenswürdigen Heimnetz oder hinter zusätzlicher Zugriffskontrolle betreiben; nicht direkt ins Internet stellen.
- Keine Instagram-, KI-, Jellyfin- oder ForgeCore-Integration in v0.1.0.
- PostgreSQL ist ausschließlich intern verfügbar und wird nicht als Port auf dem Host freigegeben.
- Für spätere Schemaänderungen sind versionierte Datenbankmigrationen vorgesehen.

## Medien manuell hinzufügen (v0.1.1)

Unter **Entdecken** den Medientyp auswählen und einen Namen eingeben. Animes werden über AniList gesucht. Für Film- und Seriensuche in `.env` einen eigenen `TMDB_API_KEY` eintragen und `docker compose up -d --build` erneut ausführen. Alternativ können Titel ohne externen Anbieter über **Manuell hinzufügen** gespeichert werden.

Unter **Meine Sammlung** einen Titel anklicken: Mediathekstatus und Sehfortschritt lassen sich getrennt verwalten. Filme erlauben *Gesehen* / *Nicht gesehen*. Serien/Anime unterstützen außerdem *Bis zu einer Folge* (Staffel plus Episode) sowie *Staffel vollständig gesehen* (Staffelnummer). Der aktuelle Stand beschreibt jeweils nur einen Fortschrittspunkt, noch keine vollständige staffelübergreifende Seh-Historie.

Vor dem Update vorhandene PostgreSQL-Daten sichern. Das Backend ergänzt fehlende Datenbankspalten beim Start; es löscht die bisherige Sammlung nicht.


## Phase 2 – Bilder hochladen und analysieren (v0.2.0)

Öffne **Entdecken → Bilderkennung**. Bis zu acht PNG-, JPG- oder WEBP-Dateien können hochgeladen werden (maximal 8 MB pro Datei, maximal 16 Megapixel). Bilder werden nur im Arbeitsspeicher verarbeitet und nicht als Originaldateien gespeichert.

**Lokaler OCR-Betrieb (Standard):** Die Docker-Images enthalten Tesseract mit Deutsch und Englisch. Ohne `VISION_API_KEY` werden ausschließlich Textzeilen als unbestätigte Vorschläge erkannt. Bei reinen Szenen oder Charakteren kann OCR keine verlässlichen Titel ermitteln.

**Optionale Vision-KI:** Trage in deiner lokalen `.env` die Werte `VISION_API_KEY` (API-Schlüssel des OpenAI-Dienstes) und optional `VISION_MODEL` ein. Standardmäßig wird `gpt-4.1-mini` verwendet. Nach `docker compose up -d --build` werden ausgewählte Bilder zusätzlich zur externen Bilderkennung übertragen. Prüfe vorher Datenschutz und mögliche API-Kosten. Der Schlüssel bleibt ausschließlich im Backend; er wird nicht an den Browser geschickt.

Beispiel:
```dotenv
VISION_API_KEY=DEIN_API_SCHLUESSEL
VISION_MODEL=gpt-4.1-mini
```

Die KI-Ergebnisse werden nach Erkennungswahrscheinlichkeit sortiert. Alle Vorschläge lassen sich korrigieren, klassifizieren, auswählen und in die Sammlung übernehmen. Nur explizit ausgewählte Treffer werden gespeichert. OCR-Zeilen sind bewusst niedrig bewertet und standardmäßig **nicht** vorausgewählt.

API:
- `GET /api/analysis/config` – OCR-/Vision-Status und Uploadlimits
- `POST /api/analysis/images` – Multipart mit Feld `files` (1–8 Bilder)
- `POST /api/media` – bestätigten Titel speichern (bereits aus v0.1.1)

**Grenzen:** Version 0.2.0 verifiziert erkannte Namen noch nicht automatisch mit TMDB/AniList; dafür ist Phase 3 vorgesehen. OCR-/KI-Konfidenz ist eine Heuristik, keine garantierte Treffergenauigkeit. Es gibt noch keine dauerhafte Importhistorie und keine Benutzeranmeldung. Der Dienst darf nicht ungeschützt öffentlich betrieben werden.
