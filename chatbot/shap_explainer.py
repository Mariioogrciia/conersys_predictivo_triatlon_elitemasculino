"""
SHAP Explainer para el modelo predictivo de Triatlón Élite Masculino.

Carga el modelo (Azure AutoML o local XGBoost) y devuelve predicciones
con explicaciones SHAP listas para consumir desde un chatbot.
"""
import os
import pickle
import warnings
import numpy as np
import pandas as pd
import shap
from pathlib import Path

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
LOCAL_MODEL_PATH = BASE_DIR / "models" / "model_local.pkl"
DATA_PATH = BASE_DIR / "data" / "processed" / "trm_2025_azure_automl.csv"

# Columnas que el modelo usa (sin targets ni identificadores)
FEATURE_COLS = [
    "CHAMPIONSHIP_LEVEL",
    "ALTITUD",
    "TEMPERATURA_MAX",
    "HUMEDAD_MEDIA",
    "PRECIPITACION",
    "VIENTO_MAX",
    "IS_EXTREME_HEAT",
    "IS_WET_RACE",
    "VIAJE_DISTANCIA_KM",
    "ES_LOCAL",
    "MES_CARRERA",
    "MES_SIN",
    "MES_COS",
    "DAYS_SINCE_LAST_RACE",
    "FATIGUE_INDEX",
    "CLUB_POWER_SCORE",
    "RECENT_AVG_PUNTOS",
    "HIST_AVG_PUNTOS",
    "HIST_STD_PUNTOS",
    "HIST_MAX_PUNTOS",
    "HIST_COUNT_PRUEBAS",
]

TARGET_COL = "PUNTOS_TARGET"

# Descripciones en español de cada feature para las explicaciones
FEATURE_LABELS = {
    "CHAMPIONSHIP_LEVEL": "nivel del campeonato",
    "ALTITUD": "altitud de la prueba (m)",
    "TEMPERATURA_MAX": "temperatura máxima (°C)",
    "HUMEDAD_MEDIA": "humedad media (%)",
    "PRECIPITACION": "precipitación (mm)",
    "VIENTO_MAX": "viento máximo (km/h)",
    "IS_EXTREME_HEAT": "calor extremo",
    "IS_WET_RACE": "prueba mojada/lluvia",
    "VIAJE_DISTANCIA_KM": "distancia de viaje (km)",
    "ES_LOCAL": "prueba local",
    "MES_CARRERA": "mes de la carrera",
    "MES_SIN": "estacionalidad (seno)",
    "MES_COS": "estacionalidad (coseno)",
    "DAYS_SINCE_LAST_RACE": "días desde la última prueba",
    "FATIGUE_INDEX": "índice de fatiga",
    "CLUB_POWER_SCORE": "potencia del club",
    "RECENT_AVG_PUNTOS": "media reciente de puntos",
    "HIST_AVG_PUNTOS": "media histórica de puntos",
    "HIST_STD_PUNTOS": "variabilidad histórica de puntos",
    "HIST_MAX_PUNTOS": "máximo histórico de puntos",
    "HIST_COUNT_PRUEBAS": "número total de pruebas disputadas",
}


def _train_local_model():
    """Entrena XGBoost local sobre el CSV de AutoML y lo guarda en models/."""
    from xgboost import XGBRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score

    print("[SHAP] Entrenando modelo local XGBoost desde el dataset CSV...")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, shuffle=True
    )

    model = XGBRegressor(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"[SHAP] Modelo local entrenado — MAE: {mae:.2f} pts · R²: {r2:.3f}")

    with open(LOCAL_MODEL_PATH, "wb") as f:
        pickle.dump({"model": model, "feature_cols": FEATURE_COLS}, f)

    print(f"[SHAP] Modelo guardado en {LOCAL_MODEL_PATH}")
    return model


def _load_model():
    """
    Intenta cargar el modelo Azure AutoML. Si falla por dependencias,
    usa el modelo local XGBoost (lo entrena si no existe aún).
    """
    # 1. Intentar modelo local (ya entrenado)
    if LOCAL_MODEL_PATH.exists():
        with open(LOCAL_MODEL_PATH, "rb") as f:
            bundle = pickle.load(f)
        print("[SHAP] Modelo local cargado desde cache.")
        return bundle["model"]

    # 2. Intentar Azure AutoML
    try:
        with open(MODEL_PATH, "rb") as f:
            azure_model = pickle.load(f)
        print("[SHAP] Modelo Azure AutoML cargado.")
        return azure_model
    except (ModuleNotFoundError, ImportError, Exception) as e:
        print(f"[SHAP] No se pudo cargar model.pkl ({type(e).__name__}). Usando modelo local.")

    # 3. Entrenar modelo local como fallback
    return _train_local_model()


class TriathlonExplainer:
    """
    Wraps the prediction model with SHAP to generate human-readable
    explanations for each prediction. Designed for chatbot consumption.
    """

    def __init__(self):
        self.model = _load_model()
        self._explainer = None
        self._background = None
        self._init_explainer()

    def _init_explainer(self):
        """Inicializa el TreeExplainer de SHAP con datos de referencia del dataset."""
        df = pd.read_csv(DATA_PATH)
        df = df.dropna(subset=FEATURE_COLS)
        background = df[FEATURE_COLS].sample(min(100, len(df)), random_state=42)
        self._background = background

        try:
            # TreeExplainer funciona con XGBoost, RandomForest, etc.
            self._explainer = shap.TreeExplainer(self.model, background)
            print("[SHAP] TreeExplainer inicializado.")
        except Exception:
            # Fallback genérico para cualquier modelo con .predict
            self._explainer = shap.Explainer(
                self.model.predict, background, algorithm="permutation"
            )
            print("[SHAP] Explainer genérico (permutación) inicializado.")

    def predict(self, features: dict) -> float:
        """Devuelve la predicción de puntos para el atleta."""
        df = self._to_dataframe(features)
        pred = self.model.predict(df)
        return float(pred[0])

    def explain(self, features: dict, top_n: int = 5) -> dict:
        """
        Genera predicción + explicación SHAP para el chatbot.

        Args:
            features: Diccionario con los valores de las features.
            top_n: Número de factores más influyentes a devolver.

        Returns:
            dict con:
              - prediction (float): puntos predichos
              - top_factors (list): lista de factores con nombre, valor, impacto
              - explanation_text (str): texto en español para el chatbot
              - base_value (float): valor base del modelo (media global)
              - shap_values (dict): todos los valores SHAP por feature
        """
        df = self._to_dataframe(features)
        prediction = float(self.model.predict(df)[0])

        sv = self._explainer(df)
        # shap.Explanation o array dependiendo de la versión
        if hasattr(sv, "values"):
            shap_vals = sv.values[0]
            base_val = float(sv.base_values[0]) if hasattr(sv, "base_values") else 0.0
        else:
            shap_vals = np.array(sv)[0]
            base_val = 0.0

        # Construir ranking de factores por impacto absoluto
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
                    "direction": "positivo" if impact > 0 else "negativo",
                }
            )

        factor_list.sort(key=lambda x: abs(x["shap_impact"]), reverse=True)
        top_factors = factor_list[:top_n]

        explanation_text = self._build_explanation(prediction, top_factors, features)

        return {
            "prediction": round(prediction, 2),
            "base_value": round(base_val, 2),
            "top_factors": top_factors,
            "explanation_text": explanation_text,
            "shap_values": {
                f["feature"]: round(f["shap_impact"], 4) for f in factor_list
            },
        }

    def _build_explanation(
        self, prediction: float, top_factors: list, features: dict
    ) -> str:
        """Genera el texto de explicación en español para el chatbot."""
        lines = []

        # Interpretar nivel de predicción
        if prediction >= 1500:
            nivel = "muy alto (podio probable)"
        elif prediction >= 1000:
            nivel = "alto (clasificación top-10 probable)"
        elif prediction >= 500:
            nivel = "medio"
        else:
            nivel = "bajo"

        lines.append(
            f"El modelo predice **{prediction:.0f} puntos** para este atleta en esta prueba, "
            f"un rendimiento {nivel}."
        )

        lines.append("\nLos factores que más influyen en esta predicción son:\n")

        for rank, factor in enumerate(top_factors, 1):
            impact = factor["shap_impact"]
            label = factor["label"]
            value = factor["value"]
            arrow = "(+)" if impact > 0 else "(-)"
            sign = "+" if impact > 0 else ""

            # Formatear valor según tipo
            if isinstance(value, float):
                val_str = f"{value:.1f}"
            else:
                val_str = str(value)

            lines.append(
                f"  {rank}. {arrow} **{label}** ({val_str}) → {sign}{impact:.1f} pts"
            )

        # Añadir contexto deportivo para los factores más importantes
        top1 = top_factors[0] if top_factors else None
        if top1:
            lines.append(f"\n[!] El factor dominante es **{top1['label']}**.")

        # Mencionar si es local
        if features.get("ES_LOCAL") == 1:
            lines.append("[casa] Compite en casa, lo que historicamente favorece su rendimiento.")

        if features.get("IS_EXTREME_HEAT") == 1:
            lines.append("[calor] Calor extremo detectado - factor de riesgo para el atleta.")

        if features.get("IS_WET_RACE") == 1:
            lines.append("[lluvia] Prueba con lluvia - condiciones variables que pueden alterar el resultado.")

        hist = features.get("HIST_COUNT_PRUEBAS", 0)
        if hist is not None and int(hist) < 3:
            lines.append(
                "[aviso] Historial reducido (< 3 pruebas): la prediccion tiene mayor incertidumbre."
            )

        return "\n".join(lines)

    def _to_dataframe(self, features: dict) -> pd.DataFrame:
        """Convierte el dict de features a DataFrame con las columnas correctas."""
        row = {}
        for col in FEATURE_COLS:
            row[col] = features.get(col, self._background[col].median())
        return pd.DataFrame([row], columns=FEATURE_COLS)


# Singleton: se instancia una sola vez al importar el módulo
_explainer_instance: TriathlonExplainer | None = None


def get_explainer() -> TriathlonExplainer:
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = TriathlonExplainer()
    return _explainer_instance
