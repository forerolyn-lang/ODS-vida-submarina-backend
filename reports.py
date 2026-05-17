from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from extensions import db
from models import Observation, Species, Zone, User

reports_bp = Blueprint("reports", __name__)


def _date_range(period: str):
    """Devuelve (date_from, date_to) según el período solicitado."""
    now = datetime.now(timezone.utc)
    periods = {
        "week":    timedelta(weeks=1),
        "month":   timedelta(days=30),
        "quarter": timedelta(days=90),
        "year":    timedelta(days=365),
    }
    delta = periods.get(period)
    return (now - delta) if delta else None, now


# ── GET /api/reports/summary ──────────────────────────────────────────────────
@reports_bp.route("/summary", methods=["GET"])
@jwt_required()
def summary():
    period   = request.args.get("period", "month")
    from_dt, to_dt = _date_range(period)

    q = Observation.query
    if from_dt:
        q = q.filter(Observation.observed_at >= from_dt,
                     Observation.observed_at <= to_dt)

    total = q.count()

    # Calcular crecimiento vs período anterior
    prev_q = Observation.query
    if from_dt:
        delta    = to_dt - from_dt
        prev_end = from_dt
        prev_st  = prev_end - delta
        prev_q   = prev_q.filter(Observation.observed_at >= prev_st,
                                  Observation.observed_at <= prev_end)

    prev_total = prev_q.count()
    growth = (
        round(((total - prev_total) / prev_total) * 100, 1)
        if prev_total > 0 else 0
    )

    return jsonify({
        "period":      period,
        "total":       total,
        "growth_pct":  growth,
        "prev_total":  prev_total,
    }), 200


# ── GET /api/reports/by-species ───────────────────────────────────────────────
@reports_bp.route("/by-species", methods=["GET"])
@jwt_required()
def by_species():
    period = request.args.get("period", "month")
    from_dt, to_dt = _date_range(period)

    q = (db.session.query(
            Species.id,
            Species.common_name,
            Species.emoji,
            func.count(Observation.id).label("count")
         )
         .join(Observation, Observation.species_id == Species.id))

    if from_dt:
        q = q.filter(Observation.observed_at >= from_dt,
                     Observation.observed_at <= to_dt)

    rows = q.group_by(Species.id).order_by(func.count(Observation.id).desc()).all()

    return jsonify([
        {"id": r.id, "name": r.common_name, "emoji": r.emoji, "count": r.count}
        for r in rows
    ]), 200


# ── GET /api/reports/by-zone ──────────────────────────────────────────────────
@reports_bp.route("/by-zone", methods=["GET"])
@jwt_required()
def by_zone():
    period = request.args.get("period", "month")
    from_dt, to_dt = _date_range(period)

    q = (db.session.query(
            Zone.id,
            Zone.name,
            Zone.emoji,
            func.count(Observation.id).label("count")
         )
         .join(Observation, Observation.zone_id == Zone.id))

    if from_dt:
        q = q.filter(Observation.observed_at >= from_dt,
                     Observation.observed_at <= to_dt)

    rows = q.group_by(Zone.id).order_by(func.count(Observation.id).desc()).all()
    total = sum(r.count for r in rows) or 1

    return jsonify([
        {
            "id":      r.id,
            "name":    r.name,
            "emoji":   r.emoji,
            "count":   r.count,
            "pct":     round((r.count / total) * 100, 1),
        }
        for r in rows
    ]), 200


# ── GET /api/reports/monthly-trends ──────────────────────────────────────────
@reports_bp.route("/monthly-trends", methods=["GET"])
@jwt_required()
def monthly_trends():
    rows = (db.session.query(
                func.strftime("%Y-%m", Observation.observed_at).label("month"),
                func.count(Observation.id).label("count")
            )
            .group_by("month")
            .order_by("month")
            .limit(12).all())

    return jsonify([{"month": r.month, "count": r.count} for r in rows]), 200


# ── GET /api/reports/top-observers ───────────────────────────────────────────
@reports_bp.route("/top-observers", methods=["GET"])
@jwt_required()
def top_observers():
    period = request.args.get("period", "month")
    from_dt, to_dt = _date_range(period)
    limit  = int(request.args.get("limit", 10))

    q = (db.session.query(
            User.id,
            User.full_name,
            func.count(Observation.id).label("count")
         )
         .join(Observation, Observation.user_id == User.id))

    if from_dt:
        q = q.filter(Observation.observed_at >= from_dt,
                     Observation.observed_at <= to_dt)

    rows = q.group_by(User.id).order_by(func.count(Observation.id).desc()).limit(limit).all()

    return jsonify([
        {"id": r.id, "full_name": r.full_name, "count": r.count}
        for r in rows
    ]), 200


# ── GET /api/reports/export ───────────────────────────────────────────────────
@reports_bp.route("/export", methods=["GET"])
@jwt_required()
def export_csv():
    """Exporta observaciones como CSV."""
    import csv
    import io

    period = request.args.get("period", "month")
    from_dt, to_dt = _date_range(period)

    q = Observation.query
    if from_dt:
        q = q.filter(Observation.observed_at >= from_dt,
                     Observation.observed_at <= to_dt)

    observations = q.order_by(Observation.observed_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Fecha", "Especie", "Zona", "Observador",
        "Cantidad", "Comportamiento", "Temperatura (°C)",
        "Salinidad (PSU)", "Visibilidad", "Latitud", "Longitud", "Notas"
    ])
    for o in observations:
        writer.writerow([
            o.id,
            o.observed_at.strftime("%Y-%m-%d %H:%M"),
            o.species.common_name if o.species else "",
            o.zone.name           if o.zone    else "",
            o.observer.full_name  if o.observer else "",
            o.quantity,
            o.behavior      or "",
            o.temperature_c or "",
            o.salinity_psu  or "",
            o.visibility    or "",
            o.latitude      or "",
            o.longitude     or "",
            o.notes         or "",
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Type"]        = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="oceanlearn_{period}.csv"'
    return response
