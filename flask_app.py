"""Adaptación Flask de las rutas del servidor local v0.5.6, solo para laboratorio."""
from pathlib import Path
from datetime import datetime
import json
import os
import re
import sqlite3

from flask import Flask, jsonify, request, send_from_directory

BASE = Path(__file__).resolve().parent
CFG = json.loads((BASE / "config/settings.json").read_text(encoding="utf-8"))
DB = BASE / "data/ordenes.db"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200_000


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB, timeout=20) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS ordenes (id INTEGER PRIMARY KEY AUTOINCREMENT, creado TEXT NOT NULL, contenido TEXT NOT NULL)")
        db.execute('CREATE TABLE IF NOT EXISTS numeros (numero TEXT PRIMARY KEY, orden_id INTEGER UNIQUE, fecha TEXT NOT NULL, secuencia INTEGER, estado TEXT NOT NULL DEFAULT "CONFIRMADA")')
        db.execute("CREATE INDEX IF NOT EXISTS idx_numeros_fecha ON numeros(fecha,secuencia)")


init_db()


@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


@app.get("/")
def home():
    return send_from_directory(BASE / "web", "index.html")


@app.get("/api/config")
def config():
    return jsonify(CFG)


@app.get("/api/ad/buscar")
def ad_disabled():
    return jsonify({"disponible": False, "resultados": [], "mensaje": "Directorio deshabilitado en laboratorio. Ingrese datos ficticios manualmente."})


@app.get("/api/ordenes")
def list_orders():
    with sqlite3.connect(DB, timeout=20) as db:
        rows = db.execute("SELECT o.id,o.creado,o.contenido,n.numero FROM ordenes o LEFT JOIN numeros n ON n.orden_id=o.id ORDER BY o.id DESC LIMIT 100").fetchall()
    return jsonify([{"id": i, "creado": c, "numero": n, "orden": json.loads(d)} for i,c,d,n in rows])


@app.get("/api/proximo")
def next_number():
    day = datetime.now().strftime("%Y%m%d")
    with sqlite3.connect(DB, timeout=20) as db:
        seq = db.execute("SELECT COALESCE(MAX(secuencia),0)+1 FROM numeros WHERE fecha=?", (day,)).fetchone()[0]
    return jsonify({"sugerido": f"OD-{day}-{seq:03d}", "nota": "Orientativo: el definitivo se reserva al confirmar"})


@app.post("/api/ordenes")
def save_order():
    try:
        d = request.get_json(silent=True)
        if not isinstance(d, dict):
            raise ValueError("Solicitud inválida")
        if not all(isinstance(d.get(k), str) and d[k].strip() for k in ("responsable", "area", "origen", "destino", "parrafo")):
            raise ValueError("Faltan campos obligatorios")
        if d.get("tipo") not in CFG["movimientos"]:
            raise ValueError("Tipo de movimiento inválido")
        if CFG["movimientos"][d["tipo"]].get("requiere_responsable_anterior") and not all(isinstance(d.get(k), str) and d[k].strip() for k in ("responsable_anterior", "area_anterior")):
            raise ValueError("Faltan datos del responsable anterior")
        items = d.get("bienes")
        if not isinstance(items, list) or not 1 <= len(items) <= 30:
            raise ValueError("Debe incluir de 1 a 30 bienes")
        if any(not isinstance(x, dict) or not x.get("descripcion") or not x.get("serie") or not x.get("modelo") for x in items):
            raise ValueError("Bien incompleto")
        firmantes = d.get("firmantes")
        if not isinstance(firmantes, dict) or any(not isinstance(firmantes.get(k), str) or not firmantes[k].strip() for k in ("gerente_nombre", "gerente_cargo", "patrimonio_nombre", "patrimonio_cargo", "entrega_nombre", "entrega_cargo", "recepcion_nombre", "recepcion_cargo")):
            raise ValueError("Faltan datos de firmantes")
        manual = bool(d.get("numero_manual"))
        requested = str(d.get("numero", "")).strip().upper()
        if manual and (not requested or len(requested) > 45 or not re.fullmatch(r"[A-Z0-9][A-Z0-9\-/]*", requested)):
            raise ValueError("Número manual inválido")
        day = datetime.now().strftime("%Y%m%d")
        with sqlite3.connect(DB, timeout=20, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                seq = None
                if manual:
                    num = requested
                    if db.execute("SELECT 1 FROM numeros WHERE numero=?", (num,)).fetchone():
                        raise ValueError("Ese número ya está registrado")
                else:
                    seq = db.execute("SELECT COALESCE(MAX(secuencia),0)+1 FROM numeros WHERE fecha=?", (day,)).fetchone()[0]
                    num = f"OD-{day}-{seq:03d}"
                    while db.execute("SELECT 1 FROM numeros WHERE numero=?", (num,)).fetchone():
                        seq += 1
                        num = f"OD-{day}-{seq:03d}"
                for item in items:
                    item["cantidad"] = 1
                d["numero"] = num
                d["fecha_confirmacion"] = datetime.now().isoformat(timespec="seconds")
                cur = db.execute("INSERT INTO ordenes(creado,contenido) VALUES (?,?)", (d["fecha_confirmacion"], json.dumps(d, ensure_ascii=False)))
                db.execute("INSERT INTO numeros(numero,orden_id,fecha,secuencia) VALUES (?,?,?,?)", (num, cur.lastrowid, day, seq))
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
        return jsonify({"id": cur.lastrowid, "numero": num, "mensaje": "Orden confirmada"}), 201
    except (ValueError, TypeError, sqlite3.Error) as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8085")), debug=False)
