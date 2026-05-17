from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from extensions import db
from models import Observation, Species, Zone, User

dashboard_bp = Blueprint("dashboard", __name__)


# ── GET /api/dashboard/stats ──────────────────────────────────────────────────
@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    now  = datetime.now(timezone.utc)
    ago2 = now - timedelta(hours=2)

    total_species      = Species.query.count()
    active_observers   = (User.query
                          .join(Observation, User.id == Observation.user_id)
                          .filter(User.is_active == True)
                          .distinct().count())
    total_observations = Observation.query.count()
    total_zones        = Zone.query.count()

    # Actividad reciente (últimas 5 observaciones)
    recent = (Observation.query
              .order_by(Observation.created_at.desc())
              .limit(5).all())

    recent_activity = []
    for obs in recent:
        diff = now - obs.created_at.replace(tzinfo=timezone.utc)
        if diff.seconds < 3600:
            when = f"Hace {diff.seconds // 60} minutos"
        elif diff.days == 0:
            when = f"Hace {diff.seconds // 3600} horas"
        else:
            when = f"Hace {diff.days} días"

        recent_activity.append({
            "type":        "observation",
            "description": f"{obs.species.common_name} observado en {obs.zone.name}",
            "when":        when,
            "emoji":       obs.species.emoji,
        })

    return jsonify({
        "total_species":      total_species,
        "active_observers":   active_observers,
        "total_observations": total_observations,
        "total_zones":        total_zones,
        "recent_activity":    recent_activity,
    }), 200
