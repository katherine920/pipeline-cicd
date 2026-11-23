#!/usr/bin/env bash
# Pruebas de humo: uso ./smoke_test.sh http://host:puerto
set -euo pipefail
URL="${1:-http://localhost:8000}"
fallos=0
check() {
  local ruta="$1" esperado="$2"
  codigo=$(curl -s -o /dev/null -w "%{http_code}" "$URL$ruta")
  if [ "$codigo" = "$esperado" ]; then echo "OK   $ruta -> $codigo"
  else echo "FAIL $ruta -> $codigo (esperado $esperado)"; fallos=$((fallos+1)); fi
}
check /health 200
check /api/productos 200
check /metrics 200
check /api/pedidos/999999 404
[ "$fallos" -eq 0 ] && echo "Pruebas de humo exitosas" || { echo "$fallos prueba(s) fallaron"; exit 1; }
