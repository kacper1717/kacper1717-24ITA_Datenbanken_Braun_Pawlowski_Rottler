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

#### Option A: Terminal

**Hinweis**: .env-Datei muss im Repo-Root liegen, damit die Befehle funktionieren, ansonsten muss .env-Dateipfad mitangegeben werden

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

4. Verfikation:

```bash
docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" -D productdb -e "SELECT COUNT(*) AS brands FROM brands; SELECT COUNT(*) AS categories FROM categories; SELECT COUNT(*) AS tags FROM tags; SELECT COUNT(*) AS products FROM products; SELECT COUNT(*) AS product_tags FROM product_tags;"'
```

### Option B: Im Adminer
1. Adminer-Container starten:
```bash
docker compose up -d adminer
```
2. Adminer im Browser öffnen: `http://localhost:8990`
3. Verbindungsdaten eingeben:
- System: MySQL
- Server: mysql
- Benutzername: root
- Passwort: `MYSQL_ROOT_PASSWORD` (siehe `.env`)
- Datenbank: productdb
4. SQL-Tab öffnen und `schema.sql` sowie `import.sql` nacheinander ausführen (bei import.sql muss "Stop on error" aktiviert sein).

   ![Adminer Stop on error](adminer_instruction.png)
5. Verifikation durch SQL-Tab: `SELECT COUNT(*) AS brands FROM brands; SELECT COUNT(*) AS categories FROM categories; SELECT COUNT(*) AS tags FROM tags; SELECT COUNT(*) AS products FROM products; SELECT COUNT(*) AS product_tags FROM product_tags;`
