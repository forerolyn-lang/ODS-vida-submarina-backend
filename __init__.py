from datetime import datetime, timezone
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


# ─────────────────────────────────────────────────────────────────────────────
# USUARIO
# ─────────────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(
        db.Enum("investigador", "estudiante", "educador", "entusiasta", "admin",
                name="user_role"),
        default="entusiasta", nullable=False
    )
    is_active  = db.Column(db.Boolean, default=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    observations = db.relationship("Observation", backref="observer", lazy="dynamic")

    def set_password(self, raw_password: str):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password, raw_password)

    def to_dict(self, include_stats=False):
        data = {
            "id":         self.id,
            "full_name":  self.full_name,
            "email":      self.email,
            "role":       self.role,
            "is_active":  self.is_active,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat(),
        }
        if include_stats:
            data["total_observations"] = self.observations.count()
        return data

    def __repr__(self):
        return f"<User {self.email}>"


# ─────────────────────────────────────────────────────────────────────────────
# ESPECIE MARINA
# ─────────────────────────────────────────────────────────────────────────────
class Species(db.Model):
    __tablename__ = "species"

    id              = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(200), unique=True, nullable=False)
    common_name     = db.Column(db.String(200), nullable=False)
    description     = db.Column(db.Text, nullable=True)
    status          = db.Column(
        db.Enum("activo", "en_peligro", "vulnerable", "extinto", name="species_status"),
        default="activo", nullable=False
    )
    emoji           = db.Column(db.String(10), default="🐟")
    image_url       = db.Column(db.String(500), nullable=True)
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    observations = db.relationship("Observation", backref="species", lazy="dynamic")

    def to_dict(self, include_stats=False):
        data = {
            "id":              self.id,
            "scientific_name": self.scientific_name,
            "common_name":     self.common_name,
            "description":     self.description,
            "status":          self.status,
            "emoji":           self.emoji,
            "image_url":       self.image_url,
            "created_at":      self.created_at.isoformat(),
        }
        if include_stats:
            data["total_observations"] = self.observations.count()
        return data

    def __repr__(self):
        return f"<Species {self.scientific_name}>"


# ─────────────────────────────────────────────────────────────────────────────
# ZONA DE MONITOREO
# ─────────────────────────────────────────────────────────────────────────────
class Zone(db.Model):
    __tablename__ = "zones"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude    = db.Column(db.Float, nullable=False)
    longitude   = db.Column(db.Float, nullable=False)
    status      = db.Column(
        db.Enum("monitoreada", "revision_pendiente", "inactiva", name="zone_status"),
        default="monitoreada", nullable=False
    )
    emoji       = db.Column(db.String(10), default="🌊")
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    observations = db.relationship("Observation", backref="zone", lazy="dynamic")

    def to_dict(self, include_stats=False):
        data = {
            "id":          self.id,
            "name":        self.name,
            "description": self.description,
            "latitude":    self.latitude,
            "longitude":   self.longitude,
            "status":      self.status,
            "emoji":       self.emoji,
            "created_at":  self.created_at.isoformat(),
        }
        if include_stats:
            data["total_observations"] = self.observations.count()
        return data

    def __repr__(self):
        return f"<Zone {self.name}>"


# ─────────────────────────────────────────────────────────────────────────────
# OBSERVACIÓN
# ─────────────────────────────────────────────────────────────────────────────
class Observation(db.Model):
    __tablename__ = "observations"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"),   nullable=False)
    species_id  = db.Column(db.Integer, db.ForeignKey("species.id"), nullable=False)
    zone_id     = db.Column(db.Integer, db.ForeignKey("zones.id"),   nullable=False)

    # Datos de la observación
    quantity    = db.Column(db.Integer, nullable=False, default=1)
    behavior    = db.Column(
        db.Enum("alimentandose", "en_reposo", "nadando", "cazando",
                "reproduciendose", "otro", name="behavior_type"),
        nullable=True
    )
    notes       = db.Column(db.Text, nullable=True)
    photo_url   = db.Column(db.String(500), nullable=True)

    # Ubicación exacta (dentro de la zona)
    latitude    = db.Column(db.Float, nullable=True)
    longitude   = db.Column(db.Float, nullable=True)
    depth_m     = db.Column(db.Float, nullable=True)

    # Condiciones ambientales
    temperature_c = db.Column(db.Float, nullable=True)
    salinity_psu  = db.Column(db.Float, nullable=True)
    visibility    = db.Column(
        db.Enum("excelente", "buena", "moderada", "pobre", name="visibility_type"),
        nullable=True
    )
    water_state   = db.Column(
        db.Enum("calmada", "moderada", "agitada", name="water_state_type"),
        nullable=True
    )

    observed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "species_id":     self.species_id,
            "zone_id":        self.zone_id,
            "quantity":       self.quantity,
            "behavior":       self.behavior,
            "notes":          self.notes,
            "photo_url":      self.photo_url,
            "latitude":       self.latitude,
            "longitude":      self.longitude,
            "depth_m":        self.depth_m,
            "temperature_c":  self.temperature_c,
            "salinity_psu":   self.salinity_psu,
            "visibility":     self.visibility,
            "water_state":    self.water_state,
            "observed_at":    self.observed_at.isoformat(),
            "created_at":     self.created_at.isoformat(),
            # Datos relacionados (si se cargaron)
            "observer_name":  self.observer.full_name if self.observer else None,
            "species_name":   self.species.common_name if self.species else None,
            "zone_name":      self.zone.name if self.zone else None,
        }

    def __repr__(self):
        return f"<Observation id={self.id}>"
