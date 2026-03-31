Teil 1 Anforderungen:
- schema.sql, muss mit ER.PDF übereinstimmen
- import.sql, mit Transaktionen
- Name, MatrNr
- README.md mit Anleitung zum Ausführen der SQL-Dateien

## Teil 1 - Datenmodell

Name, (MatrNr): Kacper Pawlowski (5022043), Marco Rottler (8971956), Ruven Braun (6136649)

### Inhalt der Abgabe
- `ER-Modell.pdf`
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

```bash
cat abgabe/Teil_1/schema.sql | docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```

3. Import ausführen (CSV-Import in Transaktion):

```bash
cat abgabe/Teil_1/import.sql | docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD"'
```

### Verifikation
```bash
docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" -D productdb -e "SELECT COUNT(*) AS brands FROM brands; SELECT COUNT(*) AS categories FROM categories; SELECT COUNT(*) AS tags FROM tags; SELECT COUNT(*) AS products FROM products; SELECT COUNT(*) AS product_tags FROM product_tags;"'
```
