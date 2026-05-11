# Lessons Learned

Kurze Zusammenfassung der wichtigsten Erkenntnisse, Probleme und Best Practices aus der Implementierung, Fehlerbehebung und dem Betrieb des Projekts.

## Datenmodell & Schema

- Entitäten in ER-Diagrammen im Singular und in PascalCase benennen, SQL-Tabellen dagegen im Plural.
- M:N-Beziehungen immer über Zuordnungstabellen auflösen.
- Constraints wie `NOT NULL` und `CHECK` direkt im Schema definieren.
- `ON DELETE` und `ON UPDATE` immer explizit setzen, statt MySQL-Defaults zu verwenden.
- `DROP DATABASE IF EXISTS` erleichtert wiederholbare Setups.

## Import & Transaktionen

- Im interaktiven MySQL-Terminal oder in Adminer bleibt die Session offen, dadurch gibt es kein automatisches Rollback wie bei einem abgebrochenen Skript im Terminal
- `LOAD DATA INFILE` ist in Stored Procedures nicht erlaubt.
- `cat import.sql | mysql` ist auf Linux, macOS und Git Bash praktisch für schnelle Tests ohne extra in Adminer-Oberfläche reingehen zu müssen, auf Windows PowerShell wird stattdessen `Get-Content` verwendet.

## Container & Entwicklung

- Änderungen an Python-Code oder Indexing-Logik erfordern oft einen Container-Restart, damit alter Code nicht weiterverwendet wird. (Hat oft zu Verwirrung geführt, wenn Änderungen nicht sofort sichtbar waren..)
- Nach Änderungen an Embeddings oder Payload-Strukturen sollte der Index neu aufgebaut werden.
- `docker compose down -v` löscht Volumes und initialisiert Datenbanken beim nächsten Start neu **– Achtung: Audit-Logs gehen verloren!**
- Die `.env`-Datei muss im Repository-Root liegen, damit `docker compose` die Variablen findet.

## Datenhaltung & Mappings

- Feldnamen in allen Schichten konsistent halten, zum Beispiel `name` statt `title` und `document` statt `doc_preview`.
- Bei Payload-Änderungen im Index ist ein Rebuild nötig, damit alle Daten die neuen Felder enthalten.
- Für Debugging Qdrant direkt mit Payload prüfen, statt nur über die UI zu gehen.

## Tests & Workflow

- Große Änderungen in kleine, überprüfbare Schritte aufteilen. (keine zu großen Commits, sondern lieber in kleiner Commits aufteilen, vor allem bei Gruppenarbeiten mit mehreren Personen)
- Vor großen Änderungen/Features neuen Branch anlegen.
- Nach Änderungen Smoke-Tests durchführen, zum Beispiel Container-Restart und Index-Rebuild

## Stored Procedures

- `DELIMITER $$` ist zwingend nötig, damit MySQL den Prozedur-Body nicht vorzeitig bei jedem `;` beendet.
- `SIGNAL SQLSTATE '45000'` ermöglicht fachliche Fehler (z. B. Pflichtfeld fehlt, negativer Preis) sauber aus der Prozedur heraus zu werfen – kein separates Error-Handling im aufrufenden Code nötig.
- `INSERT … ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)` ist ein zuverlässiges Muster, um einen Datensatz zu holen oder anzulegen, ohne vorher ein `SELECT` zu machen (Upsert-Muster).
- Dubletten-Prüfung muss explizit implementiert werden, wenn kein `UNIQUE`-Constraint auf der Tabelle liegt.
- `LOAD DATA INFILE` ist innerhalb von Stored Procedures nicht erlaubt – CSV-Import muss außerhalb erfolgen.

## Transaktionen

- `START TRANSACTION` / `COMMIT` / `ROLLBACK` müssen immer explizit gesetzt werden –> MySQL öffnet sonst pro Statement eine eigene Auto-Commit-Transaktion.
- Fachliche Fehler (z. B. Duplikat-Check) lösen keinen automatischen Rollback aus; die Entscheidung COMMIT/ROLLBACK muss selbst per `IF`-Logik getroffen werden.
- `ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)` in Verbindung mit `LAST_INSERT_ID()` ist idempotent und damit transaktionssicher wiederholbar.
- Bei konsistenten Updates immer alle abhängigen Tabellen (hier: `product_tags`) im selben Block anfassen – nie nur die Haupttabelle updaten.
- `ON DELETE CASCADE` in `product_tags` sorgt dafür, dass beim Löschen eines Produkts keine verwaisten Zeilen zurückbleiben. Referenzielle Integrität kann so über das Schema statt per Hand gewährleistet werden.

## Trigger & Audit-Log

- Trigger laufen unsichtbar im Hintergrund – `AFTER UPDATE` schreibt automatisch in die Audit-Tabelle, ohne dass der aufrufende Code davon wissen muss.
- `OLD.<feld>` und `NEW.<feld>` geben innerhalb des Triggers Zugriff auf den Zustand vor und nach der Änderung.
- `docker compose down -v` löscht auch die Audit-Tabelle –> Audit-Logs müssen vorher gesichert werden, wenn sie relevant sind.
- Trigger können nicht für `LOAD DATA INFILE` genutzt werden; bulk-importierte Daten landen nicht im Audit-Log.

## Indizes & Performance

- Fremdschlüsselspalten (`brand_id`, `category_id`) sollten immer explizit indiziert werden – InnoDB legt für FKs keinen separaten Index an.
- B+-Tree-Indizes (MySQL-Standard) unterstützen `=`, `BETWEEN`, `>`, `<` und `ORDER BY` effizient, ein führendes `%` in `LIKE '%abc%'` verhindert die Index-Nutzung.
- `EXPLAIN` zeigt, ob ein Index wirklich genutzt wird (`key`-Spalte); ohne vorherigen `ANALYZE TABLE` können veraltete Statistiken falsche Ergebnisse liefern.
- Idempotentes Index-Anlegen: Vorher per `information_schema.statistics` prüfen, ob der Index schon existiert, statt blind `CREATE INDEX` auszuführen.

## Best Practices

- `.env` nicht in Git committen!!!!, sondern nur Beispielwerte in `.env.example` pflegen.
- Secrets wie `OPENAI_API_KEY` sicher verwalten
- LLM-Testing: Es gibt fast Keine LLMs die API Keys kostenlos anbeiten, aber es hat sich herausgestellt dass die Webseite **OpenRouter** mehrere kostenlose API-Anfragen ermöglichen, was ideal für die LLM-Integration ohne Kosten war. (https://openrouter.ai/)
