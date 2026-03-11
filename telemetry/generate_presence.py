#!/usr/bin/env python3
"""
Telemetry Presence Widget Generator
----------------------------------

Este script:
1. Lee la ciudad activa desde telemetry/active-city.json
2. Lee la base de ciudades y puntos desde telemetry/cities.json
3. Calcula la hora local de la ciudad
4. Determina una "fase del día" (morning / workday / evening / overnight)
5. Elige una zona y un punto plausible según esa fase
6. Aplica una pequeña variación GPS para simular movimiento
7. Genera un bloque CLI-style
8. Reemplaza automáticamente el bloque entre marcadores en README.md

Pensado para GitHub Actions, pero también puedes correrlo localmente.
"""

import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo


# ============================================================
# RUTAS BASE
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
TELEMETRY_DIR = ROOT / "telemetry"
README_PATH = ROOT / "README.md"

ACTIVE_CITY_FILE = TELEMETRY_DIR / "active-city.json"
CITIES_FILE = TELEMETRY_DIR / "cities.json"

START_MARKER = "<!-- telemetry-presence:start -->"
END_MARKER = "<!-- telemetry-presence:end -->"


# ============================================================
# MODELOS DE DATOS
# ============================================================

@dataclass
class PresenceState:
    city_key: str
    city_label: str
    timezone_name: str
    country: str
    zone_name: str
    location_name: str
    latitude: float
    longitude: float
    altitude_m: int
    gps_accuracy_m: float
    heading_deg: int
    speed_kmh: float
    status: str
    phase: str
    local_time_str: str
    signal: str
    updated_utc: str


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def load_json(path: Path) -> Dict:
    """Carga un JSON y retorna un dict."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def deterministic_rng(*parts: str) -> random.Random:
    """
    Genera un RNG determinista a partir de una semilla estable.
    Esto permite que el widget cambie con el tiempo, pero no de forma caótica
    dentro del mismo intervalo.
    """
    seed_str = "::".join(parts)
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(seed_str))
    return random.Random(seed)


def get_local_datetime(tz_name: str) -> datetime:
    """Obtiene fecha y hora actual en la zona horaria de la ciudad."""
    return datetime.now(ZoneInfo(tz_name))


def get_utc_string() -> str:
    """Retorna timestamp UTC formateado."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def format_local_time(dt: datetime) -> str:
    """Hora local compacta HH:MM."""
    return dt.strftime("%H:%M")


# ============================================================
# FASES DEL DÍA
# ============================================================

def get_phase(local_dt: datetime) -> str:
    """
    Determina la fase del día según la hora local.
    Puedes tunear estos rangos si quieres un comportamiento distinto.
    """
    hour = local_dt.hour

    if 5 <= hour <= 7:
        return "early_morning"
    if 8 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "workday"
    if 18 <= hour <= 21:
        return "evening"
    return "overnight"


def get_phase_profiles(phase: str) -> Dict[str, List[str]]:
    """
    Define qué tipos de lugares son plausibles según la fase.
    Esto hace que el movimiento se vea más orgánico y menos random puro.
    """
    profiles = {
        "early_morning": {
            "allowed_locations": [
                "hotel",
                "residential_sector",
                "cafe",
                "pedestrian_axis",
                "transit_corridor"
            ],
            "statuses": ["stationary", "walking", "in_transit"],
            "signals": ["nominal", "stable"],
            "speed_range": (0.0, 5.2)
        },
        "morning": {
            "allowed_locations": [
                "cafe",
                "office",
                "business_lounge",
                "pedestrian_axis",
                "transit_corridor"
            ],
            "statuses": ["walking", "in_transit", "stationary"],
            "signals": ["stable", "nominal"],
            "speed_range": (0.4, 9.0)
        },
        "workday": {
            "allowed_locations": [
                "office",
                "business_lounge",
                "transit_corridor",
                "pedestrian_axis",
                "cafe"
            ],
            "statuses": ["stationary", "in_transit", "meeting", "walking"],
            "signals": ["stable", "nominal", "strong"],
            "speed_range": (0.0, 12.0)
        },
        "evening": {
            "allowed_locations": [
                "cafe",
                "dining_lounge",
                "hotel",
                "pedestrian_axis",
                "transit_corridor",
                "business_lounge"
            ],
            "statuses": ["stationary", "walking", "in_transit"],
            "signals": ["stable", "nominal"],
            "speed_range": (0.0, 6.5)
        },
        "overnight": {
            "allowed_locations": [
                "hotel",
                "residential_sector",
                "pedestrian_axis"
            ],
            "statuses": ["resting", "stationary", "low_movement"],
            "signals": ["nominal", "stable"],
            "speed_range": (0.0, 1.8)
        }
    }
    return profiles[phase]


# ============================================================
# SELECCIÓN DE ZONAS Y PUNTOS
# ============================================================

def build_time_slot(local_dt: datetime) -> str:
    """
    Agrupa el tiempo en slots de 15 minutos para que el widget cambie
    con cierta continuidad y no en cada segundo.
    """
    minute_bucket = (local_dt.minute // 15) * 15
    return f"{local_dt:%Y-%m-%d %H}:{minute_bucket:02d}"


def choose_zone_and_point(city_key: str, city_data: Dict, phase: str, local_dt: datetime) -> Tuple[Dict, Dict]:
    """
    Elige una zona y un punto de forma determinista dentro del mismo slot horario,
    priorizando puntos compatibles con la fase del día.
    """
    phase_profile = get_phase_profiles(phase)
    allowed_locations = set(phase_profile["allowed_locations"])

    slot = build_time_slot(local_dt)
    rng = deterministic_rng(city_key, phase, slot)

    zones = city_data["zones"]

    # Filtra puntos plausibles por fase
    candidate_pairs = []
    fallback_pairs = []

    for zone in zones:
        for point in zone["points"]:
            pair = (zone, point)
            fallback_pairs.append(pair)
            if point["name"] in allowed_locations:
                candidate_pairs.append(pair)

    # Si no hay candidatos plausibles, cae al pool completo
    pool = candidate_pairs if candidate_pairs else fallback_pairs

    selected_zone, selected_point = rng.choice(pool)
    return selected_zone, selected_point


# ============================================================
# MICROVARIACIÓN GPS
# ============================================================

def apply_coordinate_jitter(lat: float, lon: float, city_key: str, phase: str, local_dt: datetime) -> Tuple[float, float]:
    """
    Aplica una microvariación a las coordenadas para simular movimiento fino.
    La variación es pequeña y estable por slot horario.
    """
    slot = build_time_slot(local_dt)
    rng = deterministic_rng("jitter", city_key, phase, slot)

    # Jitter pequeño: aprox hasta ~80m dependiendo de latitud
    lat_offset = rng.uniform(-0.00055, 0.00055)
    lon_offset = rng.uniform(-0.00055, 0.00055)

    return lat + lat_offset, lon + lon_offset


def choose_heading_speed_status_signal(city_key: str, phase: str, local_dt: datetime) -> Tuple[int, float, str, str, float, int]:
    """
    Elige heading, speed, status, signal, accuracy y altitud simulada.
    Todo determinista por slot.
    """
    slot = build_time_slot(local_dt)
    rng = deterministic_rng("motion", city_key, phase, slot)

    phase_profile = get_phase_profiles(phase)
    speed_min, speed_max = phase_profile["speed_range"]

    heading = rng.randint(0, 359)
    speed = round(rng.uniform(speed_min, speed_max), 1)
    status = rng.choice(phase_profile["statuses"])
    signal = rng.choice(phase_profile["signals"])
    gps_accuracy = round(rng.uniform(3.5, 8.7), 1)
    altitude = rng.randint(8, 160)

    # Ajustes lógicos finos
    if status in ("resting", "stationary"):
        speed = round(rng.uniform(0.0, 0.8), 1)

    if status == "low_movement":
        speed = round(rng.uniform(0.0, 0.4), 1)

    if speed < 0.2:
        heading = 0

    return heading, speed, status, signal, gps_accuracy, altitude


# ============================================================
# RENDER DEL BLOQUE CLI
# ============================================================

def build_cli_block(state: PresenceState) -> str:
    """
    Renderiza el widget como bloque de texto estilo terminal.
    """
    lines = [
        "telemetry presence widget",
        "────────────────────────────────────────────",
        f"profile        : {state.city_key}",
        f"region         : {state.city_label}",
        f"zone           : {state.zone_name}",
        f"location       : {state.location_name}",
        f"latitude       : {state.latitude:.6f}",
        f"longitude      : {state.longitude:.6f}",
        f"altitude       : {state.altitude_m} m",
        f"gps_accuracy   : ±{state.gps_accuracy_m:.1f} m",
        f"heading        : {state.heading_deg}°",
        f"speed          : {state.speed_kmh:.1f} km/h",
        f"status         : {state.status}",
        f"phase          : {state.phase}",
        f"local_time     : {state.local_time_str}",
        f"timezone       : {state.timezone_name}",
        f"signal         : {state.signal}",
        f"updated_utc    : {state.updated_utc}"
    ]
    return "\n".join(lines)


# ============================================================
# README PATCHER
# ============================================================

def update_readme_block(readme_path: Path, cli_block: str) -> None:
    """
    Reemplaza el bloque entre:
    <!-- telemetry-presence:start -->
    <!-- telemetry-presence:end -->
    """
    readme = readme_path.read_text(encoding="utf-8")

    start_index = readme.find(START_MARKER)
    end_index = readme.find(END_MARKER)

    if start_index == -1 or end_index == -1:
        raise RuntimeError(
            "No se encontraron los marcadores de telemetry presence en README.md"
        )

    end_index += len(END_MARKER)

    replacement = (
        f"{START_MARKER}\n"
        "```text\n"
        f"{cli_block}\n"
        "```\n"
        f"{END_MARKER}"
    )

    new_readme = readme[:start_index] + replacement + readme[end_index:]
    readme_path.write_text(new_readme, encoding="utf-8")


# ============================================================
# GENERACIÓN PRINCIPAL
# ============================================================

def generate_presence_state() -> PresenceState:
    """
    Carga configuración, selecciona ciudad/zona/punto, aplica jitter y
    construye el estado final.
    """
    active_data = load_json(ACTIVE_CITY_FILE)
    cities_data = load_json(CITIES_FILE)

    city_key = active_data["active_city"]
    mode = active_data.get("mode", "auto_presence")

    if mode != "auto_presence":
        raise RuntimeError(f"Modo no soportado: {mode}")

    cities = cities_data["cities"]
    if city_key not in cities:
        raise RuntimeError(f"Ciudad activa desconocida: {city_key}")

    city = cities[city_key]
    tz_name = city["timezone"]

    local_dt = get_local_datetime(tz_name)
    phase = get_phase(local_dt)

    zone, point = choose_zone_and_point(city_key, city, phase, local_dt)

    lat, lon = apply_coordinate_jitter(
        point["lat"],
        point["lon"],
        city_key,
        phase,
        local_dt
    )

    heading, speed, status, signal, gps_accuracy, altitude = choose_heading_speed_status_signal(
        city_key,
        phase,
        local_dt
    )

    return PresenceState(
        city_key=city_key,
        city_label=city["label"],
        timezone_name=tz_name,
        country=city["country"],
        zone_name=zone["name"],
        location_name=point["name"],
        latitude=lat,
        longitude=lon,
        altitude_m=altitude,
        gps_accuracy_m=gps_accuracy,
        heading_deg=heading,
        speed_kmh=speed,
        status=status,
        phase=phase,
        local_time_str=format_local_time(local_dt),
        signal=signal,
        updated_utc=get_utc_string()
    )


def main() -> None:
    """
    Entry point principal.
    """
    state = generate_presence_state()
    cli_block = build_cli_block(state)
    update_readme_block(README_PATH, cli_block)
    print(cli_block)


if __name__ == "__main__":
    main()
