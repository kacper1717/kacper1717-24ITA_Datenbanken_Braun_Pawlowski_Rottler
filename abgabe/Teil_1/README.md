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

#### Option A – Terminal

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

#### Option B – Adminer (Web UI)

Alternativ können `schema.sql` und `import.sql` über Adminer unter http://localhost:8990 ausgeführt werden (Container mit `docker compose up -d mysql adminer` starten, dann unter SQL-Befehl ausführen einfügen).

### Verifikation
```bash
docker compose exec -T mysql sh -lc 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" -D productdb -e "SELECT COUNT(*) AS brands FROM brands; SELECT COUNT(*) AS categories FROM categories; SELECT COUNT(*) AS tags FROM tags; SELECT COUNT(*) AS products FROM products; SELECT COUNT(*) AS product_tags FROM product_tags;"'
```