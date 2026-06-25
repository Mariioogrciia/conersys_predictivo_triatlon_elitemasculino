import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.metrics import mean_absolute_error
from scipy.stats import spearmanr

print("Cargando dataset...")
df = pd.read_csv('data/raw/elite_masculina_triatlon/dataset/dataset_automl_entrenamiento.csv')

# Features del modelo
feature_cols = ['athlete_age_at_race', 'athlete_federation', 'athlete_ranking_triatlon', 'athlete_has_wt_id', 'race_city', 'race_temperature', 'race_humidity', 'race_lat', 'race_lng', 'race_altitude_m', 'race_near_coast', 'race_climate_type', 'race_month', 'race_day_of_week', 'race_type', 'n_races_before', 'n_elite_races_before', 'avg_finish_pos_last_3', 'avg_finish_pos_last_5', 'best_finish_pos_ever', 'best_finish_pos_season', 'avg_swim_rank_last_5', 'avg_bike_rank_last_5', 'avg_run_rank_last_5', 'win_rate', 'podium_rate', 'top10_rate', 'dnf_rate', 'days_since_last_race', 'ranking_momentum', 'ranking_trend', 'ranking_change_recent', 'form_score', 'form_trend', 'avg_pos_high_altitude', 'avg_pos_low_altitude', 'avg_pos_coastal', 'avg_pos_inland', 'avg_pos_hot', 'avg_pos_cold', 'performance_altitude_bias', 'performance_coast_bias', 'performance_heat_bias', 'n_participants_race', 'avg_ranking_opponents', 'pct_opponents_ranked_higher', 'n_races_at_city', 'n_previous_wins_at_city', 'position_std_dev', 'current_podium_streak', 'current_top10_streak']

from sklearn.preprocessing import OrdinalEncoder

# Categorical columns
cat_cols = ['athlete_federation', 'race_city', 'race_climate_type', 'race_type', 'ranking_trend', 'form_trend']

encoders = {}
for col in cat_cols:
    df[col] = df[col].astype(str)
    # Fill nan with 'missing'
    df[col] = df[col].replace('nan', 'missing')
    enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    df[col] = enc.fit_transform(df[[col]])
    encoders[col] = enc

target_col = 'finish_position'

# Split temporal para train y test
train_seasons = [2022, 2023, 2024, 2025]
test_seasons = [2026]

df_train = df[df['race_season'].isin(train_seasons)].copy()
df_test = df[df['race_season'].isin(test_seasons)].copy()

X_train = df_train[feature_cols]
y_train = df_train[target_col]
X_test = df_test[feature_cols]
y_test = df_test[target_col]

print(f"Train size: {len(X_train)}")
print(f"Test size: {len(X_test)}")

print("Entrenando XGBoost...")
model = xgb.XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    tree_method='hist',
    early_stopping_rounds=50
)

# Fit model with early stopping
model.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_test, y_test)],
    verbose=False
)

print(f"Mejor iteracion: {model.best_iteration}")

# Evaluacion
preds = model.predict(X_test)
df_test_eval = df_test.copy()
df_test_eval['PRED'] = preds

# Calculamos metricas globales y por carrera
print("\n--- Evaluacion en Test (2026) ---")
carreras = df_test_eval['race_event_desc'].unique()
spearmans = []
maes = []

for c in carreras:
    df_c = df_test_eval[df_test_eval['race_event_desc'] == c].copy()
    if len(df_c) < 10: continue
    
    df_c = df_c.sort_values('PRED', ascending=True)
    df_c['RANK_PRED'] = range(1, len(df_c) + 1)
    df_c = df_c.sort_values(target_col)
    
    mae = mean_absolute_error(df_c[target_col], df_c['RANK_PRED'])
    sp, _ = spearmanr(df_c[target_col], df_c['RANK_PRED'])
    
    spearmans.append(sp)
    maes.append(mae)

print(f"Spearman promedio: {np.mean(spearmans):.3f}")
print(f"MAE promedio: {np.mean(maes):.2f} puestos")

# Guardar modelo
model_path = 'models/model_local_v2.pkl'
print(f"\nGuardando modelo en {model_path}...")
model_data = {
    'model': model,
    'feature_cols': feature_cols,
    'target_col': target_col,
    'cat_cols': cat_cols,
    'encoders': encoders
}
joblib.dump(model_data, model_path)
print("Hecho.")
