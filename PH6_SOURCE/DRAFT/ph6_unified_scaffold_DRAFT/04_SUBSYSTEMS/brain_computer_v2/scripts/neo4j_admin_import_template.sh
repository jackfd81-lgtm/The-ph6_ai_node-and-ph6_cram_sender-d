#!/usr/bin/env bash
set -euo pipefail

# Neo4j bulk import template for Brain Computer v2 exports.
# Uses neo4j-admin database import against an empty or offline target database.
# neo4j-admin cannot import into a running populated database.[web:270][web:272]

NEO4J_HOME="${NEO4J_HOME:-/opt/neo4j}"
DATABASE_NAME="${DATABASE_NAME:-brain_v2}"
IMPORT_DIR="${IMPORT_DIR:-$(pwd)/output}"
NODES_CSV="${NODES_CSV:-$IMPORT_DIR/nodes.csv}"
RELATIONSHIPS_CSV="${RELATIONSHIPS_CSV:-$IMPORT_DIR/relationships.csv}"
OVERWRITE="${OVERWRITE:-true}"
ID_TYPE="${ID_TYPE:-string}"

if [[ ! -f "$NODES_CSV" ]]; then
  echo "Missing nodes CSV: $NODES_CSV" >&2
  exit 1
fi

if [[ ! -f "$RELATIONSHIPS_CSV" ]]; then
  echo "Missing relationships CSV: $RELATIONSHIPS_CSV" >&2
  exit 1
fi

NEO4J_ADMIN="$NEO4J_HOME/bin/neo4j-admin"
if [[ ! -x "$NEO4J_ADMIN" ]]; then
  echo "neo4j-admin not found or not executable: $NEO4J_ADMIN" >&2
  exit 1
fi

echo "Preparing Neo4j bulk import"
echo "  NEO4J_HOME=$NEO4J_HOME"
echo "  DATABASE_NAME=$DATABASE_NAME"
echo "  NODES_CSV=$NODES_CSV"
echo "  RELATIONSHIPS_CSV=$RELATIONSHIPS_CSV"

echo "Ensure the target database is empty or Neo4j is offline before import." 

action=(
  "$NEO4J_ADMIN" database import full
  --overwrite-destination="$OVERWRITE"
  --id-type="$ID_TYPE"
  --nodes="$NODES_CSV"
  --relationships="$RELATIONSHIPS_CSV"
  "$DATABASE_NAME"
)

printf 'Command:\n  %q' "${action[0]}"
for ((i=1; i<${#action[@]}; i++)); do
  printf ' %q' "${action[i]}"
done
printf '\n'

"${action[@]}"

echo "Import complete for database: $DATABASE_NAME"
echo "You can start Neo4j and connect to the imported database afterward."
