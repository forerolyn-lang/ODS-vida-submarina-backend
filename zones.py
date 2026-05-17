from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Zone, User

zones_bp = Blueprint("zones", __name__)


# ── GET /api/zones ────────────────────────────────────────────────────────────
@zones_bp.route("", methods=["GET"])
@jwt_required()
def list_zones():
    status = request.args.get("status")
    query  = Zone.query
    if status:
        query = query.filter_by(status=status)
    zones = query.order_by(Zone.name).all()
    return jsonify([z.to_dict(include_stats=True) for z in zones]), 200


# ── GET /api/zones/<id> ───────────────────────────────────────────────────────
@zones_bp.route("/<int:zone_id>", methods=["GET"])
@jwt_required()
def get_zone(zone_id):
    zone = db.session.get(Zone, zone_id)
    if not zone:
        return jsonify({"error": "Zona no encontrada"}), 404
    return jsonify(zone.to_dict(include_stats=True)), 200


# ── POST /api/zones ───────────────────────────────────────────────────────────
@zones_bp.route("", methods=["POST"])
@jwt_required()
def create_zone():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or user.role not in ("admin", "investigador"):
        return jsonify({"error": "Sin permisos"}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    lat  = data.get("latitude")
    lng  = data.get("longitude")

    if not name or lat is None or lng is None:
        return jsonify({"error": "name, latitude y longitude son requeridos"}), 400

    zone = Zone(
        name        = name,
        description = data.get("description"),
        latitude    = float(lat),
        longitude   = float(lng),
        status      = data.get("status", "monitoreada"),
        emoji       = data.get("emoji", "🌊"),
    )
    db.session.add(zone)
    db.session.commit()
    return jsonify(zone.to_dict()), 201


# ── PUT /api/zones/<id> ───────────────────────────────────────────────────────
@zones_bp.route("/<int:zone_id>", methods=["PUT"])
@jwt_required()
def update_zone(zone_id):
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or user.role not in ("admin", "investigador"):
        return jsonify({"error": "Sin permisos"}), 403

    zone = db.session.get(Zone, zone_id)
    if not zone:
        return jsonify({"error": "Zona no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    for field in ("name", "description", "latitude", "longitude", "status", "emoji"):
        if field in data:
            setattr(zone, field, data[field])

    db.session.commit()
    return jsonify(zone.to_dict()), 200


# ── DELETE /api/zones/<id> ────────────────────────────────────────────────────
@zones_bp.route("/<int:zone_id>", methods=["DELETE"])
@jwt_required()
def delete_zone(zone_id):
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or user.role != "admin":
        return jsonify({"error": "Solo administradores pueden eliminar zonas"}), 403

    zone = db.session.get(Zone, zone_id)
    if not zone:
        return jsonify({"error": "Zona no encontrada"}), 404

    db.session.delete(zone)
    db.session.commit()
    return jsonify({"message": "Zona eliminada"}), 200
