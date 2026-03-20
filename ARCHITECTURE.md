# Architekturüberblick

## 1. Das Szenario

Sie arbeiten mit einer **Produktdatenbank** (Werkzeuge, Maschinen, Industriebedarf), die mehrere Datenbanktechnologien kombiniert:

| Technologie | Typ | Warum? |
|---|---|---|
| **MySQL** | Relational | Strukturierte Stammdaten – Produkte, Marken, Kategorien, Tags |
| **Qdrant** | Vektordatenbank | Semantische Ähnlichkeitssuche über Embeddings |
| **Neo4j** | Graphdatenbank | Beziehungen zwischen Entitäten (z. B. „welche Produkte gehören zu einer Marke?") |

Die Webanwendung (Flask) verbindet diese Systeme und bietet u. a. eine Produktübersicht, verschiedene Sucharten und ein Dashboard.

> **Wichtig:** Der Schwerpunkt liegt auf **MySQL**, **Qdrant**, **SQL-Skripten** und dem Ergänzen vorbereiteter Platzhalter. Python darf und soll an mehreren Stellen ergänzt werden. **Neo4j** sowie **RAG/LLM-Suche** sind optionale Erweiterungen.

---

## 2. The Great Picture

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser (Frontend)                     │
│          HTML-Seiten: Dashboard, Produkte, Suche, …          │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼─────────────────────────────────┐
│                     Flask Web-App (Python)                     │
│                                                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐    │
│  │   Routes     │──▶│  Services   │──▶│  Repositories   │    │
│  │ (Controller) │   │ (Logik)     │   │ (Datenzugriff)  │    │
│  └─────────────┘   └─────────────┘   └───────┬─────────┘    │
└───────────────────────────────────────────────┼──────────────┘
                                                │
                    ┌───────────────────────────┼───────────┐
                    │                           │           │
              ┌─────▼─────┐             ┌───────▼───┐  ┌───▼───┐
              │   MySQL    │             │  Qdrant   │  │ Neo4j │
              │ (Tabellen) │             │ (Vektoren)│  │(Graph)│
              └────────────┘             └───────────┘  └───────┘
```

Die App ist in **drei Schichten** aufgebaut (von oben nach unten):

1. **Routes** – Nehmen HTTP-Anfragen entgegen, rufen Services auf, rendern HTML
2. **Services** – Enthalten die Geschäftslogik, kombinieren ggf. mehrere Repositories
3. **Repositories** – Sprechen direkt mit den Datenbanken (SQL, Vektor-API, Cypher)

Diese Trennung sorgt dafür, dass z. B. ein SQL-Query nur an **einer** Stelle steht (im Repository) und nicht im gesamten Code verstreut ist.

---

## 3. Datenbank-Schema (MySQL)

Das relationale Schema entwerfen und erstellen **Sie selbst** als Teil der Aufgabe.

**Hinweise zur Orientierung:**
- Es gibt Stammdaten-Tabellen für **Produkte**, **Marken**, **Kategorien** und **Tags**
- Zwischen Produkten und Tags besteht eine **N:M-Beziehung** (ein Produkt kann mehrere Tags haben, ein Tag kann mehreren Produkten zugeordnet sein)
- Jedes Produkt gehört zu genau einer Marke und genau einer Kategorie (**1:N**)
- Eine Log-Tabelle protokolliert ETL-Durchläufe (wann wurden Daten nach Qdrant übertragen?)

> 💡 **Ihre Aufgabe:** Entwerfen Sie ein ER-Diagramm, erstellen Sie die Tabellen mit geeigneten Datentypen, Primär- und Fremdschlüsseln und füllen Sie sie mit den bereitgestellten CSV-Daten.

---

## 4. Wie hängen die drei Datenbanken zusammen?

```
                    ┌───────────┐
                    │   MySQL   │  "Single Source of Truth"
                    │ (Stamm-   │  Alle Produkte, Marken,
                    │  daten)   │  Kategorien, Tags
                    └─────┬─────┘
                          │
              ┌───────────┼───────────┐
              │ ETL/Index │           │ Sync-Skript
              ▼           │           ▼
        ┌───────────┐     │     ┌───────────┐
        │  Qdrant   │     │     │   Neo4j   │
        │ (Vektor-  │     │     │ (Graph-   │
        │  suche)   │     │     │  daten)   │
        └───────────┘     │     └───────────┘
                          │
                    ┌─────▼─────┐
                    │  Suche /  │  Zur Query-Zeit werden
                    │  RAG      │  Ergebnisse aus Qdrant
                    └───────────┘  mit Neo4j angereichert
```

- **MySQL** ist die zentrale Datenquelle
- **Qdrant** erhält Produkt-Daten als Vektoren (über einen ETL-Prozess)
- **Neo4j** kann optional die gleichen Daten als Graph erhalten (über ein Sync-Skript)
- Im Pflichtteil werden vor allem **MySQL** und **Qdrant** genutzt; **Neo4j** und **RAG** sind Erweiterungen

---

## 5. Vorgesehene Seiten der Web-App

| Seite | URL | Zielverhalten |
|---|---|---|
| **Dashboard** | `/` | Zeigt Statistiken – wie viele Produkte, Marken, Tags gibt es? |
| **Produkte** | `/products` | Paginierte Liste aller Produkte mit Marke, Kategorie und Tags |
| **Index** | `/index` | Startet den ETL-Prozess (MySQL → Qdrant) |
| **Suche** | `/search` | Verschiedene Sucharten: Vektor und SQL, optional auch RAG |
| **RAG** | `/rag` | Optionale KI-gestützte Suche mit natürlichsprachlicher Antwort |
| **Audit** | `/audit` | Protokoll der Index-Durchläufe |
| **Validierung** | `/validate` | Prüft, ob das MySQL-Schema korrekt ist |
| **PDF-Upload** | `/pdf-upload` | PDFs hochladen und durchsuchbar machen |

---

## 6. Was passiert bei einer Produktsuche? (vereinfacht)

### Klassische SQL-Suche
```
Nutzer gibt Suchbegriff ein
  → SQL-Query mit LIKE/MATCH auf MySQL
  → Ergebnisliste zurück
```

### Vektor-Suche (semantisch)
```
Nutzer gibt Suchbegriff ein
  → Text wird in einen Zahlenvektor umgewandelt (Embedding)
  → Qdrant findet die ähnlichsten Produkt-Vektoren
  → Ergebnisliste mit Ähnlichkeits-Score zurück
```

### RAG-Suche (Retrieval-Augmented Generation, optional)
```
Nutzer gibt Frage ein
  → Vektor-Suche liefert relevante Produkte
  → (Optional) Neo4j reichert Ergebnisse an (Marke, Kategorie, Tags)
  → Produkt-Infos + Frage gehen an ein Sprachmodell (LLM)
  → LLM formuliert eine natürlichsprachliche Antwort
```

> 🤔 **Zum Nachdenken:** Welche Vor-/Nachteile hat jede Suchart? Welche Teile gehören zum Pflichtumfang, welche sind Erweiterungen?

---

## 7. Der ETL-Prozess (Extract, Transform, Load: MySQL → Qdrant)

Damit die Vektor-Suche funktioniert, müssen Produkte aus MySQL in Qdrant übertragen werden:

```
  EXTRACT          TRANSFORM              LOAD
┌─────────┐    ┌──────────────┐    ┌─────────────────┐
│  MySQL   │───▶│ Text-Dokument│───▶│ Qdrant-Vektoren │
│ Produkte │    │ + Embedding  │    │ (Collection)    │
└─────────┘    └──────────────┘    └─────────────────┘
```

1. **Extract:** Produkte mit Marke, Kategorie und Tags aus MySQL laden
2. **Transform:** Aus den Produktdaten ein Textdokument erstellen und daraus einen Vektor berechnen
3. **Load:** Vektoren + Metadaten in Qdrant hochladen

> 💡 Dieser Prozess wird auf der `/index`-Seite ausgelöst.

---

## 8. Wo arbeiten Sie?

### Ihre Dateien

```
sql/
├── aufgabe1_transaktion_erfolg_template.sql   ← Transaktionen
├── aufgabe2_trigger_price_history_template.sql ← Trigger
├── aufgabe3_procedure_mass_tag_template.sql    ← Stored Procedures
└── aufgabe4_indizes_template.sql              ← Indizes & Performance

repositories/
├── mysql_repository.py      ← SQL-Queries in Python-Platzhalter einfügen
├── neo4j_repository.py      ← Optional: Neo4j-/Cypher-Zugriffe ergänzen
└── qdrant_repository.py     ← Vektor-Operationen ergänzen

services/
├── search_service.py        ← Suche orchestrieren (Vektor, RAG, SQL)
└── index_service.py         ← ETL-Pipeline zusammenbauen
```

> Hinweis: Dieses Dokument beschreibt teilweise die **Zielarchitektur**. Mehrere Dateien im Template enthalten aktuell noch `TODO`-Platzhalter und sind noch nicht vollständig implementiert.

### Was ist fertig, was müssen Sie ergänzen?

| Komponente | Was macht sie? | Müssen Sie ändern? |
|---|---|---|
| Flask-Routes | Nimmt HTTP-Requests entgegen, ruft Services auf | ❌ Nein |
| Neo4j-Repository | Graph-Abfragen und Graph-Enrichment | ⭐ Optional – nur für die Neo4j-Erweiterung |
| Templates (HTML) | Frontend-Darstellung | ❌ Nein |
| Docker-Setup | Startet MySQL, Qdrant, Neo4j | ❌ Nein |
| **MySQL-Repository** | **SQL-Queries für Datenzugriff** | **✅ JA – hier kommen Ihre Queries rein** |
| **SQL-Aufgaben** | **Transaktionen, Trigger, Prozeduren, Indizes** | **✅ JA – reine SQL-Arbeit** |
| **Search-Service** | **Vektor-Suche, RAG-Suche und SQL-Suche orchestrieren** | **✅ JA – Pflichtteil: SQL- und Vektor-Suche; RAG optional** |
| **Index-Service** | **ETL-Pipeline: MySQL → Embedding → Qdrant** | **✅ JA – Schritte zusammensetzen** |
| **Qdrant-Repository** | **Vektor-Operationen (Suche, Upload)** | **✅ JA – Teil des Pflichtumfangs** |

---

## 9. Docker-Umgebung

Alles läuft in Containern – Sie müssen nichts lokal installieren außer Docker:

```
docker-compose up -d
```

| Container | Port | Zugriff |
|---|---|---|
| MySQL | `3396` | `mysql -h localhost -P 3396 -u app -p` |
| Adminer (DB-UI) | `8980` | http://localhost:8980 |
| Qdrant | `6333` | http://localhost:6333/dashboard |
| Neo4j Browser | `7474` | http://localhost:7474 |
| **Web-App** | **`8080`** | **http://localhost:8080** |

---

## 10. Glossar

| Begriff | Erklärung |
|---|---|
| **Blueprint** | Flask-Mechanismus, um Routen in eigene Module aufzuteilen |
| **Route** | Flask-Endpunkt, der eine URL auf eine Python-Funktion abbildet |
| **Controller** | Schicht, die Requests entgegennimmt und an Services weiterleitet; in Flask meist die Route-Funktion |
| **Repository** | Klasse, die den Datenbankzugriff kapselt (eine Klasse pro Datenbank-Typ) |
| **Service** | Klasse mit Geschäftslogik, die ein oder mehrere Repositories nutzt |
| **Factory** | Zentrale Klasse zum Erzeugen und Wiederverwenden von Repositories oder Services |
| **ETL** | Extract – Transform – Load: Daten aus einer Quelle laden, umwandeln, in ein Ziel schreiben |
| **Embedding** | Numerische Vektor-Darstellung eines Textes (hier: 384 Zahlen pro Produkt) |
| **Vektor-Suche** | Suche über mathematische Ähnlichkeit von Vektoren statt exakter Textübereinstimmung |
| **RAG** | Retrieval-Augmented Generation: Relevante Daten finden + Sprachmodell-Antwort generieren |
| **Graph-Enrichment** | Anreicherung von Suchergebnissen mit zusätzlichen Beziehungsdaten aus Neo4j |
| **Collection** | Qdrant-Äquivalent zu einer MySQL-Tabelle (enthält Vektoren + Metadaten) |
| **Cypher** | Abfragesprache für Neo4j (wie SQL für Graphen) |
| **N:M-Beziehung** | Viele-zu-Viele-Beziehung, aufgelöst über eine Zwischentabelle (`product_tags`) |
| **ACID** | Atomicity, Consistency, Isolation, Durability – Garantien einer Transaktion |
| **HNSW** | Approximativer Algorithmus für schnelle Vektorsuche in Qdrant |

