from app.main import app


def cliente():
    return app.test_client()


def test_health():
    r = cliente().get("/health")
    assert r.status_code == 200 and r.json["status"] == "ok"


def test_listar_productos():
    assert len(cliente().get("/api/productos").json) == 3


def test_crear_pedido_ok():
    r = cliente().post("/api/pedidos", json={"productos": [1, 2]})
    assert r.status_code == 201 and r.json["total"] == 700.0


def test_crear_pedido_invalido():
    assert cliente().post("/api/pedidos", json={"productos": [99]}).status_code == 400


def test_pedido_inexistente():
    assert cliente().get("/api/pedidos/9999").status_code == 404


def test_metrics():
    r = cliente().get("/metrics")
    assert r.status_code == 200 and b"http_requests_total" in r.data
