#!/usr/bin/env bash
set -euo pipefail
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASS="${DB_PASS:-rootpw}"
DB_NAME="${DB_NAME:-testdb}"
RECORD="${RECORD:-0}"   # 1 = Expected-Dateien neu schreiben
CLI="mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASS} --batch --skip-column-names"
# Nur SELECTs zulassen (Heuristik)
for sql in src/sql/*.sql; do
  if grep -Eiq '(^|[^a-z])(insert|update|delete|merge|replace|create|alter|drop)\b' "$sql"; then
    echo "❌ $sql enthält schreibende/DDL-Statements. Erwartet werden reine SELECTs."
    exit 3
  fi
done
# DB vorbereiten
$CLI -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` /*\!40100 DEFAULT CHARACTER SET utf8mb4 */;"
$CLI -e "SET GLOBAL sql_mode='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';"
$CLI -e "SET GLOBAL time_zone='+00:00';"
$CLI "${DB_NAME}" < tests/fixtures/seed.sql
mkdir -p tests/out tests/expected
fail=0
for sql in src/sql/*.sql; do
  name="$(basename "$sql" .sql)"
  out="tests/out/${name}.csv"
  exp="tests/expected/${name}.csv"
  $CLI "${DB_NAME}" < "$sql" > "$out"
  sed -i 's/\r$//' "$out"
  sed -i 's/[[:space:]]\+$//' "$out"
  if [ "$RECORD" = "1" ]; then
    cp -f "$out" "$exp"
    echo "📝 Recorded: $exp"
  elif [ ! -f "$exp" ]; then
    echo "⏭️  Skipped (no expected file): ${name}"
  elif ! diff -u "$exp" "$out"; then
    echo "❌ Test failed: ${name}"
    fail=1
  else
    echo "✅ Test passed: ${name}"
  fi
done
exit $fail