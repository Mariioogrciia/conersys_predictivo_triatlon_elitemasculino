#!/usr/bin/env python3
"""
Build a comprehensive predictive dataset for Elite Masculine Triathlon.
Each row = one athlete in one race, with ~80+ features.
"""
import json
import os
import csv
import re
import math
from datetime import datetime, timedelta
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELITE_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'elite_masculina_triatlon')
OUTPUT_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'dataset_predictivo.csv')

WEATHER_CACHE_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'clima_carreras.json')
weather_cache = {}
try:
    with open(WEATHER_CACHE_PATH, 'r', encoding='utf-8') as f:
        weather_cache = json.load(f)
except Exception:
    print("Warning: clima_carreras.json not found. Weather will be empty.")

# ============================================================================
# PASO 1: GEOLOCALIZACIÓN DE CIUDADES
# ============================================================================
# Static lookup: city -> (lat, lng, altitude_m, near_coast, climate_type)
GEO_DATA = {
    "Águilas":              (37.4049, -1.5832,  23, True,  "mediterraneo"),
    "Roquetas de Mar":      (36.7643, -2.6147,   5, True,  "mediterraneo"),
    "Albacete":             (38.9942, -1.8585, 686, False, "continental"),
    "Ciudad Real":          (38.9848, -3.9274, 628, False, "continental"),
    "Centro Niemeyer":      (43.5573, -5.9247,  10, True,  "atlantico"),  # Avilés
    "Avilés":               (43.5573, -5.9247,  10, True,  "atlantico"),
    "La Nucía":             (38.6189, -0.1261, 200, False, "mediterraneo"),
    "Soria":                (41.7636, -2.4649, 1063, False, "continental"),
    "Cáceres":              (39.4753, -6.3724, 459, False, "continental"),
    "Banyoles":             (42.1189, 2.7644,  172, False, "mediterraneo"),
    "Pamplona":             (42.8125, -1.6458, 449, False, "continental"),
    "Alcobendas":           (40.5334, -3.6421, 670, False, "continental"),
    "Oropesa del Mar/Orpesa": (40.0967, 0.1358, 5, True,  "mediterraneo"),
    "Almazán":              (41.4862, -2.5327, 950, False, "continental"),
    "Madrid":               (40.4168, -3.7038, 667, False, "continental"),
    "Calahorra":            (42.3050, -1.9653, 358, False, "continental"),
    "Peníscola/Peñíscola":  (40.3577, 0.4076,   5, True,  "mediterraneo"),
    "Peñíscola":            (40.3577, 0.4076,   5, True,  "mediterraneo"),
    "Cartagena - Murcia":   (37.6257, -0.9966,  10, True,  "mediterraneo"),
    "Cartagena":            (37.6257, -0.9966,  10, True,  "mediterraneo"),
    "Vitoria-Gasteiz":      (42.8467, -2.6716, 525, False, "atlantico"),
    "Pontevedra":           (42.4311, -8.6443,  20, True,  "atlantico"),
    "Coruña, A":            (43.3623, -8.4115,  10, True,  "atlantico"),
    "A Coruña":             (43.3623, -8.4115,  10, True,  "atlantico"),
    "Mérida":               (38.9160, -6.3435, 217, False, "continental"),
    "Punta Umbría":         (37.1768, -6.9595,   5, True,  "atlantico"),
    "Narón":                (43.5233, -8.1541,  15, True,  "atlantico"),
    "Tarazona":             (41.9047, -1.7260, 480, False, "continental"),
    "Fuente Álamo":         (37.7147, -1.1713, 155, False, "mediterraneo"),
    "Fuente Álamo de Murcia": (37.7147, -1.1713, 155, False, "mediterraneo"),
    "Calasparra":           (38.2294, -1.6978, 340, False, "mediterraneo"),
    "Berlanga de Duero":    (41.4583, -2.8583, 938, False, "continental"),
    "Platja d'Aro":         (41.8172, 3.0672,   5, True,  "mediterraneo"),
    "Ansó":                 (42.7578, -0.8289, 860, False, "montaña"),
    "Reinosa":              (43.0017, -4.1375, 851, False, "montaña"),
    "Orihuela":             (38.0849, -0.9441,  24, False, "mediterraneo"),
    "Playas de Orihuela":   (37.9413, -0.7528,   5, True,  "mediterraneo"),
    "Sevilla":              (37.3886, -5.9823,   7, False, "mediterraneo"),
    "Ibiza":                (38.9067, 1.4206,   10, True,  "mediterraneo"),
    "Mallorca":             (39.6953, 3.0176,  20, True,  "mediterraneo"),
    "Peguera":              (39.5386, 2.4353,  20, True,  "mediterraneo"),
    "Valencia":             (39.4699, -0.3763,  15, True,  "mediterraneo"),
    "Salou":                (41.0764, 1.1416,   5, True,  "mediterraneo"),
    "Xilxes":               (39.7611, -0.2122,   5, True,  "mediterraneo"),
    "TriXilxes":            (39.7611, -0.2122,   5, True,  "mediterraneo"),
    "Catalunya":            (41.5912, 1.5209, 250, False, "mediterraneo"),
    "Valladolid":           (41.6520, -4.7286, 698, False, "continental"),
    "Huesca":               (42.1362, -0.4087, 488, False, "continental"),
    "Huelva":               (37.2614, -6.9447,  54, True,  "atlantico"),
    "Girona":               (41.9794, 2.8214,  75, False, "mediterraneo"),
    "Navarra":              (42.8125, -1.6458, 449, False, "continental"),
    "Santa Eulària des Riu":(38.9833, 1.5333,  10, True,  "mediterraneo"),
    "Jerez de los Caballeros":(38.3214, -6.7722, 490, False, "continental"),
    "Alcudia":              (39.8530, 3.1194,   5, True,  "mediterraneo"),
    "Zaragoza":             (41.6488, -0.8891, 199, False, "continental"),
    "Illes Balears":        (39.5700, 2.6502,  20, True,  "mediterraneo"),
    "Aguilar de Campoo":    (42.7944, -4.2567, 895, False, "montaña"),
}

def get_geo(city):
    """Get geolocation data for a city. Try exact match first, then fuzzy."""
    if not city:
        return (None, None, None, None, None)
    
    # Exact match
    if city in GEO_DATA:
        return GEO_DATA[city]
    
    # Fuzzy match: check if any key is contained in the city name or vice versa
    city_lower = city.lower()
    for key, data in GEO_DATA.items():
        if key.lower() in city_lower or city_lower in key.lower():
            return data
    
    # Check for known substrings
    for keyword in ["Águilas", "Roquetas", "Albacete", "Ciudad Real", "Nucía", "Soria",
                    "Cáceres", "Banyoles", "Pamplona", "Alcobendas", "Oropesa", "Almazán",
                    "Madrid", "Calahorra", "Peñíscola", "Cartagena", "Vitoria", "Pontevedra",
                    "Coruña", "Mérida", "Punta Umbría", "Narón", "Tarazona", "Fuente Álamo",
                    "Calasparra", "Berlanga", "Platja", "Ansó", "Reinosa", "Orihuela",
                    "Sevilla", "Ibiza", "Mallorca", "Peguera", "Valencia", "Salou", "Xilxes"]:
        if keyword.lower() in city_lower:
            return GEO_DATA.get(keyword, (None, None, None, None, None))
    
    return (None, None, None, None, None)


# ============================================================================
# PASO 2: UTILIDADES DE PARSEO
# ============================================================================

def parse_time_to_seconds(time_str):
    """Convert time string like '1:06:37', '23:01', '0:50' to seconds."""
    if not time_str or time_str.strip() == '':
        return None
    
    time_str = time_str.strip()
    parts = time_str.split(':')
    
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:
            return int(parts[0])
    except (ValueError, IndexError):
        return None
    return None


def parse_date(date_str, fmt='%d/%m/%Y'):
    """Parse a date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), fmt)
    except ValueError:
        # Try alternative format MM/DD/YYYY
        try:
            return datetime.strptime(date_str.strip(), '%m/%d/%Y')
        except ValueError:
            return None


def parse_date_sort(date_str):
    """Parse ChdDateSort format YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d')
    except ValueError:
        return None


def safe_int(val):
    """Safely convert to int."""
    if val is None or val == '':
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def safe_float(val):
    """Safely convert to float."""
    if val is None or val == '':
        return None
    try:
        return float(str(val).replace(',', '.'))
    except (ValueError, TypeError):
        return None


def detect_race_type(chd_name, ev_des):
    """Detect race type from championship name and event description."""
    text = (chd_name or '').lower() + ' ' + (ev_des or '').lower()
    
    if 'larga distancia' in text or 'ld' in text.split():
        return 'larga_distancia'
    if 'media distancia' in text or 'md' in text.split() or 'half' in text or 't100' in text or '113' in text:
        return 'media_distancia'
    if 'cros' in text or 'cross' in text:
        return 'cross'
    if 'invierno' in text:
        return 'invierno'
    if 'olímpic' in text or 'olimpic' in text:
        return 'olimpico'
    if 'sprint' in text or 'supersprint' in text or 'super sprint' in text:
        return 'sprint'
    if 'relevo' in text or 'parejas' in text:
        return 'relevos'
    if 'aquabike' in text:
        return 'aquabike'
    return 'otro'


def is_relay(result):
    """Check if a result is a relay/team event."""
    ev_des = (result.get('EvDes', '') or '').lower()
    chd_name = (result.get('ChdName', '') or '').lower()
    name = result.get('Name', '') or ''
    
    if 'relevo' in ev_des or 'relevo' in chd_name or 'parejas' in ev_des:
        return True
    if '/' in name and name.count('/') >= 2:  # Team names separated by /
        return True
    return False


def is_elite_triathlon(result):
    """Check if a result is elite masculine triathlon."""
    ev_des = (result.get('EvDes', '') or '').upper()
    is_elite = ('ELITE' in ev_des or 'ÉLITE' in ev_des) and 'MASCULIN' in ev_des
    
    if not is_elite:
        return False
    
    # Check for triathlon segments
    detail_types = {d.get('Type', '') for d in result.get('ResDetail', [])}
    is_tri_segments = 'SW' in detail_types and 'CY' in detail_types and 'RU' in detail_types
    
    chd_name = (result.get('ChdName', '') or '').lower()
    is_tri_name = any(w in chd_name for w in ['triatlón', 'triatlon', 'triathlon'])
    
    return is_tri_segments or is_tri_name


# ============================================================================
# PASO 3: CARGAR Y PROCESAR TODOS LOS ATLETAS
# ============================================================================

print("=" * 70)
print("BUILDING PREDICTIVE DATASET - ELITE MASCULINE TRIATHLON")
print("=" * 70)

# Load all athlete data
print("\n[1/5] Loading athlete data...")
athletes = {}  # license -> full data
athlete_all_results = defaultdict(list)  # license -> list of (date, result) for ALL results

json_files = [f for f in os.listdir(ELITE_DIR) if f.endswith('.json')]
for filename in json_files:
    filepath = os.path.join(ELITE_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        continue
    
    license_id = filename.replace('.json', '')
    athletes[license_id] = data
    
    # Collect ALL results (not just elite) for historical features
    for result in data.get('results', []):
        race_date = parse_date_sort(result.get('ChdDateSort'))
        if race_date:
            athlete_all_results[license_id].append((race_date, result))

# Sort all results by date
for lid in athlete_all_results:
    athlete_all_results[lid].sort(key=lambda x: x[0])

print(f"  Loaded {len(athletes)} athletes")

# ============================================================================
# PASO 4: IDENTIFY ALL ELITE TRIATHLON RACES AND BUILD RACE PARTICIPANT INDEX
# ============================================================================

print("\n[2/5] Identifying elite triathlon races...")

# Collect all individual elite triathlon results (exclude relays)
all_rows = []  # (athlete_license, race_date, result_dict, basic_info)
race_participants = defaultdict(list)  # race_key -> [(license, position, time)]

missing_cities = set()

for license_id, data in athletes.items():
    basic = data.get('athleteBasicInfo', {})
    
    for result in data.get('results', []):
        if not is_elite_triathlon(result):
            continue
        
        # Skip relays for individual prediction
        if is_relay(result):
            continue
        
        race_date = parse_date_sort(result.get('ChdDateSort'))
        if not race_date:
            continue
        
        all_rows.append((license_id, race_date, result, basic))
        
        # Build race participant index
        race_key = f"{result.get('ChId')}_{result.get('EvDes')}_{result.get('PhDes', '')}"
        pos = safe_int(result.get('Rk'))
        time_s = parse_time_to_seconds(result.get('Res'))
        race_participants[race_key].append((license_id, pos, time_s))
        
        # Track missing cities
        city = result.get('ChdCity', '')
        geo = get_geo(city)
        if geo[0] is None and city:
            missing_cities.add(city)

print(f"  Found {len(all_rows)} individual elite triathlon results")
print(f"  Across {len(race_participants)} unique race events")
if missing_cities:
    print(f"  Missing geo for: {missing_cities}")

# ============================================================================
# PASO 5: BUILD FEATURES FOR EACH ROW
# ============================================================================

print("\n[3/5] Building features for each row...")

dataset = []

for idx, (license_id, race_date, result, basic) in enumerate(all_rows):
    if (idx + 1) % 500 == 0:
        print(f"  Processing row {idx+1}/{len(all_rows)}...")
    
    row = {}
    rankings = basic.get('rankings', {})
    
    # --- ATHLETE FEATURES ---
    birth_date = parse_date(basic.get('birthDate'))
    age_at_race = None
    if birth_date and race_date:
        age_at_race = (race_date - birth_date).days / 365.25
    
    row['athlete_id'] = license_id
    row['athlete_name'] = basic.get('fullName', '')
    row['athlete_age_at_race'] = round(age_at_race, 1) if age_at_race else ''
    row['athlete_club'] = basic.get('clubName', '')
    row['athlete_federation'] = basic.get('autonomy', '')
    row['athlete_ranking_triatlon'] = rankings.get('triatlon', '') or 9999
    row['athlete_ranking_wr'] = rankings.get('wr', '') or 9999
    row['athlete_has_wt_id'] = 1 if basic.get('wtId') else 0
    
    # --- RACE FEATURES ---
    city = result.get('ChdCity', '')
    geo = get_geo(city)
    race_type = detect_race_type(result.get('ChdName'), result.get('EvDes'))
    
    row['race_id'] = result.get('ChId', '')
    row['race_name'] = result.get('ChdName', '')
    row['race_city'] = city
    row['race_date'] = result.get('ChdDateSort', '')
    row['race_season'] = result.get('ChSeason', '')
    row['race_event_desc'] = result.get('EvDes', '')
    row['race_phase'] = (result.get('PhDes', '') or '').strip()
    
    # Real Weather Logic
    t_raw = safe_float(result.get('Temperature'))
    h_raw = safe_float(result.get('Humidity'))
    
    if t_raw is None or h_raw is None:
        cached = weather_cache.get(str(row['race_id']), {})
        if t_raw is None:
            t_raw = cached.get('temperature', '')
        if h_raw is None:
            h_raw = cached.get('humidity', '')
            
    row['race_temperature'] = t_raw if t_raw != '' and t_raw is None else t_raw
    row['race_humidity'] = h_raw if h_raw != '' and h_raw is None else h_raw
    
    row['race_lat'] = geo[0] or ''
    row['race_lng'] = geo[1] or ''
    row['race_altitude_m'] = geo[2] or ''
    row['race_near_coast'] = 1 if geo[3] else (0 if geo[3] is not None else '')
    row['race_climate_type'] = geo[4] or ''
    row['race_month'] = race_date.month if race_date else ''
    row['race_day_of_week'] = race_date.weekday() if race_date else ''  # 0=Monday
    row['race_type'] = race_type
    
    # --- RESULT FEATURES (TARGET) ---
    irm = (result.get('IRM', '') or '').strip().upper()
    finish_pos = safe_int(result.get('Rk'))
    finish_time_s = parse_time_to_seconds(result.get('Res'))
    
    row['finish_position'] = finish_pos if finish_pos else ''
    row['finish_time_seconds'] = finish_time_s if finish_time_s else ''
    row['is_dnf'] = 1 if irm == 'DNF' else 0
    row['is_dns'] = 1 if irm == 'DNS' else 0
    row['is_dsq'] = 1 if irm == 'DSQ' else 0
    
    # --- SPLIT FEATURES ---
    details = result.get('ResDetail', [])
    splits = {}
    for d in details:
        dtype = d.get('Type', '')
        desc = (d.get('Description', '') or '').lower()
        # Only take first occurrence of each type (ignore relay rounds R2, R3)
        if '- r2' in desc or '- r3' in desc:
            continue
        if dtype and dtype not in splits:
            splits[dtype] = d
    
    for seg, prefix in [('SW', 'swim'), ('T1', 't1'), ('CY', 'bike'), ('T2', 't2'), ('RU', 'run')]:
        d = splits.get(seg, {})
        row[f'{prefix}_time_s'] = parse_time_to_seconds(d.get('Interval')) or ''
        row[f'{prefix}_rank'] = safe_int(d.get('RK')) or ''
    
    # --- HISTORICAL FEATURES (computed from results before this race) ---
    past_results = [(dt, r) for dt, r in athlete_all_results[license_id] if dt < race_date]
    past_elite = [(dt, r) for dt, r in past_results if is_elite_triathlon(r) and not is_relay(r)]
    
    row['n_races_before'] = len(past_results)
    row['n_elite_races_before'] = len(past_elite)
    
    # Recent positions
    past_positions = [safe_int(r.get('Rk')) for _, r in past_elite if safe_int(r.get('Rk'))]
    past_all_positions = [safe_int(r.get('Rk')) for _, r in past_results if safe_int(r.get('Rk'))]
    
    # Recent positions (use whatever is available up to the window size)
    past_3 = past_positions[-3:] if past_positions else []
    past_5 = past_positions[-5:] if past_positions else []
    
    row['avg_finish_pos_last_3'] = round(sum(past_3) / len(past_3), 1) if past_3 else ''
    row['avg_finish_pos_last_5'] = round(sum(past_5) / len(past_5), 1) if past_5 else ''
    row['best_finish_pos_ever'] = min(past_positions) if past_positions else ''
    
    # Best in current season
    season_positions = [safe_int(r.get('Rk')) for dt, r in past_elite 
                       if safe_int(r.get('Rk')) and dt.year == race_date.year]
    row['best_finish_pos_season'] = min(season_positions) if season_positions else ''
    
    # Split averages (last 5 races with data)
    for seg, prefix in [('SW', 'swim'), ('CY', 'bike'), ('RU', 'run')]:
        recent_ranks = []
        for _, r in reversed(past_results[-10:]):
            for d in r.get('ResDetail', []):
                if d.get('Type') == seg and safe_int(d.get('RK')):
                    recent_ranks.append(safe_int(d.get('RK')))
                    break
            if len(recent_ranks) >= 5:
                break
        row[f'avg_{prefix}_rank_last_5'] = round(sum(recent_ranks) / len(recent_ranks), 1) if recent_ranks else ''
    
    # Win/podium/top10 rates
    if past_positions:
        row['win_rate'] = round(sum(1 for p in past_positions if p == 1) / len(past_positions), 3)
        row['podium_rate'] = round(sum(1 for p in past_positions if p <= 3) / len(past_positions), 3)
        row['top10_rate'] = round(sum(1 for p in past_positions if p <= 10) / len(past_positions), 3)
    else:
        row['win_rate'] = 0.0
        row['podium_rate'] = 0.0
        row['top10_rate'] = 0.0
    
    # DNF rate
    past_irms = [(r.get('IRM', '') or '').strip().upper() for _, r in past_results]
    row['dnf_rate'] = round(sum(1 for i in past_irms if i == 'DNF') / len(past_irms), 3) if past_irms else 0.0
    
    # Days since last race
    if past_results:
        last_race_date = past_results[-1][0]
        row['days_since_last_race'] = (race_date - last_race_date).days
    else:
        row['days_since_last_race'] = 999  # Large number instead of empty
        
    # --- RANKING EVOLUTION FEATURES ---
    if len(past_positions) >= 1:
        # Last 30 days
        pos_30d = [safe_int(r.get('Rk')) for dt, r in past_elite 
                   if safe_int(r.get('Rk')) and (race_date - dt).days <= 30]
        pos_90d = [safe_int(r.get('Rk')) for dt, r in past_elite 
                   if safe_int(r.get('Rk')) and (race_date - dt).days <= 90]
        pos_180d = [safe_int(r.get('Rk')) for dt, r in past_elite 
                    if safe_int(r.get('Rk')) and (race_date - dt).days <= 180]
        
        # Compare recent performance to overall
        overall_avg = sum(past_positions) / len(past_positions)
        recent_avg = sum(past_positions[-3:]) / len(past_positions[-3:])
        
        # Positive = improving (lower positions = better)
        momentum = round(overall_avg - recent_avg, 1)
        row['ranking_momentum'] = momentum
        
        if momentum > 3:
            row['ranking_trend'] = 'ascending'
        elif momentum < -3:
            row['ranking_trend'] = 'descending'
        else:
            row['ranking_trend'] = 'stable'
        
        # Form score (0-100, higher = better form)
        recent_3 = sum(past_positions[-3:]) / len(past_positions[-3:])
        best = min(past_positions)
        worst = max(past_positions)
        rng = worst - best if worst != best else 1
        form_raw = 1 - (recent_3 - best) / rng
        row['form_score'] = round(max(0, min(100, form_raw * 100)), 1)
        
        # Position change indicators
        if len(past_positions) >= 2:
            older_avg = sum(past_positions[-6:-3]) / len(past_positions[-6:-3]) if len(past_positions) >= 4 else overall_avg
            newer_avg = sum(past_positions[-3:]) / len(past_positions[-3:])
            change = round(older_avg - newer_avg, 1)  # Positive = improving
            row['ranking_change_recent'] = change
            
            if change > 0:
                row['form_trend'] = 'ascending'
            elif change < 0:
                row['form_trend'] = 'descending'
            else:
                row['form_trend'] = 'stable'
        else:
            row['ranking_change_recent'] = 0.0
            row['form_trend'] = 'stable'
    else:
        row['ranking_momentum'] = 0.0
        row['ranking_trend'] = 'stable'
        row['form_score'] = 50.0  # Default form score
        row['ranking_change_recent'] = 0.0
        row['form_trend'] = 'stable'
    
    # --- PERFORMANCE BY CONDITIONS ---
    if past_results:
        pos_high_alt = []
        pos_low_alt = []
        pos_coastal = []
        pos_inland = []
        pos_hot = []
        pos_cold = []
        
        for dt, r in past_results:
            p = safe_int(r.get('Rk'))
            if not p:
                continue
            c = r.get('ChdCity', '')
            g = get_geo(c)
            
            temp = safe_float(r.get('Temperature'))
            if temp is None:
                cached_opp = weather_cache.get(str(r.get('ChId')), {})
                cached_t = cached_opp.get('temperature', '')
                if cached_t != '':
                    temp = safe_float(cached_t)
            
            if g[2] is not None:
                if g[2] > 600:
                    pos_high_alt.append(p)
                elif g[2] < 100:
                    pos_low_alt.append(p)
            
            if g[3] is not None:
                if g[3]:
                    pos_coastal.append(p)
                else:
                    pos_inland.append(p)
            
            if temp is not None:
                if temp > 25:
                    pos_hot.append(p)
                elif temp < 15:
                    pos_cold.append(p)
        
        row['avg_pos_high_altitude'] = round(sum(pos_high_alt) / len(pos_high_alt), 1) if pos_high_alt else ''
        row['avg_pos_low_altitude'] = round(sum(pos_low_alt) / len(pos_low_alt), 1) if pos_low_alt else ''
        row['avg_pos_coastal'] = round(sum(pos_coastal) / len(pos_coastal), 1) if pos_coastal else ''
        row['avg_pos_inland'] = round(sum(pos_inland) / len(pos_inland), 1) if pos_inland else ''
        row['avg_pos_hot'] = round(sum(pos_hot) / len(pos_hot), 1) if pos_hot else ''
        row['avg_pos_cold'] = round(sum(pos_cold) / len(pos_cold), 1) if pos_cold else ''
        
        # Bias features (negative = performs better in condition A vs B)
        if pos_high_alt and pos_low_alt:
            row['performance_altitude_bias'] = round(
                sum(pos_low_alt)/len(pos_low_alt) - sum(pos_high_alt)/len(pos_high_alt), 1)
        else:
            row['performance_altitude_bias'] = 0.0
        
        if pos_coastal and pos_inland:
            row['performance_coast_bias'] = round(
                sum(pos_inland)/len(pos_inland) - sum(pos_coastal)/len(pos_coastal), 1)
        else:
            row['performance_coast_bias'] = 0.0
        
        if pos_hot and pos_cold:
            row['performance_heat_bias'] = round(
                sum(pos_cold)/len(pos_cold) - sum(pos_hot)/len(pos_hot), 1)
        else:
            row['performance_heat_bias'] = 0.0
    else:
        for f in ['avg_pos_high_altitude', 'avg_pos_low_altitude', 'avg_pos_coastal',
                   'avg_pos_inland', 'avg_pos_hot', 'avg_pos_cold']:
            row[f] = ''
        for f in ['performance_altitude_bias', 'performance_coast_bias', 'performance_heat_bias']:
            row[f] = 0.0
    
    # --- RACE COMPETITIVENESS FEATURES ---
    race_key = f"{result.get('ChId')}_{result.get('EvDes')}_{result.get('PhDes', '')}"
    participants = race_participants.get(race_key, [])
    
    row['n_participants_race'] = len(participants) if participants else ''
    
    # Average ranking of opponents
    opponent_rankings = []
    for opp_license, opp_pos, opp_time in participants:
        if opp_license == license_id:
            continue
        opp_data = athletes.get(opp_license, {})
        opp_rk = opp_data.get('athleteBasicInfo', {}).get('rankings', {}).get('triatlon')
        if opp_rk is not None:
            opponent_rankings.append(opp_rk)
    
    row['avg_ranking_opponents'] = round(sum(opponent_rankings) / len(opponent_rankings), 1) if opponent_rankings else ''
    
    my_ranking = rankings.get('triatlon')
    if my_ranking and opponent_rankings:
        row['pct_opponents_ranked_higher'] = round(
            sum(1 for r in opponent_rankings if r < my_ranking) / len(opponent_rankings), 3)
    else:
        row['pct_opponents_ranked_higher'] = ''
    
    # Previous races at this city
    prev_at_city = [(dt, r) for dt, r in past_results if r.get('ChdCity') == city]
    row['n_races_at_city'] = len(prev_at_city)
    row['n_previous_wins_at_city'] = sum(1 for _, r in prev_at_city if safe_int(r.get('Rk')) == 1)
    
    # --- CONSISTENCY FEATURES ---
    if len(past_all_positions) >= 3:
        row['position_std_dev'] = round(
            (sum((p - sum(past_all_positions)/len(past_all_positions))**2 
                 for p in past_all_positions) / len(past_all_positions)) ** 0.5, 1)
    else:
        row['position_std_dev'] = ''
    
    # Streak features
    if past_positions:
        # Current podium streak
        streak = 0
        for p in reversed(past_positions):
            if p <= 3:
                streak += 1
            else:
                break
        row['current_podium_streak'] = streak
        
        # Current top10 streak
        streak10 = 0
        for p in reversed(past_positions):
            if p <= 10:
                streak10 += 1
            else:
                break
        row['current_top10_streak'] = streak10
    else:
        row['current_podium_streak'] = 0
        row['current_top10_streak'] = 0
    
    dataset.append(row)

print(f"  Built {len(dataset)} feature rows")

# ============================================================================
# PASO 6: WRITE CSV
# ============================================================================

print("\n[4/5] Writing CSV...")

# Define column order
columns = [
    # Athlete
    'athlete_id', 'athlete_name', 'athlete_age_at_race', 'athlete_club',
    'athlete_federation', 'athlete_ranking_triatlon', 'athlete_ranking_wr', 'athlete_has_wt_id',
    # Race
    'race_id', 'race_name', 'race_city', 'race_date', 'race_season',
    'race_event_desc', 'race_phase', 'race_temperature', 'race_humidity',
    'race_lat', 'race_lng', 'race_altitude_m', 'race_near_coast', 'race_climate_type',
    'race_month', 'race_day_of_week', 'race_type',
    # Result (target)
    'finish_position', 'finish_time_seconds', 'is_dnf', 'is_dns', 'is_dsq',
    # Splits
    'swim_time_s', 'swim_rank', 't1_time_s', 't1_rank', 'bike_time_s', 'bike_rank',
    't2_time_s', 't2_rank', 'run_time_s', 'run_rank',
    # Historical
    'n_races_before', 'n_elite_races_before',
    'avg_finish_pos_last_3', 'avg_finish_pos_last_5',
    'best_finish_pos_ever', 'best_finish_pos_season',
    'avg_swim_rank_last_5', 'avg_bike_rank_last_5', 'avg_run_rank_last_5',
    'win_rate', 'podium_rate', 'top10_rate', 'dnf_rate',
    'days_since_last_race',
    # Ranking evolution
    'ranking_momentum', 'ranking_trend', 'ranking_change_recent', 'form_score', 'form_trend',
    # Performance by conditions
    'avg_pos_high_altitude', 'avg_pos_low_altitude', 'avg_pos_coastal', 'avg_pos_inland',
    'avg_pos_hot', 'avg_pos_cold',
    'performance_altitude_bias', 'performance_coast_bias', 'performance_heat_bias',
    # Race competitiveness
    'n_participants_race', 'avg_ranking_opponents', 'pct_opponents_ranked_higher',
    'n_races_at_city', 'n_previous_wins_at_city',
    # Consistency
    'position_std_dev', 'current_podium_streak', 'current_top10_streak',
]

with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=columns, delimiter=';', extrasaction='ignore')
    writer.writeheader()
    for row in sorted(dataset, key=lambda x: (x.get('race_date', ''), int(x['finish_position']) if x.get('finish_position') not in ('', None) else 9999)):
        writer.writerow(row)

print(f"  Written to: {OUTPUT_CSV}")

# ============================================================================
# PASO 7: SUMMARY STATS
# ============================================================================

print("\n[5/5] Dataset summary:")
print(f"  Total rows: {len(dataset)}")
print(f"  Total columns: {len(columns)}")
print(f"  Unique athletes: {len(set(r['athlete_id'] for r in dataset))}")
print(f"  Unique races: {len(set(r['race_id'] for r in dataset))}")
print(f"  Date range: {min(r['race_date'] for r in dataset if r['race_date'])} to {max(r['race_date'] for r in dataset if r['race_date'])}")

# Race types
type_counts = defaultdict(int)
for r in dataset:
    type_counts[r['race_type']] += 1
print(f"  Race types:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"    {t}: {c}")

# Geo coverage
geo_filled = sum(1 for r in dataset if r.get('race_lat'))
print(f"  Geo coverage: {geo_filled}/{len(dataset)} ({geo_filled/len(dataset)*100:.1f}%)")

# Historical features coverage
hist_filled = sum(1 for r in dataset if r.get('avg_finish_pos_last_3'))
print(f"  Historical features (last_3): {hist_filled}/{len(dataset)} ({hist_filled/len(dataset)*100:.1f}%)")

form_filled = sum(1 for r in dataset if r.get('form_score') != '')
print(f"  Form score: {form_filled}/{len(dataset)} ({form_filled/len(dataset)*100:.1f}%)")

print(f"\n{'=' * 70}")
print(f"DONE! CSV ready at: {OUTPUT_CSV}")
print(f"{'=' * 70}")
