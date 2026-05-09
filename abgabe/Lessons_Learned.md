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

## Best Practices

- `.env` nicht in Git committen!!!!, sondern nur Beispielwerte in `.env.example` pflegen.
- Secrets wie `OPENAI_API_KEY` sicher verwalten
- LLM-Testing: Es gibt fast Keine LLMs die API Keys kostenlos anbeiten, aber es hat sich herausgestellt dass die Webseite **OpenRouter** mehrere kostenlose API-Anfragen ermöglichen, was ideal für die LLM-Integration ohne Kosten war. (https://openrouter.ai/)
