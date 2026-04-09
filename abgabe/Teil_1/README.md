## Teil 1 – Relationales Schema & Datenimport

Name, (MatrNr): Kacper Pawlowski (5022043), Marco Rottler (8971956), Ruven Braun (6136649)

### Inhalt der Abgabe
- `ER-Diagramm.pdf` *(Crow's-Foot-Notation: `||` = 1, `o{` = n; `ProductTag` hat zusammengesetzten PK aus `product_id` + `tag_id`)*
- `schema.sql`
- `import.sql`

### Voraussetzungen
- *docker* und *docker compose* sind installiert.
- Das Projekt wurde im Repo-Root gestartet.

### Ausführung

1. Datenbank-Container starten:
```bash
docker compose up -d mysql
```

2. Schema ausführen (legt `productdb` und alle Tabellen an):

**Linux/macOS/Git Bash:**
```bash
cat abgabe/Teil_1/schema.sql | docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```
**Windows (PowerShell):**
```powershell
Get-Content abgabe\Teil_1\schema.sql | docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```

3. Import ausführen (CSV-Import in Transaktion):

**Linux/macOS/Git Bash:**
```bash
cat abgabe/Teil_1/import.sql | docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```
**Windows (PowerShell):**
```powershell
Get-Content abgabe\Teil_1\import.sql | docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```

### Verifikation
```bash
docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" -D productdb -e "SELECT COUNT(*) AS brands FROM brands; SELECT COUNT(*) AS categories FROM categories; SELECT COUNT(*) AS tags FROM tags; SELECT COUNT(*) AS products FROM products; SELECT COUNT(*) AS product_tags FROM product_tags;"'
```