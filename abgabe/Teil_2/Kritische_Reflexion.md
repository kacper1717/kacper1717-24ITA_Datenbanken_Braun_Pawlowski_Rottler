# Kritische Reflexion

---

## 1. Grenzen klassischer relationaler Suche

Die im Projekt verwendete SQL-Suche basiert auf `LIKE '%keyword%'`-Ausdrücken auf den Feldern `name` und `description` der Tabelle `products`. Diese Methode hat strukturelle Grenzen, die unabhängig von der Qualität des Schemas oder der Daten bestehen.

### Fehlende Semantik

SQL kennt keine inhaltliche Ähnlichkeit. Die Suche nach „Fahrradpedal" findet nicht „Pedale", „Tretlager" oder „Klickpedal", solange das exakte Wort nicht im Textfeld steht. Synonyme, Oberbegriffe und verwandte Konzepte sind für die Datenbank unsichtbar. Das ist kein Fehler in der Implementierung, sondern eine fundamentale Eigenschaft des relationalen Modells: Es speichert Fakten, nicht Bedeutungen.

### Index-Inkompatibilität bei führendem Wildcard

Ein `LIKE '%abc%`-Ausdruck mit führendem `%` kann den B+-Tree-Index auf `products.name` nicht nutzen. InnoDB muss jeden Datensatz einzeln prüfen, was in einem Full Table Scan resultiert (O(n)). Mit wachsender Produktanzahl degradiert die Performance direkt proportional – die angelegten Indizes (`idx_products_name`, `idx_products_price` etc.) helfen bei dieser Suchform nicht.

### Keine Relevanzsortierung

Alle Treffer einer LIKE-Suche sind strukturell gleichwertig. Es gibt keinen Score und keine Möglichkeit, „wie gut passt dieses Ergebnis zur Anfrage?" zu quantifizieren. Der Nutzer erhält eine Liste, muss aber selbst einschätzen, welcher Treffer relevant ist.

### Abhängigkeit von Textfeldqualität

Die Trefferquote hängt direkt davon ab, ob `name` und `description` vollständig und konsistent befüllt sind. Kurze, unvollständige oder inkonsistente Beschreibungen reduzieren die Auffindbarkeit, ohne dass die Datenbankstruktur selbst ein Problem wäre.

### Fazit

Die klassische SQL-Suche ist deterministisch, transaktionssicher und auditierbar – und genau deshalb wertvoll. Ihre Grenzen liegen nicht in schlechter Implementierung, sondern im Einsatzbereich: Sie ist präzise für exakte Attribute (Preis, Marke, Kategorie als Filter), aber ungeeignet als primäre Freitext-Suchstrategie bei großen, heterogenen Produktdaten.

---

## 2. Grenzen semantischer Suche

Die Vektorsuche mit `sentence-transformers/all-MiniLM-L6-v2` und dem HNSW-Index in Qdrant überwindet die lexikalische Enge der SQL-Suche, bringt aber eigene strukturelle Schwächen mit.

### Approximate Nearest Neighbour ist nicht exakt

HNSW (Hierarchical Navigable Small Worlds) ist ein Approximate-Nearest-Neighbour-Verfahren. Es garantiert nicht, dass der geometrisch nächste Vektor im Ergebnis erscheint – es findet einen Nachbarn, der mit hoher Wahrscheinlichkeit nah genug ist. Bei den gewählten Parametern (`m=16`, `ef_construct=128`, `hnsw_ef=64`) ist der Recall hoch, aber nie 100 %. Für sicherheitskritische oder vollständigkeitsrelevante Abfragen wäre das nicht akzeptabel.

### Embedding-Qualität begrenzt die Suchqualität

Das Modell `all-MiniLM-L6-v2` erzeugt 384-dimensionale Vektoren. Es wurde auf englischsprachigen Texten trainiert und versteht branchenspezifische Fachbegriffe (z. B. „Tretlager", „Schaltwerk") schlechter als allgemeine Sprache. Das Embedding ist nur so gut wie das Sprachmodell – ein Produktname mit Tippfehler oder ein unbekannter Markenname können zu schlechten Vektoren führen.

### Kein strukturiertes Filtern

Die Vektorsuche findet inhaltlich ähnliche Dokumente, aber sie kann nicht nativ nach Preis < 50 € oder Kategorie = „Radsport" filtern, ohne Payload-Filter in Qdrant explizit zu konfigurieren. Die Suche operiert im Semantikraum, nicht im Werteraum.

### ETL-Kopplung und Konsistenzproblem

Der Qdrant-Index muss manuell über einen ETL-Lauf aktualisiert werden. Wird ein Produkt in MySQL geändert oder gelöscht, bleibt der veraltete Vektor in Qdrant, bis der nächste ETL-Lauf ausgeführt wird. Es gibt keine automatische Synchronisation. In diesem Zustand kann die Vektorsuche Produkte zurückliefern, die in MySQL nicht mehr existieren oder sich verändert haben.

### Kein Bezug zu relationalen Strukturen

Die Vektorsuche kennt keine Fremdschlüssel, Constraints oder JOIN-Logik. Der eingebettete Text ist eine Momentaufnahme des Dokuments zum ETL-Zeitpunkt. Strukturelle Beziehungen (z. B. „Produkte derselben Marke") sind im Vektorraum nicht direkt abfragbar – sie müssen entweder in den Dokumenttext kodiert oder durch einen Graph (wie in der Graph-RAG-Variante) ergänzt werden.

### Fazit

Semantische Suche ist kein Ersatz für strukturierte Abfragen, sondern eine Ergänzung. Ihre Stärke liegt im Auffinden inhaltlich verwandter Treffer bei unscharfen Anfragen. Ihre Grenzen liegen in der Näherungsnatur des Index, der Sprachmodelabhängigkeit und der fehlenden Transaktionssicherheit.

---

## 3. Warum dies keine saubere Datenmodellierung ersetzt

Vektorsuche, RAG und Graph-RAG sind Abfragewerkzeuge, keine Datenbankarchitektur. Sie setzen ein funktionierendes relationales Fundament voraus und können dessen Fehler nicht kompensieren.

### Semantische Suche kaschiert schlechte Datenqualität, korrigiert sie aber nicht

Wenn `description`-Felder leer oder inkonsistent sind, werden die Embeddings unscharf. Die Vektorsuche findet trotzdem etwas – aber nicht das Richtige. Ein Schema ohne NOT-NULL-Constraints, ohne Normalisierung und ohne referentielle Integrität erzeugt Vektoren aus inkonsistentem Input. Das Suchergebnis ist dann semantisch plausibel klingend, aber sachlich falsch.

### Graphdatenbanken ersetzen kein relationales Schema

Neo4j wird im Projekt für die Anreicherung von Produktbeziehungen genutzt. Es modelliert Produkt→Marke, Produkt→Kategorie und Produkt→Tag als Knoten und Kanten. Diese Beziehungen existieren aber bereits in MySQL als Fremdschlüsselbeziehungen (`brand_id`, `category_id`) und der Verbindungstabelle `product_tags`. Neo4j fügt eine Traversierungsperspektive hinzu, ersetzt aber keine strukturierte Datenhaltung mit Constraints und Transaktionen.

### LLM-generierte Antworten sind nicht datenbanktreu

Ein Large Language Model kann im RAG-Kontext Informationen zusammenfassen, umformulieren oder ergänzen, die nicht im übergebenen Kontext stehen (Halluzination). Eine Produktdatenbank erfordert Korrektheit, nicht Plausibilität. Für Preise, Artikelnummern, Verfügbarkeiten oder technische Spezifikationen ist eine LLM-Antwort kein verlässlicher Datenbankausgang.

### Mehrschichtige Systeme erhöhen die Komplexität ohne strukturelle Garantien

Das Projekt nutzt vier Komponenten (MySQL, Qdrant, Neo4j, OpenAI). Jede zusätzliche Schicht erhöht die Ausfallwahrscheinlichkeit, die Synchronisationslast und den Erklärungsaufwand. Eine sauber modellierte relationale Datenbank mit Volltextindex (z. B. MySQL FULLTEXT INDEX) würde viele Anforderungen mit einem Bruchteil der Infrastruktur erfüllen – und dabei transaktionssicher bleiben.

### Fazit

Vektorsuche und LLM-Integration sind sinnvolle Ergänzungen für Anwendungsfälle, in denen Bedeutungsähnlichkeit wichtiger ist als exakte Treffergarantie. Sie setzen aber ein korrekt modelliertes, normalisiertes und constraint-geschütztes Schema voraus. Sie sind Werkzeuge auf dem Fundament – nicht das Fundament selbst.

---

## 4. Warum MySQL die Source of Truth bleibt

Trotz der Ergänzung durch Qdrant und Neo4j ist MySQL im Projekt die einzige autoritative Datenquelle. Das ist eine bewusste Architekturentscheidung mit konkreten Gründen.

### Transaktionssicherheit und ACID-Garantien

MySQL (InnoDB) garantiert Atomicity, Consistency, Isolation und Durability. Jede Schreiboperation ist entweder vollständig committed oder vollständig zurückgerollt. Qdrant und Neo4j bieten keine vergleichbaren transaktionalen Garantien über Systemgrenzen hinweg. Wenn der ETL-Lauf nach dem MySQL-Update aber vor der Qdrant-Synchronisation abbricht, bleibt MySQL konsistent – der Index ist veraltet, aber die Wahrheit ist erhalten.

### Referentielle Integrität und Constraint-Enforcement

Die Tabellen `products`, `brands`, `categories`, `tags` und `product_tags` sind durch Fremdschlüssel und CHECK-Constraints verknüpft. MySQL verhindert strukturell inkonsistente Zustände (z. B. ein Produkt ohne existierende Marke). Qdrant speichert denormalisierte Payloads – dort können verwaiste Einträge entstehen, die in MySQL längst gelöscht wurden.

### Auditierbarkeit

Die Tabelle `etl_run_log` protokolliert alle ETL-Läufe mit Zeitstempel und Status. Für Fragen wie „Welche Daten waren zum Zeitpunkt X im System?" ist MySQL die einzige Quelle, die eine vollständige, zeitgeordnete Antwort geben kann. LLM-Ausgaben und Vektorähnlichkeiten sind nicht rekonstruierbar.

### Einziger Schreibpfad

Im Projekt werden Produkte ausschließlich über MySQL angelegt und verändert. Qdrant und Neo4j sind reine Lesequellen für den Suchpfad – sie werden aus MySQL befüllt, aber nie direkt beschrieben. Dieser unidirektionale Datenfluss (MySQL → ETL → Qdrant/Neo4j) verhindert Konflikte und macht MySQL zum natürlichen Single Point of Truth.

### Schema-Evolution ist in MySQL kontrollierbar

Migrationen, Typänderungen und Constraint-Anpassungen lassen sich in MySQL mit DDL-Statements versionieren und ausrollen. Eine Schemaänderung in MySQL zieht eine Neuindizierung in Qdrant und einen Neuaufbau des Neo4j-Graphen nach sich – aber die Änderung selbst ist in MySQL atomar und rückverfolgbar.

### Fazit

MySQL ist nicht deshalb die Source of Truth, weil die anderen Systeme schlecht sind, sondern weil relationale Datenbanken mit ACID-Semantik für strukturierte, constraints-geprüfte Stammdaten das geeignetste Werkzeug sind. Qdrant und Neo4j erweitern die Abfragefähigkeiten – aber im Konfliktfall gilt: Was MySQL sagt, ist wahr.
