**Architektur der Anwendung**

1. Überblick

- Die Anwendung ist eine mehrschichtige Flask-Webanwendung mit klarer Trennung in
  Controller (Routes), Business-Logik (Services) und Datenzugriff (Repositories).
- Ziel: Produktstammdaten in MySQL verwalten (Single Source of Truth), semantische
  Suche über Qdrant ermöglichen und optional Neo4j für Graph‑Anreicherungen nutzen.

2. Schichten und Komponenten

- **Routes (Controller):** Blueprints (z. B. `products`, `search`, `index`, `pdf`, `rag`, `audit`, `dashboard`) nehmen HTTP-Requests entgegen,
  validieren/parsieren Parameter und rufen Services auf. Sie sind zuständig für Rendering/Antworten.

- **Services:** Implementieren Geschäftslogik (ETL/Index-Aufbau, Such-Orchestrierung, Produkt-Listing, Validierung).
  Services kombinieren und koordinieren mehrere Repositories und führen die eigentlichen Use Cases aus.

- **Repositories:** Kapseln den direkten Zugriff auf Persistenzschichten:
  - **MySQLRepository:** SQL-Queries, Transaktionen, Stored Procedures, Trigger/Audit.
  - **QdrantRepository:** Embedding-Upload, Vektor-Suche, Collection-Management.
  - **Neo4jRepository (optional):** Cypher-Abfragen und Graph-Upserts zur Anreicherung.

3. Datenbanken & Rollen

- **MySQL:** Autoritative Quelle für Stammdaten (Produkte, Marken, Kategorien, Tags).
  - Sorgt für ACID, Fremdschlüssel, CHECK-Constraints und Audit-Tables/Trigger.
  - Beinhaltet SQL-Skripte für Schema, Bulk-Import und Beispiel-Transaktionen (siehe `abgabe`).

- **Qdrant (Vector DB):** Hält Embeddings + Payloads für semantische Suche.
  - Wird per ETL aus MySQL befüllt (Textdokument pro Produkt → Embedding → Upload).
  - Nutzt HNSW-Index (ANN) für schnelle Relevanzsuche.

- **Neo4j (optional):** Modelliert Beziehungen als Graph zum Traversieren/Enrichen
  (z. B. verwandte Produkte, Markenbeziehungen). Füllt sich per Sync/ETL.

4. Typische Datenflüsse

- **Produkt erstellen/ändern (Schreibpfad):**
  Client → Route → Service → MySQL (Transaktion/Procedure) → COMMIT → (optional) ETL/Async → Qdrant/Neo4j Upsert

- **Suche (Lese-Pfad)**
  - SQL-Suche: Route → Service → MySQL (LIKE / FILTERS) → Ergebnisse.
  - Vektor-Suche: Route → Service → Embedding-Modell → Qdrant → Metadaten → Ergebnisse.
  - RAG: Vektor-Suche → (optional Neo4j-Anreicherung) → LLM → formulierte Antwort.

5. Konsistenz & Synchronisation

- Unidirektionaler Datenfluss: MySQL → ETL → Qdrant/Neo4j. MySQL bleibt Single Source of Truth.
- Risiko: Zeitliche Inkonsistenzen zwischen MySQL und Qdrant/Neo4j wenn ETL fehlschlägt oder verzögert.
- Empfehlung: idempotente Upserts, ETL-Run-Log, Monitoring, evtl. Near‑Realtime-Events (z. B. CDC) bei strengeren Konsistenzanforderungen.

6. Transaktionen & Integrität

- Schreiboperationen (CREATE/UPDATE/DELETE) sollten in MySQL in Transaktionen stattfinden;
  `abgabe/Teil_2/transaction.sql` demonstriert korrekte Patterns (LAST_INSERT_ID, kontrollierte ROLLBACK-Entscheidungen).
- Stored Procedures kapseln Validierung und Idempotenz (z. B. `import_product`).
- Trigger (Audit) protokollieren Änderungen für Nachvollziehbarkeit.

7. Suche: Strategie und Verantwortlichkeiten

- **SQL:** Gut für exakte Filtersuchen, ACID-sichere Abfragen, niedrige Latenz; limitiert bei Freitext.
- **Vektor:** Liefert semantische Treffer und Relevanzrankings; benötigt ETL und ist approximate (ANN).
- **RAG / Graph-RAG:** Kombiniert Retrieval + LLM (optional Neo4j) für natürliche Antworten und relationale Anreicherung;
  trade-offs: Latenz, Kosten (API) und Halluzinationsrisiken.

8. Betrieb & Deployment

- Containerisiert per `docker-compose.yml` + `Dockerfile` (MySQL, Qdrant, Neo4j, App). Lokales Testing via Compose empfohlen.
- Produktionsreife: Ausrollen in orchestrierter Umgebung (K8s), persistent storage, Backups für MySQL/Neo4j, Scaling für Qdrant und Modell‑Serving.

9. Überwachung & Observability

- Logging: per App-Handler in `app.py`, tägliche Logfiles. ETL-Run-Log und Audit-Tabellen liefern ergänzende Telemetrie.
- Health-Checks: DB-Connectivity, Qdrant-API, Neo4j-Bolt; Alerts bei fehlgeschlagenen ETL-Läufen.

10. Sicherheits- & Qualitätsaspekte

- Roh-SQL-Ausführung nur als SELECT mit Whitelist/Regex-Checks.
- Validierung serverseitig (Procedures + CHECKs) reduziert fehlerhafte Daten.
- Rollen/Authentifizierung sind nicht Teil des Skeletons — für Produktion ergänzen.

11. App-Dokumentation

### Zweck der Anwendung

- Die App stellt einen Produktkatalog mit relationalen Daten, semantischer Suche und optionaler KI-gestützter Antwortgenerierung bereit.
- MySQL liefert die fachlich gültigen Daten, Qdrant unterstützt die Vektorsuche und Neo4j kann Beziehungen im Graphen ergänzen.

### Wichtige Seiten und Routen

- **Dashboard** (`/`): Überblick über Produkt-, Marken-, Kategorie- und Index-Status.
- **Produkte** (`/products`): Produktliste mit Paginierung und verknüpften Stammdaten.
- **Index** (`/index`): Verwaltung des Vektorindex, etwa Neuaufbau oder Truncate.
- **Suche** (`/search`): Einheitliche Suchoberfläche für SQL-, Vektor- und RAG-Szenarien.
- **RAG** (`/rag`): Natürlichsprachliche Antwort auf Basis der Vektorsuche.
- **Graph-RAG** (`/graph-rag`): RAG mit zusätzlicher Graph-Anreicherung über Neo4j.
- **Audit** (`/audit`): Anzeige der ETL- und Änderungsprotokolle.
- **Validierung** (`/validate`): Prüfung von Schema und Datenintegrität.
- **PDF-Upload** (`/pdf-upload`): Verwaltung von Lehr- und Produkt-PDFs.
- **PDF-API** (`/api/pdf-stats`): Liefert Statistikdaten für die PDF-Verwaltung.

### Typischer Nutzerfluss

- Ein Nutzer öffnet zuerst das Dashboard und erhält Kennzahlen zum Datenbestand.
- Über die Produktseite kann er vorhandene Datensätze durchsuchen und kontrollieren.
- Über die Suchseite kann er zwischen SQL-Suche, semantischer Vektorsuche und RAG wechseln.
- Bei Bedarf werden PDFs hochgeladen, indexiert und anschließend ebenfalls durchsucht.

### Start und Betrieb

- Die Anwendung läuft standardmäßig im Flask-Container auf Port 5000 und wird per Docker Compose nach außen auf Port 8081 freigegeben.
- Im lokalen Entwicklungsmodus wird die App direkt über `python app.py` gestartet.
- Damit die Kernfunktionen arbeiten, müssen MySQL und Qdrant erreichbar sein; Neo4j ist optional.

### Bedienlogik der Hauptfunktionen

- **Produktanzeige:** Die Route liest paginierte Produktdaten aus MySQL und rendert sie im Template.
- **Index-Aufbau:** Produkte werden aus MySQL extrahiert, als Text aufbereitet, eingebettet und in Qdrant gespeichert.
- **Suche:**
  - SQL-Suche nutzt direkte Datenbankabfragen für exakte oder filternde Treffer.
  - Vektorsuche nutzt Embeddings und Relevanzscores aus Qdrant.
  - RAG kombiniert Suchergebnisse mit einem LLM für eine formulierte Antwort.
- **Validierung:** Die App prüft, ob Schema, Tabellen und Datenregeln zu den erwarteten Strukturen passen.
- **Audit:** Historische Läufe und Änderungen werden angezeigt, um Datenimporte und Anpassungen nachvollziehbar zu machen.

### Grenzen der App im aktuellen Stand

- Nicht jede Route ist bereits vollständig implementiert; einige Bereiche sind als Platzhalter oder TODO angelegt.
- Die App ist primär als Projekt- und Lehranwendung ausgelegt, nicht als produktives System mit Login, Rollenmodell und vollständigem Rechtekonzept.
- Die semantischen Funktionen hängen von der Verfügbarkeit der externen Dienste und des Embedding-Modells ab.