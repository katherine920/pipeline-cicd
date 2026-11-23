"""API de pedidos TiendaRapida (caso de estudio). Expone /health, /metrics y API REST."""
import time
from flask import Flask, jsonify, request, g, Response

app = Flask(__name__)

PRODUCTOS = [
    {"id": 1, "nombre": "Teclado", "precio": 450.0},
    {"id": 2, "nombre": "Mouse", "precio": 250.0},
    {"id": 3, "nombre": "Monitor", "precio": 3200.0},
]
PEDIDOS = []

# Metricas simples en formato Prometheus (sin dependencias extra)
METRICAS = {"requests": {}, "errors": 0, "duration_sum": 0.0, "duration_count": 0,
            "buckets": {0.1: 0, 0.3: 0, 0.5: 0, 1.0: 0, float("inf"): 0}}
INICIO = time.time()


@app.before_request
def _inicio():
    g.t0 = time.time()


@app.after_request
def _fin(resp):
    dur = time.time() - g.t0
    clave = (request.method, request.path, resp.status_code)
    METRICAS["requests"][clave] = METRICAS["requests"].get(clave, 0) + 1
    if resp.status_code >= 500:
        METRICAS["errors"] += 1
    METRICAS["duration_sum"] += dur
    METRICAS["duration_count"] += 1
    for b in METRICAS["buckets"]:
        if dur <= b:
            METRICAS["buckets"][b] += 1
    return resp


@app.get("/health")
def health():
    return jsonify(status="ok", uptime_s=round(time.time() - INICIO, 1))


@app.get("/api/productos")
def productos():
    return jsonify(PRODUCTOS)


@app.post("/api/pedidos")
def crear_pedido():
    data = request.get_json(silent=True) or {}
    ids = data.get("productos", [])
    if not ids or not all(any(p["id"] == i for p in PRODUCTOS) for i in ids):
        return jsonify(error="productos invalidos"), 400
    total = sum(p["precio"] for p in PRODUCTOS if p["id"] in ids)
    pedido = {"id": len(PEDIDOS) + 1, "productos": ids, "total": total}
    PEDIDOS.append(pedido)
    return jsonify(pedido), 201


@app.get("/api/pedidos/<int:pid>")
def obtener_pedido(pid):
    for p in PEDIDOS:
        if p["id"] == pid:
            return jsonify(p)
    return jsonify(error="no encontrado"), 404


@app.get("/metrics")
def metrics():
    l = []
    l.append("# TYPE http_requests_total counter")
    for (m, p, s), v in METRICAS["requests"].items():
        l.append(f'http_requests_total{{method="{m}",path="{p}",status="{s}"}} {v}')
    l.append("# TYPE http_errors_total counter")
    l.append(f"http_errors_total {METRICAS['errors']}")
    l.append("# TYPE http_request_duration_seconds histogram")
    for b, v in METRICAS["buckets"].items():
        le = "+Inf" if b == float("inf") else b
        l.append(f'http_request_duration_seconds_bucket{{le="{le}"}} {v}')
    l.append(f"http_request_duration_seconds_sum {METRICAS['duration_sum']}")
    l.append(f"http_request_duration_seconds_count {METRICAS['duration_count']}")
    l.append("# TYPE app_uptime_seconds gauge")
    l.append(f"app_uptime_seconds {time.time() - INICIO}")
    return Response("\n".join(l) + "\n", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
