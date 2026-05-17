from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


# ── POST /api/auth/register ───────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email     = (data.get("email")     or "").strip().lower()
    password  = data.get("password", "")
    role      = data.get("role", "entusiasta")

    # Validaciones básicas
    if not full_name or not email or not password:
        return jsonify({"error": "full_name, email y password son requeridos"}), 400

    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    valid_roles = {"investigador", "estudiante", "educador", "entusiasta"}
    if role not in valid_roles:
        return jsonify({"error": f"Rol inválido. Opciones: {', '.join(valid_roles)}"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con ese correo"}), 409

    user = User(full_name=full_name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message":       "Cuenta creada exitosamente",
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    }), 201


# ── POST /api/auth/login ──────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email y password son requeridos"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    if not user.is_active:
        return jsonify({"error": "Cuenta desactivada. Contacta al administrador"}), 403

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message":       "Sesión iniciada",
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    }), 200


# ── POST /api/auth/refresh ────────────────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity     = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200


# ── GET /api/auth/me ──────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user    = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({"user": user.to_dict(include_stats=True)}), 200


# ── PUT /api/auth/change-password ─────────────────────────────────────────────
@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user    = db.session.get(User, user_id)
    data    = request.get_json(silent=True) or {}

    current  = data.get("current_password", "")
    new_pass = data.get("new_password", "")

    if not user.check_password(current):
        return jsonify({"error": "Contraseña actual incorrecta"}), 401

    if len(new_pass) < 6:
        return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400

    user.set_password(new_pass)
    db.session.commit()
    return jsonify({"message": "Contraseña actualizada"}), 200
