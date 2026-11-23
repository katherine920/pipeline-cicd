#!/usr/bin/env python3
"""Verifica SLOs basicos: tasa de error < 1% y p95 de latencia < 500 ms (50 peticiones)."""
import sys
import time
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
N, LAT_MAX, ERR_MAX = 50, 0.5, 0.01
tiempos, errores = [], 0
for _ in range(N):
    t0 = time.time()
    try:
        urllib.request.urlopen(URL + "/api/productos", timeout=5).read()
    except Exception:
        errores += 1
    tiempos.append(time.time() - t0)
tiempos.sort()
p95 = tiempos[int(N * 0.95) - 1]
tasa = errores / N
print(f"p95={p95*1000:.1f} ms (max {LAT_MAX*1000:.0f}) | errores={tasa:.2%} (max {ERR_MAX:.0%})")
if p95 > LAT_MAX or tasa > ERR_MAX:
    print("SLO NO CUMPLIDO")
    sys.exit(1)
print("SLO cumplido")
