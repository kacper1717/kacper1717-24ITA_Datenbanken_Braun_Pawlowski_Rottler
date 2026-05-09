# Vergleichsanalyse der Suchmethoden

Im Folgendem werden die vier im Projekt implementierten Suchmethoden verglichen. Dabei werden folgende Suchmethoden betrachtet:

1. SQL-Suche
2. Vektorsuche
3. RAG-LLM (Vektorsuche + KI-generierte Antwort)
4. Graph-RAG (Neo4j + Vektorsuche + LLM)

---

## 1. Klassische SQL-Suche

### Implementierung

Die Methode `search_products_by_keyword` in `repositories/mysql_repository.py` führt
eine LIKE-basierte Schlüsselwortsuche auf den Feldern `name` und `description` der
MySQL-Tabelle `products` aus:

```sql
SELECT p.id, p.name, p.price, b.name AS brand, c.name AS category, p.description
FROM products p
LEFT JOIN brands b ON p.brand_id = b.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.name LIKE :kw OR p.description LIKE :kw
LIMIT :limit
```

Das Suchmuster wird als `%keyword%` übergeben (beiderseitiger Wildcard). Zusätzlich
erlaubt `execute_raw_query` das direkte Ausführen beliebiger SELECT-Abfragen, wobei
DML-Schlüsselwörter (INSERT, UPDATE, DELETE, DROP usw.) per Regex-Prüfung blockiert
werden.

Das relationale Schema (`mysql-init/01_schema.sql`) definiert die Tabellen `products`,
`brands`, `categories`, `tags` und die Verbindungstabelle `product_tags`. Für Preis
und Fremdschlüssel existieren CHECK- und FOREIGN-KEY-Constraints.

### Indizes

In `abgabe/Teil_2/index.sql` werden B+-Tree-Indizes angelegt:

| Index                    | Spalte         | Zweck                                  |
|--------------------------|----------------|----------------------------------------|
| `idx_products_name`      | `name`         | Gleichheits- und Präfixsuche           |
| `idx_products_brand_id`  | `brand_id`     | JOIN auf `brands`                      |
| `idx_products_category_id` | `category_id` | JOIN auf `categories`                 |
| `idx_products_price`     | `price`        | Bereichsabfragen / ORDER BY            |

InnoDB verwendet B+-Tree-Indizes, die Gleichheitssuchen in O(log n) ermöglichen und
Bereichsabfragen (BETWEEN, >, <) sowie ORDER BY effizient unterstützen. Ein
führendes Wildcard (`LIKE '%abc%'`) kann den Index **nicht** nutzen und erzwingt einen
Full Table Scan – das ist das zentrale Performance-Problem der LIKE-Suche.

### Vorteile

- Kein externer Dienst erforderlich: MySQL ist die einzige Datenbankabhängigkeit.
- Vollständig deterministisch und reproduzierbar – gleicher Input liefert immer
  gleichen Output.
- Ergebnisse sind transaktionssicher und schemavalidiert (Constraints, FK).
- Direkte Integration mit dem Audit-Log (`etl_run_log`-Tabelle).
- Parametrisierte Abfragen verhindern SQL-Injection.
- Einfache Erweiterung durch SQL-Ausdrücke (Filterung nach Preis, Marke, Kategorie).

### Nachteile

- Keine semantische Ähnlichkeit: Die Suche nach „Fahrradpedal" findet nicht
  „Pedale" oder „Tretlager", solange das Wort nicht wörtlich im Textfeld steht.
- Führendes Wildcard (`LIKE '%abc%`) verhindert Indexnutzung → O(n)-Full-Table-Scan.
- Keine Relevanzsortierung: Alle Treffer sind gleichwertig, es gibt keinen Score.
- Abhängig von der Qualität der Textfelder `name` und `description` – fehlende oder
  kurze Beschreibungen verschlechtern die Trefferquote direkt.
- Keine mehrsprachige oder tippfehlertolerante Suche.

### Einsatz im Projekt

Die SQL-Suche ist unter `/search?type=sql` erreichbar und dient als Basisvergleich.
Sie ist die einzige Methode, die ohne Vorindizierung (ETL-Lauf) sofort funktioniert.

---

## 2. Vektorsuche

### Implementierung

Die Methode `vector_search` in `services/search_service.py` folgt drei Schritten:

1. **Embedding**: Der Suchbegriff wird mit dem Modell
   `sentence-transformers/all-MiniLM-L6-v2` in einen 384-dimensionalen Vektor
   umgewandelt (`SentenceTransformer.encode`).
2. **ANN-Suche**: Der Abfragevektor wird gegen die Qdrant-Collection `products`
   gesucht, die alle Produkte als vorberechnete Vektoren enthält.
3. **Formatierung**: Ergebnisse werden mit Score, Name, Marke, Kategorie, Preis
   und dem ursprünglichen Dokument zurückgegeben.

Die Produkt-Dokumente werden beim ETL-Lauf (`services/index_service.py`) aus
mehreren Feldern zusammengesetzt:

```
Produkt: {name} | Marke: {brand} | Kategorie: {category} | Beschreibung: {desc} | Tags: {tags}
```

Dieser angereicherte Text wird eingebettet und als Payload zusammen mit dem Vektor
in Qdrant gespeichert.

### HNSW-Index in Qdrant

Qdrant verwendet Hierarchical Navigable Small Worlds (HNSW) als Approximate Nearest
Neighbour (ANN)-Index. Die konfigurierten Parameter (`repositories/qdrant_repository.py`):

| Parameter        | Wert | Bedeutung                                      |
|------------------|------|------------------------------------------------|
| `m`              | 16   | Verbindungen pro Knoten im Graph               |
| `ef_construct`   | 128  | Suchtiefe beim Indexaufbau (Qualität)          |
| `hnsw_ef`        | 64   | Suchtiefe zur Laufzeit (Speed vs. Recall)      |
| Distanzmetrik    | COSINE | Kosinus-Ähnlichkeit der normalisierten Vektoren |

Collections: `products` (Produktdaten), `pdf_skripte` (Lehrskripte), `pdf_produkte`
(Produktkataloge). PDF-Texte werden seitenweise in Chunks von max. 300 Zeichen
aufgeteilt und separat eingebettet.

### Vorteile

- Semantisch: Synonyme, verwandte Konzepte und inhaltliche Ähnlichkeit werden
  erkannt, auch ohne exakte Wortübereinstimmung.
- Rangliste mit Score (Kosinus-Ähnlichkeit 0–1): Ergebnisse sind nach Relevanz
  sortiert.
- Skaliert mit HNSW sublinear: Suche bleibt schnell auch bei wachsender
  Datenmenge (annäherndes O(log n)).
- Unterstützt mehrere Collections: Produktdaten und PDF-Dokumente getrennt
  durchsuchbar.
- Reiches Dokument als Embedding-Basis: Tags, Kategorie und Marke fließen in
  die Einbettung ein, nicht nur der Produktname.

### Nachteile

- Erfordert einen vorgelagerten ETL-Indexierungslauf (Qdrant muss befüllt sein).
- Erstmaliges Laden des Embedding-Modells (`all-MiniLM-L6-v2`) erhöht die Latenz
  der ersten Anfrage deutlich (Modell wird lazy geladen).
- Approximate Nearest Neighbour: Es ist möglich, dass ein exakt passender Treffer
  zugunsten eines ähnlicheren Vektors übergangen wird (Recall < 100 %).
- Keine Transaktionssicherheit: Der Qdrant-Index und MySQL können inkonsistent
  werden, wenn ein ETL-Lauf unterbrochen wird.
- Keine exakte Filterung nach Preis, Marke o. ä. ohne zusätzliche Payload-Filter.

### Einsatz im Projekt

Die Vektorsuche ist unter `/search?type=vector` erreichbar. Sie ist auch die
Grundlage für alle RAG-Varianten.

---

## 3. Semantische Suche / RAG

### Implementierung

`rag_search` in `services/search_service.py` erweitert die Vektorsuche um einen
LLM-Schritt:

1. **Retrieval**: `vector_search` liefert die Top-k ähnlichsten Produkte aus Qdrant.
2. **Kontextformatierung**: Die Treffer werden in einen strukturierten Prompt
   eingebettet (Name, Marke, Kategorie, Tags, Score).
3. **LLM-Generierung**: OpenAI (`gpt-4.1-mini`, Temperatur 0,2) generiert eine
   deutsche Antwort, die ausschließlich auf dem übergebenen Kontext basiert.

Systemprompt:

```
Du antwortest präzise und sachlich auf Deutsch.
Du beantwortest kurze Produktanfragen auf Deutsch.
Nutze nur den gegebenen Kontext und nenne Unsicherheiten offen.
```

Die PDF-RAG-Variante (`pdf_rag_search`) durchsucht stattdessen die Collections
`pdf_skripte` oder `pdf_produkte` und füttert LLM-Chunks mit Seitenangaben.
Falls kein `OPENAI_API_KEY` konfiguriert ist, gibt das System die formatierten
Treffer als Plaintext zurück (Fallback).

### Vorteile

- Antwortqualität: Statt einer Trefferliste erhält der Nutzer eine formulierte
  deutsche Antwort, die die relevantesten Fakten zusammenfasst.
- Kontextuell: Das LLM kann mehrere Treffer in Beziehung setzen und eine
  zusammenhängende Empfehlung formulieren.
- Unsicherheit wird explizit kommuniziert: Der Systemprompt fordert das LLM auf,
  Lücken im Kontext offen zu benennen.
- Erweiterbar auf PDF-Dokumente: Lehrskripte und Produktkataloge sind über
  dieselbe Pipeline durchsuchbar.

### Nachteile

- Abhängigkeit von `OPENAI_API_KEY`: Ohne gültigen Schlüssel ist nur der Fallback
  verfügbar.
- Latenz: Zu Vektorsuche-Latenz addiert sich ein API-Roundtrip zu OpenAI.
- Kosten: Jede LLM-Anfrage erzeugt Token-Kosten (Modell `gpt-4.1-mini`).
- Halluzinationsrisiko: Das LLM kann trotz Systemprompt und Temperatur 0,2
  Details erfinden, die nicht im Kontext stehen.
- Nicht deterministisch: Gleicher Input kann leicht variierende Antworten
  erzeugen.
- Kontext begrenzt auf Top-5-Treffer: Informationen aus weiteren Treffern fließen
  nicht in die Antwort ein.

### Einsatz im Projekt

RAG ohne Graph-Anreicherung ist unter `/rag` und `/search?type=rag` erreichbar.
Die PDF-Variante ist über `/search?type=pdf` zugänglich.

---

## 4. Graph-DB-Anreicherung + LLM (Graph-RAG)

### Implementierung

`rag_search(..., use_graph_enrichment=True)` erweitert den RAG-Ablauf um einen
Neo4j-Schritt zwischen Retrieval und LLM-Generierung:

1. **Retrieval**: Vektorsuche in Qdrant liefert Top-k Produkte mit MySQL-IDs.
2. **Graph-Anreicherung**: `neo4j_repository.get_product_relationships(ids)` ruft
   für alle Treffer-IDs Beziehungsdaten aus Neo4j ab:

```cypher
MATCH (p:Product)
WHERE coalesce(p.mysql_id, p.id) IN $mysql_ids
OPTIONAL MATCH (p)-[:HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND]->(brand)
OPTIONAL MATCH (p)-[:HAS_CATEGORY|IN_CATEGORY|BELONGS_TO_CATEGORY|CATEGORY]->(category)
OPTIONAL MATCH (p)-[:HAS_TAG|TAGGED_WITH|IN_TAG|TAG]->(tag)
WITH p, brand, category, collect(DISTINCT tag.name) AS tag_names
RETURN ...
```

3. **Merge**: Die zurückgegebenen Graph-Attribute (Titel, Marke, Kategorie, Tags)
   überschreiben die entsprechenden Payload-Felder aus Qdrant. Jedes angereicherte
   Ergebnis erhält `"graph_source": "Neo4j"` als Markierung.
4. **LLM-Generierung**: Wie bei RAG, aber mit dem angereicherten Kontext.

Der Neo4j-Graph wird beim ETL-Lauf über `neo4j_repository.upsert_products` befüllt:
Es werden Knoten für `Product`, `Brand` und `Category` angelegt und durch
`HAS_BRAND`- bzw. `HAS_CATEGORY`-Kanten verbunden. Zusätzlich gibt es Abfragen für
verwandte Produkte (`get_related_products`) über gemeinsame Marken oder Kategorien.

Ist Neo4j nicht erreichbar, greift automatisch `NoOpNeo4jRepository` als Fallback,
das leere Ergebnisse zurückliefert, ohne die restliche Pipeline zu unterbrechen.

### Vorteile

- Strukturelle Beziehungen: Der Graph modelliert Produkt→Marke, Produkt→Kategorie
  und Produkt→Tag als First-Class-Relationen und kann verwandte Produkte traversieren.
- Anreicherung im Kontext: LLM erhält nicht nur die Vektorähnlichkeit, sondern auch
  graphbasierte Metadaten, was die Antwortqualität bei verwandten Produkten verbessert.
- Flexibles Schema: Cypher-Abfragen unterstützen mehrere Beziehungstypen
  (z. B. `HAS_BRAND|IN_BRAND|BELONGS_TO_BRAND|BRAND`) und tolerieren verschiedene
  Schemaversionen durch `OPTIONAL MATCH`.
- Erweiterbar: Weitere Beziehungen (z. B. kompatible Produkte, Ersatzteile) lassen
  sich im Graph ergänzen, ohne die MySQL-Struktur anzupassen.

### Nachteile

- Höchste Systemkomplexität: Drei Datenbanken (MySQL, Qdrant, Neo4j) + LLM-API
  müssen gleichzeitig verfügbar sein.
- Latenz addiert sich: Vektorsuche + Cypher-Abfrage + LLM-Roundtrip.
- Datenkonsistenz: MySQL, Qdrant und Neo4j müssen durch ETL-Läufe synchron gehalten
  werden; Abweichungen sind möglich.
- Neo4j optional: Wenn `NEO4J_URI` nicht konfiguriert ist, greift `NoOpNeo4jRepository`
  – die Graph-Anreicherung entfällt stillschweigend, ohne Fehlermeldung an den Nutzer.
- Betriebsaufwand: Eigener Neo4j-Container im docker-compose, separate Authentifizierung
  und Backup-Strategie erforderlich.

### Einsatz im Projekt

Graph-RAG ist unter `/graph-rag` und `/search?type=graph` erreichbar. Die Route setzt
`use_graph_enrichment=True`, während die reine RAG-Route (`/rag`) diesen Parameter
auf `False` setzt.

---

## 5. Gesamtvergleich

| Kriterium                  | SQL (LIKE)         | Vektorsuche           | RAG                   | Graph-RAG              |
|----------------------------|--------------------|-----------------------|-----------------------|------------------------|
| **Suchmechanismus**        | Zeichenketten-Match | Kosinus-Ähnlichkeit  | Vektor + LLM          | Vektor + Graph + LLM   |
| **Semantik**               | Nein               | Ja                    | Ja                    | Ja + Beziehungskontext |
| **Relevanzranking**        | Nein               | Score 0–1             | Score + LLM-Auswahl   | Score + Graph + LLM    |
| **Antwortformat**          | Rohdaten (Liste)   | Rohdaten (Liste)      | Formulierte Antwort   | Formulierte Antwort    |
| **Datenbankabhängigkeiten**| MySQL              | MySQL + Qdrant        | MySQL + Qdrant + API  | MySQL + Qdrant + Neo4j + API |
| **ETL-Voraussetzung**      | Keine              | Ja (Qdrant-Indexierung) | Ja                  | Ja (Qdrant + Neo4j)    |
| **Latenz**                 | Niedrig            | Mittel (Modell-Inferenz) | Hoch (+ API-RTT)  | Sehr hoch (+ Cypher + API-RTT) |
| **Deterministisch**        | Ja                 | Ja (Approximate)      | Nein                  | Nein                   |
| **Auditierbarkeit**        | Hoch (etl_run_log) | Mittel                | Gering (LLM-Output)   | Gering                 |
| **Kosten**                 | Keine API-Kosten   | Keine API-Kosten      | Token-Kosten (OpenAI) | Token-Kosten (OpenAI)  |
| **Halluzinationsrisiko**   | Kein               | Kein                  | Vorhanden             | Vorhanden              |
| **Komplexität (Betrieb)**  | Niedrig            | Mittel                | Mittel                | Hoch                   |

---

## 6. Fazit

Die vier Methoden ergänzen sich und decken unterschiedliche Anforderungen ab.

Die **SQL-Suche** ist die zuverlässigste und transparenteste Methode. Sie eignet sich
für exakte Produktsuchen, wenn der Nutzer den genauen Namen oder eine spezifische
Eigenschaft kennt. Das führende Wildcard bei der LIKE-Suche verhindert jedoch die
Indexnutzung, was bei großen Datenmengen zu Performance-Problemen führt.

Die **Vektorsuche** überbrückt die semantische Lücke der LIKE-Suche. Dank
`all-MiniLM-L6-v2` und HNSW-Index in Qdrant werden inhaltlich verwandte Produkte
auch ohne exakte Wortübereinstimmung gefunden. Sie ist die empfohlene Grundlage
für alle suchintensiven Funktionen, erfordert aber einen vorgelagerten ETL-Lauf.

**RAG** eignet sich, wenn der Nutzer eine natürlichsprachliche Frage stellt und
eine ausformulierte Empfehlung erwartet, anstatt selbst eine Trefferliste zu
interpretieren. Die LLM-Abhängigkeit bringt jedoch Kosten, Latenz und
Halluzinationsrisiko mit sich.

**Graph-RAG** ist dann sinnvoll, wenn Beziehungen zwischen Entitäten (Marken,
Kategorien, Tags) für die Antwortqualität entscheidend sind – z. B. „Zeige mir
alle Produkte derselben Marke wie dieses". Die höchste Systemkomplexität und
Latenz machen es zur aufwändigsten Option, rechtfertigt sich aber bei
beziehungsreichen Daten.
