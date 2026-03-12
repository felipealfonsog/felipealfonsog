#!/usr/bin/env python3
"""
Telemetry Presence Widget Generator
----------------------------------

Este script:
1. Lee la ciudad activa desde telemetry/active-city.json
2. Lee la base de ciudades y puntos desde telemetry/cities.json
3. Calcula la hora local de la ciudad
4. Determina una fase del día
5. Elige una zona y un punto plausible según esa fase
6. Aplica una pequeña variación GPS para simular movimiento
7. Genera un bloque CLI-style
8. Reemplaza automáticamente el bloque entre marcadores en README.md
9. Si falla la generación, reutiliza el último snapshot válido
"""

import json
import random
from dataclasses import asdict, dataclass
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
LAST_PRESENCE_FILE = TELEMETRY_DIR / "last_presence.json"

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
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def deterministic_rng(*parts: str) -> random.Random:
    seed_str = "::".join(parts)
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(seed_str))
    return random.Random(seed)


def get_local_datetime(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def get_utc_string() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def format_local_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def state_to_dict(state: PresenceState) -> Dict:
    return asdict(state)


def dict_to_state(data: Dict) -> PresenceState:
    return PresenceState(**data)


def save_last_presence(state: PresenceState) -> None:
    save_json(LAST_PRESENCE_FILE, state_to_dict(state))


def load_last_presence() -> PresenceState:
    if not LAST_PRESENCE_FILE.exists():
        raise RuntimeError("No existe cache de last_presence.json")
    return dict_to_state(load_json(LAST_PRESENCE_FILE))


# ============================================================
# FASES DEL DÍA
# ============================================================

def get_phase(local_dt: datetime) -> str:
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
    profiles = {
        "early_morning": {
            "allowed_locations": [
                "hotel",
                "residential_sector",
                "urban_sector",
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
                "urban_sector",
                "business_lounge",
                "pedestrian_axis",
                "transit_corridor",
                "residential_sector"
            ],
            "statuses": ["walking", "in_transit", "stationary"],
            "signals": ["stable", "nominal"],
            "speed_range": (0.4, 9.0)
        },
        "workday": {
            "allowed_locations": [
                "office",
                "urban_sector",
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
                "urban_sector",
                "residential_sector",
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
                "urban_sector",
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
    minute_bucket = (local_dt.minute // 15) * 15
    return f"{local_dt:%Y-%m-%d %H}:{minute_bucket:02d}"


def choose_zone_and_point(city_key: str, city_data: Dict, phase: str, local_dt: datetime) -> Tuple[Dict, Dict]:
    phase_profile = get_phase_profiles(phase)
    allowed_locations = set(phase_profile["allowed_locations"])

    slot = build_time_slot(local_dt)
    rng = deterministic_rng(city_key, phase, slot)

    candidate_pairs = []
    fallback_pairs = []

    for zone in city_data["zones"]:
        for point in zone["points"]:
            pair = (zone, point)
            fallback_pairs.append(pair)
            if point["name"] in allowed_locations:
                candidate_pairs.append(pair)

    pool = candidate_pairs if candidate_pairs else fallback_pairs
    selected_zone, selected_point = rng.choice(pool)
    return selected_zone, selected_point


# ============================================================
# MICROVARIACIÓN GPS
# ============================================================

def apply_coordinate_jitter(lat: float, lon: float, city_key: str, phase: str, local_dt: datetime) -> Tuple[float, float]:
    slot = build_time_slot(local_dt)
    rng = deterministic_rng("jitter", city_key, phase, slot)

    lat_offset = rng.uniform(-0.00055, 0.00055)
    lon_offset = rng.uniform(-0.00055, 0.00055)

    return lat + lat_offset, lon + lon_offset


def choose_heading_speed_status_signal(city_key: str, phase: str, local_dt: datetime) -> Tuple[int, float, str, str, float, int]:
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

def build_cli_block(state: PresenceState, used_fallback: bool = False) -> str:
    lines = [
        "Presence Vector Telemetry — Remote Node",
        "────────────────────────────────────────────",
#        f"profile        : {state.city_key}",
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

    if used_fallback:
        lines.append("cache_state    : retained_last_snapshot")

    return "\n".join(lines)


# ============================================================
# README PATCHER
# ============================================================

def update_readme_block(readme_path: Path, cli_block: str) -> None:
    readme = readme_path.read_text(encoding="utf-8")

    start_index = readme.find(START_MARKER)
    end_index = readme.find(END_MARKER)

    if start_index == -1 or end_index == -1:
        raise RuntimeError("No se encontraron los marcadores de telemetry presence en README.md")

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

    lat, lon = apply_coordinate_jitter(point["lat"], point["lon"], city_key, phase, local_dt)

    heading, speed, status, signal, gps_accuracy, altitude = choose_heading_speed_status_signal(
        city_key, phase, local_dt
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
    used_fallback = False

    try:
        state = generate_presence_state()
        save_last_presence(state)
    except Exception as e:
        print(f"[warn] failed to generate fresh telemetry: {e}")

        try:
            state = load_last_presence()
            used_fallback = True
            print("[info] using cached last_presence.json")
        except Exception as cache_error:
            raise RuntimeError(
                f"No se pudo generar estado nuevo ni cargar cache previa: {cache_error}"
            ) from e

    cli_block = build_cli_block(state, used_fallback=used_fallback)
    update_readme_block(README_PATH, cli_block)
    print(cli_block)


if __name__ == "__main__":
    main()
