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
