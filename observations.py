import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import Observation, Species, Zone, User

observations_bp = Blueprint("observations", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── GET /api/observations ─────────────────────────────────────────────────────
@observations_bp.route("", methods=["GET"])
@jwt_required()
def list_observations():
    page       = int(request.args.get("page", 1))
    size       = min(int(request.args.get("size", 20)), 100)
    species_id = request.args.get("species_id", type=int)
    zone_id    = request.args.get("zone_id",    type=int)
    user_id    = request.args.get("user_id",    type=int)
    behavior   = request.args.get("behavior")
    date_from  = request.args.get("date_from")   # ISO: 2024-01-01
    date_to    = request.args.get("date_to")

    query = Observation.query
    if species_id: query = query.filter_by(species_id=species_id)
    if zone_id:    query = query.filter_by(zone_id=zone_id)
    if user_id:    query = query.filter_by(user_id=user_id)
    if behavior:   query = query.filter_by(behavior=behavior)
    if date_from:
        from datetime import datetime
        query = query.filter(Observation.observed_at >= datetime.fromisoformat(date_from))
    if date_to:
        from datetime import datetime
        query = query.filter(Observation.observed_at <= datetime.fromisoformat(date_to))

    paginated = query.order_by(Observation.observed_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )
    return jsonify({
        "items":  [o.to_dict() for o in paginated.items],
        "total":  paginated.total,
        "page":   page,
        "pages":  paginated.pages,
    }), 200


# ── GET /api/observations/<id> ────────────────────────────────────────────────
@observations_bp.route("/<int:obs_id>", methods=["GET"])
@jwt_required()
def get_observation(obs_id):
    obs = db.session.get(Observation, obs_id)
    if not obs:
        return jsonify({"error": "Observación no encontrada"}), 404
    return jsonify(obs.to_dict()), 200


# ── POST /api/observations ────────────────────────────────────────────────────
@observations_bp.route("", methods=["POST"])
@jwt_required()
def create_observation():
    user_id = int(get_jwt_identity())

    # Soportar multipart/form-data (con foto) y application/json
    if request.content_type and "multipart" in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json(silent=True) or {}

    # Campos obligatorios
    species_id = data.get("species_id")
    zone_id    = data.get("zone_id")
    quantity   = data.get("quantity", 1)

    if not species_id or not zone_id:
        return jsonify({"error": "species_id y zone_id son requeridos"}), 400

    if not db.session.get(Species, int(species_id)):
        return jsonify({"error": "Especie no encontrada"}), 404
    if not db.session.get(Zone, int(zone_id)):
        return jsonify({"error": "Zona no encontrada"}), 404

    # Manejo de foto
    photo_url = None
    if "photo" in request.files:
        file = request.files["photo"]
        if file and file.filename and allowed_file(file.filename):
            filename  = secure_filename(f"{user_id}_{file.filename}")
            upload_dir = os.path.join(current_app.root_path, current_app.config["UPLOAD_FOLDER"])
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            photo_url = f"/uploads/{filename}"

    obs = Observation(
        user_id       = user_id,
        species_id    = int(species_id),
        zone_id       = int(zone_id),
        quantity      = int(quantity),
        behavior      = data.get("behavior") or None,
        notes         = data.get("notes") or None,
        photo_url     = photo_url,
        latitude      = float(data["latitude"])  if data.get("latitude")  else None,
        longitude     = float(data["longitude"]) if data.get("longitude") else None,
        depth_m       = float(data["depth_m"])   if data.get("depth_m")   else None,
        temperature_c = float(data["temperature_c"]) if data.get("temperature_c") else None,
        salinity_psu  = float(data["salinity_psu"])  if data.get("salinity_psu")  else None,
        visibility    = data.get("visibility")   or None,
        water_state   = data.get("water_state")  or None,
    )
    db.session.add(obs)
    db.session.commit()
    return jsonify(obs.to_dict()), 201


# ── PUT /api/observations/<id> ────────────────────────────────────────────────
@observations_bp.route("/<int:obs_id>", methods=["PUT"])
@jwt_required()
def update_observation(obs_id):
    user_id = int(get_jwt_identity())
    obs     = db.session.get(Observation, obs_id)
    if not obs:
        return jsonify({"error": "Observación no encontrada"}), 404

    user = db.session.get(User, user_id)
    if obs.user_id != user_id and user.role not in ("admin", "investigador"):
        return jsonify({"error": "Sin permisos para editar esta observación"}), 403

    data = request.get_json(silent=True) or {}
    editable = ("quantity", "behavior", "notes", "latitude", "longitude",
                "depth_m", "temperature_c", "salinity_psu", "visibility", "water_state")
    for field in editable:
        if field in data:
            setattr(obs, field, data[field])

    db.session.commit()
    return jsonify(obs.to_dict()), 200


# ── DELETE /api/observations/<id> ─────────────────────────────────────────────
@observations_bp.route("/<int:obs_id>", methods=["DELETE"])
@jwt_required()
def delete_observation(obs_id):
    user_id = int(get_jwt_identity())
    obs     = db.session.get(Observation, obs_id)
    if not obs:
        return jsonify({"error": "Observación no encontrada"}), 404

    user = db.session.get(User, user_id)
    if obs.user_id != user_id and user.role not in ("admin", "investigador"):
        return jsonify({"error": "Sin permisos para eliminar esta observación"}), 403

    db.session.delete(obs)
    db.session.commit()
    return jsonify({"message": "Observación eliminada"}), 200
