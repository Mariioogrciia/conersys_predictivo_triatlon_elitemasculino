import os
import json
import urllib.request
import ssl
import pickle
import warnings
import numpy as np
import pandas as pd
import shap
import joblib
from pathlib import Path
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# Cargar variables de entorno
load_dotenv()
AZURE_ML_ENDPOINT = os.getenv("AZURE_ML_ENDPOINT")
AZURE_ML_KEY = os.getenv("AZURE_ML_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_MODEL_PATH = BASE_DIR / "models" / "model_local_v2.pkl"
DATA_PATH = BASE_DIR / "data" / "raw" / "elite_masculina_triatlon" / "dataset" / "dataset_automl_entrenamiento.csv"

FEATURE_COLS = ['athlete_age_at_race', 'athlete_federation', 'athlete_ranking_triatlon', 'athlete_has_wt_id', 'race_city', 'race_temperature', 'race_humidity', 'race_lat', 'race_lng', 'race_altitude_m', 'race_near_coast', 'race_climate_type', 'race_month', 'race_day_of_week', 'race_type', 'n_races_before', 'n_elite_races_before', 'avg_finish_pos_last_3', 'avg_finish_pos_last_5', 'best_finish_pos_ever', 'best_finish_pos_season', 'avg_swim_rank_last_5', 'avg_bike_rank_last_5', 'avg_run_rank_last_5', 'win_rate', 'podium_rate', 'top10_rate', 'dnf_rate', 'days_since_last_race', 'ranking_momentum', 'ranking_trend', 'ranking_change_recent', 'form_score', 'form_trend', 'avg_pos_high_altitude', 'avg_pos_low_altitude', 'avg_pos_coastal', 'avg_pos_inland', 'avg_pos_hot', 'avg_pos_cold', 'performance_altitude_bias', 'performance_coast_bias', 'performance_heat_bias', 'n_participants_race', 'avg_ranking_opponents', 'pct_opponents_ranked_higher', 'n_races_at_city', 'n_previous_wins_at_city', 'position_std_dev', 'current_podium_streak', 'current_top10_streak']
CAT_COLS = ['athlete_federation', 'race_city', 'race_climate_type', 'race_type', 'ranking_trend', 'form_trend']
TARGET_COL = "finish_position"

FEATURE_LABELS = {
    'athlete_age_at_race': 'edad del atleta', 
    'athlete_federation': 'federación', 
    'athlete_ranking_triatlon': 'ranking de triatlón', 
    'athlete_has_wt_id': 'tiene ID de World Triathlon', 
    'race_city': 'ciudad de la carrera', 
    'race_temperature': 'temperatura (°C)', 
    'race_humidity': 'humedad (%)', 
    'race_lat': 'latitud', 
    'race_lng': 'longitud', 
    'race_altitude_m': 'altitud (m)', 
    'race_near_coast': 'carrera cerca de la costa', 
    'race_climate_type': 'tipo de clima', 
    'race_month': 'mes de la carrera', 
    'race_day_of_week': 'día de la semana', 
    'race_type': 'tipo de carrera', 
    'n_races_before': 'carreras previas disputadas', 
    'n_elite_races_before': 'carreras élite previas', 
    'avg_finish_pos_last_3': 'posición media (últimas 3)', 
    'avg_finish_pos_last_5': 'posición media (últimas 5)', 
    'best_finish_pos_ever': 'mejor posición histórica', 
    'best_finish_pos_season': 'mejor posición esta temporada', 
    'avg_swim_rank_last_5': 'ranking medio de natación (últimas 5)', 
    'avg_bike_rank_last_5': 'ranking medio de ciclismo (últimas 5)', 
    'avg_run_rank_last_5': 'ranking medio de carrera (últimas 5)', 
    'win_rate': 'porcentaje de victorias', 
    'podium_rate': 'porcentaje de podios', 
    'top10_rate': 'porcentaje de top 10', 
    'dnf_rate': 'porcentaje de abandonos (DNF)', 
    'days_since_last_race': 'días desde la última carrera', 
    'ranking_momentum': 'momentum en el ranking', 
    'ranking_trend': 'tendencia en el ranking', 
    'ranking_change_recent': 'cambio reciente en el ranking', 
    'form_score': 'puntuación de forma actual', 
    'form_trend': 'tendencia de forma', 
    'avg_pos_high_altitude': 'posición media en altura', 
    'avg_pos_low_altitude': 'posición media a nivel del mar', 
    'avg_pos_coastal': 'posición media en costa', 
    'avg_pos_inland': 'posición media en interior', 
    'avg_pos_hot': 'posición media con calor', 
    'avg_pos_cold': 'posición media con frío', 
    'performance_altitude_bias': 'sesgo de rendimiento en altitud', 
    'performance_coast_bias': 'sesgo de rendimiento en costa', 
    'performance_heat_bias': 'sesgo de rendimiento con calor', 
    'n_participants_race': 'número de participantes', 
    'avg_ranking_opponents': 'ranking medio de oponentes', 
    'pct_opponents_ranked_higher': 'porcentaje de oponentes con mejor ranking', 
    'n_races_at_city': 'carreras previas en esta ciudad', 
    'n_previous_wins_at_city': 'victorias previas en esta ciudad', 
    'position_std_dev': 'desviación estándar de posición', 
    'current_podium_streak': 'racha actual de podios', 
    'current_top10_streak': 'racha actual de top 10'
}

def _load_model():
    if not LOCAL_MODEL_PATH.exists():
        raise FileNotFoundError(f"No se encuentra el modelo en {LOCAL_MODEL_PATH}")
    bundle = joblib.load(LOCAL_MODEL_PATH)
    print("[SHAP] Modelo local v2 cargado desde cache.")
    return bundle

class TriathlonExplainer:
    def __init__(self):
        bundle = _load_model()
        self.model = bundle["model"]
        self.encoders = bundle.get("encoders", {})
        self._explainer = None
        self._background = None
        self._init_explainer()

    def _init_explainer(self):
        df = pd.read_csv(DATA_PATH)
        for col in CAT_COLS:
            df[col] = df[col].astype(str).replace('nan', 'missing')
            if col in self.encoders:
                df[col] = self.encoders[col].transform(df[[col]])
        
        df = df.dropna(subset=FEATURE_COLS)
        background = df[FEATURE_COLS].sample(min(100, len(df)), random_state=42)
        self._background = background

        try:
            self._explainer = shap.TreeExplainer(self.model)
            print("[SHAP] TreeExplainer inicializado.")
        except Exception as e:
            print(f"Error al inicializar TreeExplainer: {e}")
            self._explainer = shap.Explainer(
                self.model.predict, background, algorithm="permutation"
            )
            print("[SHAP] Explainer genérico inicializado.")

    def _call_azure_endpoint_batch(self, df: pd.DataFrame) -> list:
        """Llama al endpoint real de Azure ML para obtener predicciones en bloque."""
        if not AZURE_ML_ENDPOINT or not AZURE_ML_KEY:
            print("[PREDICCIÓN] Sin credenciales Azure ML — usando modelo local en bloque")
            return [float(p) for p in self.model.predict(df)]
            
        data = {
            "input_data": {
                "columns": df.columns.tolist(),
                "data": df.values.tolist()
            }
        }
        body = str.encode(json.dumps(data))
        url = AZURE_ML_ENDPOINT
        api_key = AZURE_ML_KEY
        
        headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key), 'azureml-model-deployment': 'blue' }
        req = urllib.request.Request(url, body, headers)
        
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            response = urllib.request.urlopen(req, context=ctx, timeout=30) # Aumentar timeout por si acaso
            result = response.read()
            res_json = json.loads(result)
            return [float(p) for p in res_json]
        except urllib.error.HTTPError as error:
            print(f"[AZURE ML BATCH] Error HTTP {error.code}: {error.read().decode('utf8', 'ignore')}")
            print("[AZURE ML BATCH] Fallback a modelo local")
            return [float(p) for p in self.model.predict(df)]
        except Exception as e:
            print(f"[AZURE ML BATCH] Error: {e} — Fallback a modelo local")
            return [float(p) for p in self.model.predict(df)]

    def predict(self, features: dict) -> float:
        df = self._to_dataframe(features)
        return self._call_azure_endpoint_batch(df)[0]

    def predict_batch(self, features_list: list) -> list:
        if not features_list:
            return []
        df_list = [self._to_dataframe(f) for f in features_list]
        df = pd.concat(df_list, ignore_index=True)
        return self._call_azure_endpoint_batch(df)

    def explain_batch(self, features_list: list, top_n: int = 5) -> tuple[list, list]:
        """
        Returns (predictions: list, explanation_texts: list) for a batch of athletes.
        """
        if not features_list:
            return [], []
        df_list = [self._to_dataframe(f) for f in features_list]
        df = pd.concat(df_list, ignore_index=True)
        predictions = self._call_azure_endpoint_batch(df)

        sv = self._explainer(df)
        if hasattr(sv, "values"):
            shap_vals_all = sv.values
        else:
            shap_vals_all = np.array(sv)

        explanations = []
        for row_idx in range(len(features_list)):
            shap_vals = shap_vals_all[row_idx]
            features = features_list[row_idx]
            prediction = predictions[row_idx]
            
            factor_list = []
            for i, col in enumerate(FEATURE_COLS):
                impact = float(shap_vals[i])
                value = features.get(col, df.iloc[row_idx][col])
                factor_list.append(
                    {
                        "feature": col,
                        "label": FEATURE_LABELS.get(col, col),
                        "value": value,
                        "shap_impact": impact,
                        "direction": "negativo" if impact > 0 else "positivo",
                    }
                )

            factor_list.sort(key=lambda x: abs(x["shap_impact"]), reverse=True)
            top_factors = factor_list[:top_n]
            explanation_text = self._build_explanation(prediction, top_factors, features)
            explanations.append(explanation_text)

        return predictions, explanations

    def explain(self, features: dict, top_n: int = 5) -> dict:
        df = self._to_dataframe(features)
        prediction = self._call_azure_endpoint_batch(df)[0]

        sv = self._explainer(df)
        if hasattr(sv, "values"):
            shap_vals = sv.values[0]
            base_val = float(sv.base_values[0]) if hasattr(sv, "base_values") else 0.0
        else:
            shap_vals = np.array(sv)[0]
            base_val = 0.0

        factor_list = []
        for i, col in enumerate(FEATURE_COLS):
            impact = float(shap_vals[i])
            value = features.get(col, df[col].iloc[0])
            factor_list.append(
                {
                    "feature": col,
                    "label": FEATURE_LABELS.get(col, col),
                    "value": value,
                    "shap_impact": impact,
                    "direction": "negativo" if impact > 0 else "positivo",
                }
            )

        factor_list.sort(key=lambda x: abs(x["shap_impact"]), reverse=True)
        top_factors = factor_list[:top_n]

        explanation_text = self._build_explanation(prediction, top_factors, features)

        return {
            "prediction": round(prediction, 1),
            "base_value": round(base_val, 1),
            "top_factors": top_factors,
            "explanation_text": explanation_text,
            "shap_values": {
                f["feature"]: round(f["shap_impact"], 4) for f in factor_list
            },
        }

    def _build_explanation(self, prediction: float, top_factors: list, features: dict) -> str:
        lines = []
        # The XGBoost model's raw outputs are shrunk towards the mean (range 28.0 - 45.0 approx).
        # We need to use calibrated thresholds to translate these raw scores to human readable levels.
        if prediction <= 30.5:
            nivel = "excepcional (claro candidato al podio o a la victoria)"
        elif prediction <= 33.0:
            nivel = "muy alto (clasificación top-10 probable)"
        elif prediction <= 36.0:
            nivel = "medio (pelotón principal)"
        else:
            nivel = "bajo (parte trasera)"

        lines.append(f"El modelo predictivo estima una posición base esperada alrededor del **puesto {prediction:.0f}** para este atleta en su estado de forma actual (nivel {nivel}).")
        lines.append("\nLos factores que más influyen en esta predicción son:\n")

        for rank, factor in enumerate(top_factors, 1):
            impact = factor["shap_impact"]
            label = factor["label"]
            value = factor["value"]
            arrow = "(+) sube puestos" if impact > 0 else "(-) baja puestos"
            sign = "+" if impact > 0 else ""
            if isinstance(value, float):
                val_str = f"{value:.1f}"
            else:
                val_str = str(value)
            lines.append(f"  {rank}. {arrow} **{label}** ({val_str}) → {sign}{impact:.1f} posiciones")

        top1 = top_factors[0] if top_factors else None
        if top1:
            lines.append(f"\n[!] El factor dominante es **{top1['label']}**.")

        if features.get("race_near_coast") == 1:
            lines.append("[costa] La carrera es cerca de la costa.")
        if features.get("race_temperature", 0) >= 35:
            lines.append("[calor] Calor extremo detectado - factor de riesgo para el atleta.")
        hist = features.get("n_races_before", 10)
        if hist is not None and int(hist) < 3:
            lines.append("[aviso] Historial reducido (< 3 carreras previas): la predicción tiene mayor incertidumbre.")

        return "\n".join(lines)

    def _to_dataframe(self, features: dict) -> pd.DataFrame:
        row = {}
        for col in FEATURE_COLS:
            if col in CAT_COLS:
                val = str(features.get(col, self._background[col].iloc[0]))
                if col in self.encoders:
                    df_temp = pd.DataFrame({col: [val]})
                    row[col] = self.encoders[col].transform(df_temp)[0][0]
                else:
                    row[col] = val
            else:
                row[col] = features.get(col, self._background[col].median())
        df = pd.DataFrame([row], columns=FEATURE_COLS)
        return df

_explainer_instance = None
def get_explainer() -> TriathlonExplainer:
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = TriathlonExplainer()
    return _explainer_instance
