# Cinearis 🎬

<p align="center">
  <img src="assets/Cinearis.png" alt="Cinearis Logo" width="180" />
</p>

**KI-gestützte Entdeckung, Organisation und Verwaltung von Filmen, Serien und Animes.**

Cinearis ist Teil des **Novarion-Ökosystems**. Die selbst gehostete Webanwendung erkennt Titel aus Bildern und – soweit technisch und rechtlich zugänglich – Social-Media-Beiträgen, erstellt eine dauerhaft wachsende persönliche Merkliste und gleicht diese mit **Jellyfin / Velaris** ab. Eine spätere Verbindung zu **ForgeCore** ist geplant.

> **Projektstatus:** **v1.0.0 Release Candidate – Phase 8 implementiert, Integrationstest ausstehend** · Docker-Betrieb auf ZimaOS noch nicht praktisch verifiziert · Automatischer Instagram-Medienabruf ist wegen API-Beschränkungen nicht enthalten; ForgeCore-Export (CSV/JSON) und die optionale, explizite Übernahme einzelner TMDB-Titel in die ForgeCore-v1.8.5-Merkliste sind implementiert.

## ✅ Implementierte Funktionen (v1.0.0 RC)

- **Release-Kandidat (v1.0.0):** ForgeCore-Export als JSON/CSV sowie die bestätigungspflichtige Übergabe einzelner TMDB-Titel in die ForgeCore-Merkliste (ohne automatischen Download), PWA-Manifest mit Offline-Hinweisseite, verpflichtender nginx-Basic-Auth-Zugangsschutz, Backup-Script, Sicherheitsheader und Release-Checkliste.\n- **Insights (v0.7.0):** Echtes Dashboard mit Medienarten, Sammlungs- und Sehstatus, getrackten Episoden, Jellyfin-Abgleich, Instagram-Fundhäufigkeit, Quellenübersicht und monatlichen Zugängen.\n- **Instagram-Import (v0.6.0):** Instagram-Beitrags-/Reel-Links mit Herkunftsangabe speichern, Mehrbild-Screenshots analysieren und bestätigte Medien (auch vorhandene Titel) der Quelle zuordnen; Duplikate vermeiden. Kein automatisches Scraping oder automatischer Bildabruf per Link.\n- **Jellyfin-Bibliotheksabgleich (v0.5.0):** Sichere Konfiguration über Backend-Umgebungsvariablen, manueller Metadaten-Snapshot, eindeutiger TMDB-/Titelabgleich, getrennte Anwesenheitsanzeige, Staffel- und Episodenübersicht; keinerlei Änderungen an Jellyfin oder dem persönlichen Sehfortschritt.\n- **Erweiterte Sammlung (v0.4.0):** Titel, Aliasnamen, Status und Sehstatus filtern; sortieren, Titel/Jahr/Beschreibung bearbeiten, Dubletten mit normalisierten Namen vermeiden, Episoden und Staffeln einzeln abhaken. Specials können als Staffel 0 erfasst werden.\n- **Metadaten-Abgleich (v0.3.0):** TMDB/AniList mit deutschen und alternativen Titeln, Originaltiteln, Erscheinungsjahr, Poster, Anbieter-IDs, Textähnlichkeitsranking und bestätigter Zuordnung auch für bereits gespeicherte Titel.\n- **Bild-Upload und Analyse (v0.2.0):** Mehrere Screenshots/Poster gleichzeitig hochladen, lokale OCR mit Tesseract (Deutsch/Englisch), optional externe Vision-KI, Konfidenz, bearbeitbare Kandidaten und bewusste Übernahme in die persönliche Liste.\n- **Manuell suchen:** Filme und Serien über TMDB (eigener API-Schlüssel), Anime über AniList, plus direkte Titel-Erfassung ohne API.
- **Titel hinzufügen:** Sammlung mit Dublettenprüfung für Anbieter-IDs und manuell erfasste Namen.
- **Sehfortschritt:** Filme *gesehen/nicht gesehen*; Serien und Anime *nicht gesehen*, *komplett gesehen*, *bis Staffel/Folge* oder *Staffel gesehen*.
- **Getrennte Statuswerte:** Ein Titel kann bereits in der Mediathek liegen und dennoch ungesehen sein.
- **Sammlung und Wunschliste:** Einträge anzeigen, Status und Fortschritt ändern und Titel löschen.
- **Datenübernahme:** Bestehende v0.1.0-Datenbank um die neuen Spalten erweitern.

Die Staffel-/Folgenangabe speichert aktuell einen **einzelnen Fortschrittspunkt pro Titel**, keine vollständige Historie mehrerer abgehakter Staffeln. Die manuelle Erfassung und der Fortschritt benötigen weder Instagram noch KI.

## ✨ Weitere geplante Funktionen

- **Bilderkennung:** Poster, Screenshots, Collagen, Szenen und Texteinblendungen mit Vision-KI und OCR analysieren.
- **Instagram-Import:** Beitrags-Links analysieren, soweit erlaubte Schnittstellen oder zugängliche Medien dies ermöglichen; manueller Screenshot-/Bild-Upload als verlässlicher Fallback.
- **Medien-Abgleich:** Titel, Originaltitel und alternative Schreibweisen über **TMDB** (Filme/Serien) und **AniList** (Anime) zuordnen.
- **Persönliche Watchlist:** Kategorien, Filter, Suche und Status wie *Fehlt*, *Wunschliste*, *Geplant*, *In Bearbeitung*, *Vorhanden*, *Ignoriert*.
- **Jellyfin-Integration:** Vorhandene Medien automatisch zuordnen; bei Serien und Animes perspektivisch Staffel- und Episodenabdeckung anzeigen.
- **Dubletten vermeiden:** Externe IDs und Aliasnamen statt bloßem Textvergleich nutzen.
- **Quellennachweis:** Nachhalten, in welchen Beiträgen oder Uploads ein Titel gefunden wurde.
- **Statistiken:** Erfasste, vorhandene und fehlende Titel; besonders häufig genannte Empfehlungen.
- **ForgeCore-Anbindung:** Fehlende Titel später gezielt an ForgeCore übergeben, ohne ungeprüfte automatische Downloads.

## 🗺️ Roadmap

Alle Phasen sind **geplant**. Versionen bezeichnen Entwicklungsziele, keine bereits veröffentlichten Releases.

| Phase | Zielversion | Umfang | Abnahmekriterium |
| --- | --- | --- | --- |
| 1 – Fundament ✅ implementiert | **v0.1.0** | React/TypeScript-Frontend, FastAPI-Backend, PostgreSQL, Docker Compose, Basis-UI, Konfiguration | Anwendung startet lokal und unter ZimaOS, Healthcheck erfolgreich |
| 2 – Bildanalyse ✅ implementiert (Test ausstehend) | **v0.2.0** | Einzel-/Mehrfach-Upload, OCR, austauschbarer Vision-KI-Anbieter, Konfidenz und manuelle Bestätigung | Titelvorschläge werden aus Testbildern angezeigt und korrigierbar gespeichert |
| 3 – Metadaten ✅ implementiert (Test ausstehend) | **v0.3.0** | TMDB/AniList-Suche, Titel-Aliase, Poster, Jahreszahlen, ID-Mapping | Erkannte Titel können zuverlässig mit Datensätzen verknüpft werden |
| 4 – Mediensammlung ✅ implementiert (Test ausstehend) | **v0.4.0** | Watchlist, individuelle Status, Filter, Suche, Bearbeiten, Duplikatschutz | Wiederholte Erkennung erzeugt keine doppelten Titel |
| 5 – Jellyfin ✅ implementiert (ZimaOS-Test ausstehend) | **v0.5.0** | Sichere API-Anbindung, Bibliotheksabgleich, Titel- und Staffel-/Episodenstatus | Vorhandene und teilweise vorhandene Titel werden nachvollziehbar markiert |
| 6 – Instagram ✅ Screenshot-Workflow implementiert | **v0.6.0** | Link-Import unter Beachtung der Plattformbeschränkungen, unterstützte Mehrbildbeiträge, Upload-Fallback | Zugängliche Beiträge werden verarbeitet; nicht zugängliche sauber abgefangen |
| 7 – Insights ✅ implementiert (ZimaOS-Test ausstehend) | **v0.7.0** | Dashboard, Quellenhistorie, Fundhäufigkeit, Prüf- und Fehlerübersicht | Statistiken und Herkunft pro Titel sind nachvollziehbar |
| 8 – Integration & Release (RC implementiert) | **v1.0.0** | ForgeCore-Schnittstelle, PWA-Grundfunktionen, Tests, Backups, Sicherheit, Dokumentation | Stabiler, dokumentierter Docker-Release für den Heimserver |

### Spätere Ideen (nach v1.0.0)

- Reel-/Video-Frame-Analyse, soweit zugänglich
- Weitere Quellen wie TikTok, YouTube, Pinterest und Reddit
- Automatisierbare Import-Workflows nur mit berechtigtem Zugriff
- Optionaler lokaler Vision-KI-Anbieter für datenschutzfreundliche Verarbeitung

## 🧱 Geplante Architektur

| Bereich | Technologie |
| --- | --- |
| Frontend | React, TypeScript, Tailwind CSS |
| Backend / API | Python, FastAPI |
| Datenbank | PostgreSQL |
| Vision / Texterkennung | Austauschbarer Vision-KI-Anbieter und OCR |
| Metadaten | TMDB, AniList |
| Mediathek | Jellyfin API |
| Deployment | Docker Compose auf ZimaOS / Linux |

Die technischen Entscheidungen können sich mit der Entwicklung ändern.

## 📁 Zielstruktur

```text
Cinearis/
├── assets/
│   ├── .gitkeep
│   ├── Cinearis.png          # offizielles Projektlogo
│   └── favicon.ico           # Browser-Favicon
├── frontend/                 # React / TypeScript / nginx
├── backend/                  # FastAPI / SQLAlchemy
├── docs/
│   ├── SETUP.md              # Installation und Betrieb
│   └── RELEASE_CHECKLIST.md  # Abnahmetests
├── scripts/
│   ├── setup-auth.sh         # Passwortdatei anlegen
│   └── backup.sh             # Datenbank sichern
├── frontend/public/          # PWA-Manifest und Offline-Seite
├── .env.example
├── .gitignore
└── docker-compose.yml
```

Weitere generierte Favicons können im `assets/`-Ordner liegen.

Das offizielle Cinearis-Logo liegt bereits unter **`assets/Cinearis.png`** und wird oben in dieser README angezeigt. Aus diesem Motiv wurden Favicon-Varianten (16 × 16, 32 × 32, 48 × 48, .ico, Apple Touch und PWA) vorbereitet. Welche Varianten bereits im Repository liegen, ist im Ordner `assets/` ersichtlich.

Sobald `assets/favicon.ico` vorhanden ist, kann die Website z. B. so darauf verweisen:

```html
<link rel="icon" type="image/x-icon" href="/assets/favicon.ico" />
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png" />
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png" />
<link rel="manifest" href="/assets/site.webmanifest" />
```

Bei einem späteren Build werden die Dateien im statischen öffentlichen Verzeichnis bereitgestellt.

## 🚀 Installation / Update

```bash
git clone https://github.com/Homiiboy/Cinearis.git
cd Cinearis
cp .env.example .env
bash scripts/setup-auth.sh
# In .env ein starkes POSTGRES_PASSWORD setzen
docker compose up -d --build
```

Standardmäßig nur auf `127.0.0.1:8088` erreichbar. Für den Zugriff im **vertrauenswürdigen LAN** `CINEARIS_BIND_IP=0.0.0.0` in `.env` setzen und dann `http://<SERVER-IP>:8088` öffnen (mit Basic-Auth-Anmeldung). Für Fernzugriff HTTPS/VPN nutzen. Für den API-/Datenbankcheck nach Anmeldung `http://<SERVER-IP>:8088/api/health` aufrufen.

Zum Aktualisieren nach einem bestehenden Checkout: `git pull && docker compose up -d --build`. Für die TMDB-Suche `TMDB_API_KEY` und für eine zusätzliche Vision-KI optional `VISION_API_KEY` in `.env` ergänzen. **Ausführliche Anleitung:** [docs/SETUP.md](docs/SETUP.md). **Sicherheit:** v1.0.0 RC bietet verpflichtende Einzelbenutzer-HTTP-Basic-Auth, aber noch keine Mehrbenutzerverwaltung. Nicht ungeschützt ins Internet stellen; für Fernzugriff HTTPS/VPN voraussetzen.

## 🔐 Datenschutz & Sicherheit

- API-Keys, Jellyfin-Zugangsdaten und Passwörter gehören **niemals ins Git-Repository**; für lokale Konfiguration `.env` verwenden.
- Instagram-Inhalte nur über zulässige Zugangswege bzw. vom Nutzer bereitgestellte Dateien verarbeiten.
- Externe Bilder können an einen konfigurierten KI-Anbieter gesendet werden; dies muss transparent und abschaltbar sein.
- Medien-Treffer der KI sind Vorschläge, keine garantierten Identifizierungen; unsichere Treffer müssen überprüfbar sein.
- Jellyfin zunächst mit möglichst eingeschränkten Zugriffsrechten anbinden.

## 🧩 Novarion

- **Velaris / Jellyfin:** Mediatheksbestand prüfen
- **ForgeCore:** Medien-Wunschliste und spätere Übergabe
- **Cinearis:** Neue Titel entdecken, erkennen und organisieren

## 📌 Entwicklungsstand

- [x] Repository und Entwicklungs-Roadmap
- [x] Assets-Ordner und Projektlogo
- [x] Favicon.ico im Repository
- [x] v0.1.0 – Projektfundament implementiert (ZimaOS-Laufzeittest ausstehend)
- [x] v0.1.1 – Manuelle Mediensuche und grundlegender Sehfortschritt (Integrationstest auf ZimaOS ausstehend)
- [x] v0.2.0 – Bildanalyse implementiert (ZimaOS-Laufzeittest ausstehend)
- [x] v0.3.0 – Metadaten und manuelle Titelzuordnung implementiert (ZimaOS-Laufzeittest ausstehend)
- [x] v0.4.0 – Erweiterte Sammlung implementiert (ZimaOS-Test ausstehend)
- [x] v0.5.0 – Jellyfin-Abgleich implementiert (Live-Test ausstehend)
- [x] v0.6.0 – Instagram-Links, Screenshots und Quellenzuordnung (ZimaOS-Test ausstehend; automatischer Medienabruf nicht verfügbar)
- [x] v0.7.0 – Insights und Statistiken implementiert (ZimaOS-Test ausstehend)
- [x] v1.0.0 RC – Export/PWA/Zugangsschutz/Backup implementiert\n- [ ] v1.0.0 – Vollständiger Build, Integrationstests und ZimaOS-Abnahme

---

**Cinearis** · Teil des **Novarion-Ökosystems**


> **Abnahmehinweis:** Der GitHub-Code wurde aktualisiert, aber ein vollständiger Docker-Build, ein Test der Browser-Anmeldung und der realen Jellyfin-/ForgeCore-Integration auf ZimaOS stehen noch aus. Siehe [Release-Checkliste](docs/RELEASE_CHECKLIST.md).
