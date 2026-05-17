from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User

users_bp = Blueprint("users", __name__)


def _require_admin():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or user.role != "admin":
        return None, (jsonify({"error": "Solo administradores"}), 403)
    return user, None


# ── GET /api/users ─────────────────────────────────────────────────────────────
@users_bp.route("", methods=["GET"])
@jwt_required()
def list_users():
    _, err = _require_admin()
    if err:
        return err

    page   = int(request.args.get("page", 1))
    size   = min(int(request.args.get("size", 20)), 100)
    role   = request.args.get("role")
    search = request.args.get("q", "").strip()

    query = User.query
    if role:   query = query.filter_by(role=role)
    if search: query = query.filter(
        User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
    )

    paginated = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )
    return jsonify({
        "items": [u.to_dict(include_stats=True) for u in paginated.items],
        "total": paginated.total,
        "page":  page,
        "pages": paginated.pages,
    }), 200


# ── GET /api/users/<id> ────────────────────────────────────────────────────────
@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    current_id = int(get_jwt_identity())
    current    = db.session.get(User, current_id)

    # Cada usuario puede ver su propio perfil; admins pueden ver cualquiera
    if current_id != user_id and current.role != "admin":
        return jsonify({"error": "Sin permisos"}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user.to_dict(include_stats=True)), 200


# ── PUT /api/users/<id> ────────────────────────────────────────────────────────
@users_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_id = int(get_jwt_identity())
    current    = db.session.get(User, current_id)

    if current_id != user_id and current.role != "admin":
        return jsonify({"error": "Sin permisos"}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json(silent=True) or {}

    # Solo el admin puede cambiar rol e is_active
    if "role" in data and current.role == "admin":
        user.role = data["role"]
    if "is_active" in data and current.role == "admin":
        user.is_active = bool(data["is_active"])
    if "full_name" in data:
        user.full_name = data["full_name"].strip()
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"]

    db.session.commit()
    return jsonify(user.to_dict()), 200


# ── DELETE /api/users/<id> ─────────────────────────────────────────────────────
@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    _, err = _require_admin()
    if err:
        return err

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Soft delete en lugar de borrar
    user.is_active = False
    db.session.commit()
    return jsonify({"message": "Usuario desactivado"}), 200
