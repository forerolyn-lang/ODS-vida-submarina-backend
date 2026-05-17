from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Species, User

species_bp = Blueprint("species", __name__)


def _require_admin_or_investigator():
    user_id = int(get_jwt_identity())
    user    = db.session.get(User, user_id)
    if not user or user.role not in ("admin", "investigador"):
        return None, (jsonify({"error": "Sin permisos para esta acción"}), 403)
    return user, None


# ── GET /api/species ──────────────────────────────────────────────────────────
@species_bp.route("", methods=["GET"])
@jwt_required()
def list_species():
    status = request.args.get("status")
    search = request.args.get("q", "").strip()
    page   = int(request.args.get("page", 1))
    size   = min(int(request.args.get("size", 20)), 100)

    query = Species.query
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            Species.scientific_name.ilike(f"%{search}%") |
            Species.common_name.ilike(f"%{search}%")
        )

    paginated = query.order_by(Species.common_name).paginate(
        page=page, per_page=size, error_out=False
    )
    return jsonify({
        "items":    [s.to_dict(include_stats=True) for s in paginated.items],
        "total":    paginated.total,
        "page":     page,
        "pages":    paginated.pages,
    }), 200


# ── GET /api/species/<id> ─────────────────────────────────────────────────────
@species_bp.route("/<int:species_id>", methods=["GET"])
@jwt_required()
def get_species(species_id):
    sp = db.session.get(Species, species_id)
    if not sp:
        return jsonify({"error": "Especie no encontrada"}), 404
    return jsonify(sp.to_dict(include_stats=True)), 200


# ── POST /api/species ─────────────────────────────────────────────────────────
@species_bp.route("", methods=["POST"])
@jwt_required()
def create_species():
    _, err = _require_admin_or_investigador()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    sci  = (data.get("scientific_name") or "").strip()
    com  = (data.get("common_name")     or "").strip()

    if not sci or not com:
        return jsonify({"error": "scientific_name y common_name son requeridos"}), 400

    if Species.query.filter_by(scientific_name=sci).first():
        return jsonify({"error": "Ya existe esa especie"}), 409

    sp = Species(
        scientific_name = sci,
        common_name     = com,
        description     = data.get("description"),
        status          = data.get("status", "activo"),
        emoji           = data.get("emoji", "🐟"),
        image_url       = data.get("image_url"),
    )
    db.session.add(sp)
    db.session.commit()
    return jsonify(sp.to_dict()), 201


# ── PUT /api/species/<id> ─────────────────────────────────────────────────────
@species_bp.route("/<int:species_id>", methods=["PUT"])
@jwt_required()
def update_species(species_id):
    _, err = _require_admin_or_investigador()
    if err:
        return err

    sp = db.session.get(Species, species_id)
    if not sp:
        return jsonify({"error": "Especie no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    for field in ("scientific_name", "common_name", "description", "status", "emoji", "image_url"):
        if field in data:
            setattr(sp, field, data[field])

    db.session.commit()
    return jsonify(sp.to_dict()), 200


# ── DELETE /api/species/<id> ──────────────────────────────────────────────────
@species_bp.route("/<int:species_id>", methods=["DELETE"])
@jwt_required()
def delete_species(species_id):
    user_id = int(get_jwt_identity())
    user    = db.session.get(User, user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Solo administradores pueden eliminar especies"}), 403

    sp = db.session.get(Species, species_id)
    if not sp:
        return jsonify({"error": "Especie no encontrada"}), 404

    db.session.delete(sp)
    db.session.commit()
    return jsonify({"message": "Especie eliminada"}), 200


def _require_admin_or_investigador():
    user_id = int(get_jwt_identity())
    user    = db.session.get(User, user_id)
    if not user or user.role not in ("admin", "investigador"):
        return None, (jsonify({"error": "Sin permisos para esta acción"}), 403)
    return user, None
