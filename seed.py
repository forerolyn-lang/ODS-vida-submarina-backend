"""
Script para poblar la base de datos con datos iniciales.
Ejecutar una sola vez: python seed.py
"""
from app import create_app
from extensions import db
from models import User, Species, Zone, Observation
from datetime import datetime, timezone, timedelta
import random

app = create_app()

SPECIES_DATA = [
    ("Amphiprion ocellaris",         "Pez Payaso Común",        "activo",     "🐠"),
    ("Carcharodon carcharias",       "Tiburón Blanco",          "vulnerable", "🦈"),
    ("Octopus vulgaris",             "Pulpo Común",             "activo",     "🐙"),
    ("Chelonia mydas",               "Tortuga Verde",           "en_peligro", "🐢"),
    ("Hippocampus hippocampus",      "Caballito de Mar",        "vulnerable", "🐡"),
    ("Manta birostris",              "Manta Raya Gigante",      "vulnerable", "🐟"),
    ("Tursiops truncatus",           "Delfín Nariz de Botella", "activo",     "🐬"),
    ("Physeter macrocephalus",       "Cachalote",               "vulnerable", "🐳"),
    ("Pterois volitans",             "Pez León",                "activo",     "🐡"),
    ("Panulirus argus",              "Langosta del Caribe",     "activo",     "🦞"),
]

ZONES_DATA = [
    ("Zona A - Arrecife Norte",   18.4655, -69.9312, "monitoreada",        "🌊"),
    ("Zona B - Bahía Sur",        18.2333, -70.5167, "monitoreada",        "🏝️"),
    ("Zona C - Costa Este",       19.1234, -69.3456, "revision_pendiente", "🌅"),
    ("Zona D - Laguna Central",   18.7890, -70.1234, "monitoreada",        "💧"),
    ("Zona E - Profundidades",    17.9988, -69.5678, "inactiva",           "🌑"),
]

USERS_DATA = [
    ("Admin Sistema",   "admin@oceanlearn.com",        "admin123",   "admin"),
    ("María Rodríguez", "maria@oceanlearn.com",        "pass1234",   "investigador"),
    ("Juan López",      "juan@oceanlearn.com",         "pass1234",   "estudiante"),
    ("Ana Silva",       "ana@oceanlearn.com",          "pass1234",   "educador"),
    ("Carlos Méndez",   "carlos@oceanlearn.com",       "pass1234",   "entusiasta"),
]

BEHAVIORS = ["alimentandose", "en_reposo", "nadando", "cazando", "reproduciendose", "otro"]
VISIBILITIES = ["excelente", "buena", "moderada", "pobre"]
WATER_STATES = ["calmada", "moderada", "agitada"]


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✔ Tablas creadas")

        # Usuarios
        users = []
        for full_name, email, password, role in USERS_DATA:
            u = User(full_name=full_name, email=email, role=role)
            u.set_password(password)
            db.session.add(u)
            users.append(u)
        db.session.commit()
        print(f"✔ {len(users)} usuarios creados")

        # Especies
        species_list = []
        for sci, com, status, emoji in SPECIES_DATA:
            sp = Species(scientific_name=sci, common_name=com, status=status, emoji=emoji)
            db.session.add(sp)
            species_list.append(sp)
        db.session.commit()
        print(f"✔ {len(species_list)} especies creadas")

        # Zonas
        zone_list = []
        for name, lat, lng, status, emoji in ZONES_DATA:
            z = Zone(name=name, latitude=lat, longitude=lng, status=status, emoji=emoji)
            db.session.add(z)
            zone_list.append(z)
        db.session.commit()
        print(f"✔ {len(zone_list)} zonas creadas")

        # Observaciones de ejemplo (últimos 60 días)
        obs_count = 0
        now = datetime.now(timezone.utc)
        for i in range(120):
            days_ago   = random.randint(0, 60)
            obs_date   = now - timedelta(days=days_ago, hours=random.randint(0, 23))
            user       = random.choice(users[1:])   # excluir admin
            sp         = random.choice(species_list)
            zone       = random.choice([z for z in zone_list if z.status == "monitoreada"])

            obs = Observation(
                user_id       = user.id,
                species_id    = sp.id,
                zone_id       = zone.id,
                quantity      = random.randint(1, 15),
                behavior      = random.choice(BEHAVIORS),
                notes         = "Observación generada automáticamente" if i % 3 == 0 else None,
                latitude      = zone.latitude  + random.uniform(-0.01, 0.01),
                longitude     = zone.longitude + random.uniform(-0.01, 0.01),
                depth_m       = random.uniform(1, 40),
                temperature_c = random.uniform(22, 30),
                salinity_psu  = random.uniform(30, 38),
                visibility    = random.choice(VISIBILITIES),
                water_state   = random.choice(WATER_STATES),
                observed_at   = obs_date,
            )
            db.session.add(obs)
            obs_count += 1

        db.session.commit()
        print(f"✔ {obs_count} observaciones creadas")
        print("\n✅ Base de datos inicializada correctamente")
        print("\n🔑 Credenciales de acceso:")
        for full_name, email, password, role in USERS_DATA:
            print(f"   {role:15s} → {email}  /  {password}")


if __name__ == "__main__":
    seed()
