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


## Phase 3 – Metadaten und Titelzuordnung (v0.3.0)

Unter **Entdecken** liefert die Suche nun erweiterte Metadatenvorschläge. Für Filme und Serien wird **TMDB**, für Anime **AniList** verwendet. Angezeigt werden deutscher bzw. bevorzugter Titel, Originaltitel, alternative Schreibweisen (soweit beim Anbieter hinterlegt), Poster, Erscheinungsjahr, Anbieter und externe ID.

Bei der Bilderkennung einen vorgeschlagenen Titel zunächst klassifizieren, dann **Metadaten suchen** wählen und den richtigen Treffer bestätigen. Erst danach **Geprüfte Titel hinzufügen** betätigen. Das verhindert, dass die Vision-KI einem ähnlich klingenden Titel automatisch eine falsche ID zuweist.

Bereits vorhandene Filme/Serien/Anime: In **Meine Sammlung** den Titel anklicken und **Metadaten / Poster zuordnen** wählen. Die Verknüpfung aktualisiert Titel und Bild, lässt Sehfortschritt und Mediathekstatus aber unverändert.

API:
- `GET /api/metadata/search?kind=movie&q=...` – sortierte Suchvorschläge mit Alternativtiteln und Ähnlichkeitswert
- `GET /api/metadata/detail?provider=tmdb&provider_id=...&kind=movie` – vollständigerer Anbieterdatensatz
- `PATCH /api/media/{id}/metadata` mit `{"provider":"tmdb","provider_id":"123"}` – vom Benutzer bestätigte Zuordnung
- `GET /api/media` – enthält nun `original_title`, `aliases`, `description`, `poster_url` und externe ID

**Wichtig:** Der Ähnlichkeitswert ist ein Textvergleich, kein Nachweis für einen passenden Film. Fremdsprachige Titel sind nur so vollständig wie die Daten des Anbieters. Die Datenbank verknüpft derzeit **eine primäre Anbieter-ID pro Medienobjekt**; automatische Cross-Provider-Zuordnung und Staffel-/Episoden-Metadaten folgen später. Vor Updates bitte das PostgreSQL-Volume sichern.

Tests (im Backend-Verzeichnis nach Installation der Python-Abhängigkeiten):
```bash
python -m unittest discover -s tests -v
```


## Phase 4 – Erweiterte Sammlung (v0.4.0)

- **Meine Sammlung**: Suche nach Titel, Originaltitel oder Alias, Filter nach Medientyp, Medienstatus und Sehstatus; sortiere nach Hinzufügedatum, Titel oder Erscheinungsjahr.
- **Bearbeitung**: Öffne ein Medium und wähle `Erweiterte Bearbeitung / Staffeln & Folgen`. Passe Titel, Beschreibung, Erscheinungsjahr und Mediathekstatus an.
- **Filme**: Schalter `Film gesehen`.
- **Serien/Anime**: Dokumentiere einzelne Episoden und ganze Staffeln unabhängig. Staffel `0` ist für Specials vorgesehen. Trage bei der Staffel-Aktion die **tatsächliche Anzahl Episoden** ein; Cinearis schätzt sie noch nicht automatisch. Staffelbereiche werden nur im angegebenen Episodenumfang verändert.
- **Dubletten**: Neue Einträge werden anhand normalisierter Titel/Originaltitel/Aliasse und exakter Anbieter-IDs überprüft; unklare Titel müssen weiterhin manuell beurteilt werden.

Neue Endpunkte: `PATCH /api/media/{id}`, `GET /api/media/{id}/episodes`, `PUT /api/media/{id}/episodes`, `PUT /api/media/{id}/seasons`, `DELETE /api/media/{id}/episodes`.

**Datenhaltung:** Eine neue Tabelle `episode_progress` speichert einzelne abgehakte Folgen. Alte Einträge werden nicht gelöscht. Die ältere Einstellung `bis Staffel/Folge gesehen` aus v0.1.1 wird **nicht automatisch** in einen detaillierten Episodenverlauf umgewandelt, da die tatsächlichen Staffelgrößen unbekannt sind. Einträge können nachträglich korrekt eingepflegt werden. Bis dahin zeigen ältere Übersichten ggf. noch den bisherigen groben Sehstatus an.

**Achtung:** Die Sammlung wird aktuell im Frontend gefiltert und die API gibt höchstens 1000 Titel zurück. Pagination folgt bei größeren Sammlungen. Vor dem ersten Start und bei Updates immer eine Datenbanksicherung erstellen.

Tests:
```bash
cd backend
python -m unittest discover -s tests -v
```


## Phase 5 – Jellyfin-Abgleich (v0.5.0)

Cinearis verbindet sich **nur lesend** mit deinem vorhandenen Jellyfin-/Velaris-Server. Es werden keine Medien gelöscht, keine Jellyfin-Metadaten geändert und keine Abspielstände geschrieben.

1. Erstelle in Jellyfin im Administrator-Dashboard einen **separaten API-Schlüssel** für Cinearis.
2. Trage im lokalen Cinearis-Ordner in `.env` die beiden Felder ein (keine Zugangsdaten ins öffentliche GitHub-Repository!):

```dotenv
JELLYFIN_URL=http://host.docker.internal:8096
JELLYFIN_API_KEY=HIER_DEIN_JELLYFIN_SCHLUESSEL
```

Wenn Jellyfin in einem eigenen Docker-Netzwerk läuft, kann stattdessen die interne DNS-Adresse des Jellyfin-Containers genutzt werden, sofern Cinearis dasselbe Netzwerk verwendet. Alternativ eine vom Cinearis-Backend-Container erreichbare LAN-Adresse eintragen. `localhost` im Container ist **nicht** dein ZimaOS-Host. Verwende in einem fremden oder öffentlichen Netzwerk HTTPS; die Verbindung soll auf einem vertrauenswürdigen Netzwerk bleiben.

3. Starte neu: `docker compose up -d --build`.
4. Öffne **Meine Sammlung → Jellyfin-Bibliothek → Jetzt mit Jellyfin vergleichen**.
5. Die Karte zeigt die zuletzt gefundenen Filme/Serien/Episoden und den Zeitpunkt des Scans. Die Sammlung markiert eindeutige, fehlende und mehrdeutige Zuordnungen. Ein Klick auf eine Serie zeigt die **in Jellyfin tatsächlich gefundenen** Episodennummern je Staffel.

API:
- `GET /api/jellyfin/status` – Konfiguration und letzter Scan ohne API-Schlüssel
- `POST /api/jellyfin/sync` – synchronisiert einen lokalen Metadaten-Schnappschuss (max. 50.000 Einträge)
- `GET /api/jellyfin/matches` – Vergleiche gegen die aktuelle Cinearis-Sammlung

**Zuordnungsregeln:** TMDB-ID bei Filmen/Serien, wenn verfügbar; andernfalls nur eindeutige normalisierte Titel/Alternativtitel mit plausibler Jahreszahl. Bei Anime wird in dieser Version oft der Name verwendet, da AniList-IDs und Jellyfin-TMDB-IDs nicht direkt identisch sind. Mehrdeutige Treffer werden nicht automatisch aufgelöst. Episoden gehören ausschließlich zu der jeweiligen Jellyfin-`SeriesId`; Staffel 0 bezeichnet Specials.

**Wichtig:** Die existierenden Labels `Wunschliste/Vorhanden` sind persönliche Sammlungsstatus. Der Jellyfin-Abgleich wird **separat** gezeigt und überschreibt diese Werte und den Sehfortschritt nicht. Ohne bekannten Soll-Episodenumfang kann Cinearis nicht sagen, wie viele Folgen insgesamt fehlen; angezeigt werden nur tatsächlich gefundene Episoden. Spezialfälle wie verschachtelte Serien, alternative Staffelzählungen oder gemischte Bibliotheken müssen zuhause getestet werden.

**Sicherheit:** API-Schlüssel hat Zugriff auf Informationen deines Servers. Cinearis besitzt noch keine eigene Anmeldung; daher **nicht öffentlich zugänglich machen**. Ein Jellyfin-API-Schlüssel wird nie an das Frontend übertragen.

**Validierung auf ZimaOS:**
```bash
docker compose config
docker compose up -d --build
curl http://localhost:8088/api/jellyfin/status
curl http://localhost:8088/api/health
docker compose logs --tail=100 backend
```

Zum Aufruf des Scan-Endpunkts eignet sich der Button in der Weboberfläche. Bei Fehlern bleiben zuvor gespeicherte Snapshots bestehen.
