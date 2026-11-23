#!/usr/bin/env python3
"""Prueba de integracion: flujo completo de un pedido. Uso: integration_test.py URL"""
import json
import sys
import urllib.request
import urllib.error

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def req(metodo, ruta, cuerpo=None):
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    r = urllib.request.Request(URL + ruta, data=data, method=metodo,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def esperar(cond, msg):
    print(("OK   " if cond else "FAIL ") + msg)
    if not cond:
        sys.exit(1)


s, prods = req("GET", "/api/productos")
esperar(s == 200 and len(prods) > 0, "listar productos")
s, ped = req("POST", "/api/pedidos", {"productos": [1, 3]})
esperar(s == 201 and ped["total"] == 3650.0, "crear pedido con total correcto")
s, got = req("GET", f"/api/pedidos/{ped['id']}")
esperar(s == 200 and got["id"] == ped["id"], "consultar pedido creado")
s, _ = req("POST", "/api/pedidos", {"productos": [999]})
esperar(s == 400, "rechazar pedido invalido")
print("Pruebas de integracion exitosas")
