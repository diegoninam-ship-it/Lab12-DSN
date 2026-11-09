"""T2: permisos de salas (sección 5) — un no-miembro siempre recibe 404
(nunca revela que la sala existe); un miembro sin ser dueño recibe 403 en
las acciones exclusivas del dueño."""

from tests import fabrica


def _crear_sala(como, dueno, nombre="Sala de prueba"):
    respuesta = como(dueno).post("/api/salas", json={"nombre": nombre})
    assert respuesta.status_code == 201
    return respuesta.json()


def test_crear_sala_queda_como_dueno_y_miembro(como, usuario):
    sala = _crear_sala(como, usuario)

    assert sala["es_dueno"] is True
    apodos = {m["apodo"] for m in sala["miembros"]}
    assert usuario.apodo in apodos


def test_no_miembro_recibe_404_en_detalle(como, usuario, session):
    sala = _crear_sala(como, usuario)
    externo = fabrica.crear_usuario(session)

    respuesta = como(externo).get(f"/api/salas/{sala['id']}")

    assert respuesta.status_code == 404


def test_sala_inexistente_404_en_detalle(como, usuario):
    respuesta = como(usuario).get("/api/salas/999999")
    assert respuesta.status_code == 404


def test_miembro_ve_el_detalle(como, usuario):
    sala = _crear_sala(como, usuario)

    respuesta = como(usuario).get(f"/api/salas/{sala['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == sala["id"]


def test_listar_mis_salas(como, usuario):
    _crear_sala(como, usuario, "Sala A")
    _crear_sala(como, usuario, "Sala B")

    respuesta = como(usuario).get("/api/salas")

    assert respuesta.status_code == 200
    nombres = {s["nombre"] for s in respuesta.json()}
    assert {"Sala A", "Sala B"}.issubset(nombres)


def test_ranking_de_sala_con_miembros(como, usuario, session):
    sala = _crear_sala(como, usuario)
    miembro = fabrica.crear_usuario(session)
    como(miembro).post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    respuesta = como(usuario).get(f"/api/salas/{sala['id']}/ranking")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["sala_id"] == sala["id"]
    apodos = {i["apodo"] for i in cuerpo["items"]}
    assert {usuario.apodo, miembro.apodo} == apodos


def test_no_miembro_recibe_404_en_ranking(como, usuario, session):
    sala = _crear_sala(como, usuario)
    externo = fabrica.crear_usuario(session)

    respuesta = como(externo).get(f"/api/salas/{sala['id']}/ranking")

    assert respuesta.status_code == 404


def test_unirse_con_codigo_valido(como, usuario, session):
    sala = _crear_sala(como, usuario)
    nuevo = fabrica.crear_usuario(session)

    respuesta = como(nuevo).post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    assert respuesta.status_code == 200
    apodos = {m["apodo"] for m in respuesta.json()["miembros"]}
    assert nuevo.apodo in apodos


def test_unirse_ya_siendo_miembro_no_duplica(como, usuario, session):
    sala = _crear_sala(como, usuario)
    nuevo = fabrica.crear_usuario(session)
    cliente_nuevo = como(nuevo)
    cliente_nuevo.post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    respuesta = cliente_nuevo.post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    assert respuesta.status_code == 200
    miembros = respuesta.json()["miembros"]
    assert len([m for m in miembros if m["apodo"] == nuevo.apodo]) == 1


def test_unirse_con_codigo_invalido_404(como, usuario):
    respuesta = como(usuario).post("/api/salas/unirse", json={"codigo": "NOEXISTE"})
    assert respuesta.status_code == 404


def test_dueno_no_puede_salir_409(como, usuario):
    sala = _crear_sala(como, usuario)

    respuesta = como(usuario).post(f"/api/salas/{sala['id']}/salir")

    assert respuesta.status_code == 409


def test_miembro_puede_salir(como, usuario, session):
    sala = _crear_sala(como, usuario)
    miembro = fabrica.crear_usuario(session)
    cliente_miembro = como(miembro)
    cliente_miembro.post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    respuesta = cliente_miembro.post(f"/api/salas/{sala['id']}/salir")
    assert respuesta.status_code == 200

    # Al salir, deja de ser miembro: el detalle ahora le da 404.
    detalle = cliente_miembro.get(f"/api/salas/{sala['id']}")
    assert detalle.status_code == 404


def test_regenerar_codigo_solo_dueno(como, usuario, session):
    sala = _crear_sala(como, usuario)
    miembro = fabrica.crear_usuario(session)
    como(miembro).post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    respuesta = como(miembro).post(f"/api/salas/{sala['id']}/codigo")
    assert respuesta.status_code == 403


def test_regenerar_codigo_invalida_el_anterior(como, usuario, session):
    sala = _crear_sala(como, usuario)
    codigo_viejo = sala["codigo_invitacion"]

    respuesta = como(usuario).post(f"/api/salas/{sala['id']}/codigo")
    assert respuesta.status_code == 200
    codigo_nuevo = respuesta.json()["codigo_invitacion"]
    assert codigo_nuevo != codigo_viejo

    externo = fabrica.crear_usuario(session)
    unirse = como(externo).post("/api/salas/unirse", json={"codigo": codigo_viejo})
    assert unirse.status_code == 404


def test_expulsar_solo_dueno(como, usuario, session):
    sala = _crear_sala(como, usuario)
    miembro = fabrica.crear_usuario(session)
    como(miembro).post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})
    otro_miembro = fabrica.crear_usuario(session)
    como(otro_miembro).post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    # El miembro (no dueño) no puede expulsar a otro miembro.
    respuesta = como(miembro).delete(f"/api/salas/{sala['id']}/miembros/{otro_miembro.id}")
    assert respuesta.status_code == 403

    # El dueño sí puede.
    respuesta = como(usuario).delete(f"/api/salas/{sala['id']}/miembros/{otro_miembro.id}")
    assert respuesta.status_code == 204


def test_dueno_no_puede_expulsarse_a_si_mismo_409(como, usuario):
    sala = _crear_sala(como, usuario)

    respuesta = como(usuario).delete(f"/api/salas/{sala['id']}/miembros/{usuario.id}")

    assert respuesta.status_code == 409


def test_expulsar_a_quien_no_es_miembro_404(como, usuario, session):
    sala = _crear_sala(como, usuario)
    externo = fabrica.crear_usuario(session)

    respuesta = como(usuario).delete(f"/api/salas/{sala['id']}/miembros/{externo.id}")

    assert respuesta.status_code == 404


def test_eliminar_sala_solo_dueno(como, usuario, session):
    sala = _crear_sala(como, usuario)
    miembro = fabrica.crear_usuario(session)
    como(miembro).post("/api/salas/unirse", json={"codigo": sala["codigo_invitacion"]})

    respuesta = como(miembro).delete(f"/api/salas/{sala['id']}")
    assert respuesta.status_code == 403

    respuesta = como(usuario).delete(f"/api/salas/{sala['id']}")
    assert respuesta.status_code == 204
