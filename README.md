# DB → VectorDB Manager

Flask-Anwendung für eine Datenbank-Projektarbeit mit MySQL als Source of Truth, Qdrant für semantische Suche, optionalem Neo4j-Enrichment und RAG-Funktionen über ein LLM.

## Überblick

Das Projekt kombiniert mehrere Ebenen:

- MySQL speichert die Produktdaten und ist die fachliche Hauptquelle.
- Qdrant speichert Embeddings und ermöglicht Vektorsuche.
- Neo4j kann Produktbeziehungen für Graph-RAG anreichern.
- Die Flask-App bietet UI, Suche, PDF-Upload, Validierung und Dashboard.

## Schnellstart mit Docker

1. Stelle sicher, dass Docker und Docker Compose installiert sind.
2. Lege die Konfiguration an:

```bash
cp .env.example .env
```

3. Starte alle Dienste:

```bash
docker compose up -d --build
```

4. Öffne die App im Browser:

```text
http://localhost:8081
```

Beim ersten Start werden die MySQL-Initialdaten aus `mysql-init/` geladen und die Container für MySQL, Qdrant, Neo4j und die Flask-App gestartet.

## Wichtige URLs

- App: http://localhost:8081
- Adminer: http://localhost:8990
- Neo4j Browser: http://localhost:7484
- Qdrant API: http://localhost:6343

## Neo4j-Synchronisation

Zum Synchronisieren der relationalen Produktdaten aus MySQL mit Neo4j kann das mitgelieferte Sync-Skript im `app`-Container ausgeführt werden. Beispiel (aus dem Projektverzeichnis):

```bash
docker compose exec app python /app/scripts/sync_mysql_to_neo4j.py
```

Vor Ausführung ist sicherzustellen, dass die MySQL- und Neo4j-Container laufen und die relevanten Umgebungsvariablen in `.env` gesetzt sind.

## Standard-Konfiguration

Die Datei [.env.example](.env.example) enthält die üblichen Standardwerte. Für den lokalen Start reichen meistens diese Werte:

- `FLASK_SECRET_KEY=dev-secret`
- `MYSQL_DATABASE=productdb`
- `MYSQL_USER=app`
- `MYSQL_ROOT_PASSWORD=admin123`
- `MYSQL_PASSWORD=app`
- `MYSQL_URL=mysql+pymysql://app:app@mysql:3306/productdb`
- `QDRANT_URL=http://qdrant:6333`
- `NEO4J_URI=bolt://neo4j:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=admin123`
- `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
- `EMBEDDING_DIM=384`

Optional für RAG/LLM:

- `OPENAI_API_KEY`
- `LLM_MODEL`

## Login und Zugriff

Die Anwendung besitzt kein separates Login-System. Der Zugriff erfolgt direkt über die Weboberfläche auf Port 8081. Für Datenbankzugriffe können Adminer oder die jeweiligen Container-Ports aus der Compose-Datei verwendet werden.

Typische Bereiche in der App:

- Dashboard
- Produktliste
- Index-/Embedding-Verwaltung
- Vektor-, SQL-, RAG- und Graph-RAG-Suche
- PDF-Upload und PDF-RAG
- Validierung und Audit

## Entwicklung lokal

Für einen direkten Start außerhalb von Docker werden zunächst die Abhängigkeiten installiert:

```bash
pip install -r requirements.txt
```

Anschließend kann die Flask-Anwendung mit folgendem Befehl gestartet werden:

```bash
python3 app.py
```

Hinweis: Für einen sinnvollen Lauf müssen MySQL, Qdrant und optional Neo4j erreichbar sein und die passenden Umgebungsvariablen gesetzt sein.

## Tests

Für die SQL-Übungen und Beispieltests gibt es ein eigenes Skript:

```bash
bash tests/run_tests.sh
```

Das Skript erwartet eine erreichbare MySQL-Instanz und verwendet die SQL-Dateien aus `src/sql/` zusammen mit dem Seed aus `tests/fixtures/seed.sql`.

## Projektstruktur

- `app.py` - Flask Application Factory
- `config.py` - Konfiguration über Umgebungsvariablen
- `routes/` - Blueprints für UI und API-Endpunkte
- `services/` - Business-Logik
- `repositories/` - Datenzugriff auf MySQL, Qdrant und Neo4j
- `templates/` - HTML-Templates
- `static/` - CSS und Bilder
- `mysql-init/` - Initialisierung von Schema und Import
- `abgabe/` - Abgabeunterlagen und SQL-Teile
- `tests/` - Testskripte und Fixtures

## Wichtige Hinweise

- Wenn Vektorsuche oder RAG nur Platzhalter liefern, prüfe zuerst, ob der Index in Qdrant neu aufgebaut wurde.
- Wenn Neo4j nicht verfügbar ist, bleibt die App trotzdem lauffähig; Graph-RAG ist dann nur eingeschränkt.
- Wenn `OPENAI_API_KEY` fehlt, nutzt die App einen Fallback für RAG-Antworten.

## Referenz

Weitere fachliche Hintergründe stehen in der Abgabe und in der Vergleichsanalyse unter `abgabe/Teil_2/`.