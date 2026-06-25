import os
import joblib
import shap
import pandas as pd
import numpy as np

class TriathlonShapExplainer:
    def __init__(self):
        # Rutas
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, "models", "model_local_v2.pkl")
        
        # Cargar modelo
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"No se encontró el modelo XGBoost en {self.model_path}")
            
        model_data = joblib.load(self.model_path)
        self.xgb_model = model_data['model']
        self.feature_cols = model_data['feature_cols']
        
        # Iniciar SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.xgb_model)

    def explain_prediction(self, features_dict):
        """
        Recibe un diccionario con las features (mismas que usó el modelo).
        Devuelve el Top 3 de factores que SUMAN puestos (hacen la predicción peor)
        y el Top 3 que RESTAN puestos (hacen la predicción mejor/más rápida).
        """
        # Crear un dataframe temporal con las features en el orden exacto
        # Rellenar con 0 lo que falte
        row_data = {}
        for col in self.feature_cols:
            row_data[col] = [features_dict.get(col, 0.0)]
            
        df_row = pd.DataFrame(row_data)
        
        # Calcular valores SHAP
        shap_values = self.explainer.shap_values(df_row)
        
        # shap_values puede devolver una lista si es multiclase, pero para XGBRegressor es un array
        if isinstance(shap_values, list):
            sv = shap_values[0][0]
        else:
            sv = shap_values[0]
            
        base_value = self.explainer.expected_value
        if isinstance(base_value, (list, np.ndarray)):
            base_value = base_value[0]
            
        # Emparejar nombres de features con sus valores SHAP
        feature_impacts = []
        for i, col in enumerate(self.feature_cols):
            val = float(sv[i])
            if abs(val) > 0.01: # Ignorar impactos nulos
                feature_impacts.append({
                    "factor": col,
                    "impacto": val,
                    "valor_original": df_row[col].iloc[0]
                })
                
        # Ordenar por impacto
        # Los que tienen impacto negativo (restan puestos = mejoran el resultado)
        mejores_factores = sorted([f for f in feature_impacts if f['impacto'] < 0], key=lambda x: x['impacto'])
        
        # Los que tienen impacto positivo (suman puestos = empeoran el resultado)
        peores_factores = sorted([f for f in feature_impacts if f['impacto'] > 0], key=lambda x: x['impacto'], reverse=True)
        
        return {
            "base_value_puestos": round(float(base_value), 2),
            "top_3_factores_a_favor": [{"factor": f['factor'], "impacto": f"{round(f['impacto'], 2)} puestos", "valor": f['valor_original']} for f in mejores_factores[:3]],
            "top_3_factores_en_contra": [{"factor": f['factor'], "impacto": f"+{round(f['impacto'], 2)} puestos", "valor": f['valor_original']} for f in peores_factores[:3]]
        }

if __name__ == "__main__":
    print("Probando módulo SHAP con un perfil simulado...")
    explainer = TriathlonShapExplainer()
    
    # Perfil simulado: Atleta joven (22 años), buena racha reciente (media de 5 en últimas pruebas)
    # pero compitiendo a mucha altitud y temperatura extrema.
    perfil_ejemplo = {
        'athlete_age_at_race': 22.0,
        'avg_finish_pos_last_3': 5.0,
        'avg_finish_pos_last_5': 8.0,
        'race_temperature': 35.0, # Calor extremo
        'race_altitude_m': 2000.0, # Altura elevada
        'n_races_before': 15,
        'win_rate': 0.1,
        'form_score': 85.0
    }
    
    resultado = explainer.explain_prediction(perfil_ejemplo)
    
    import json
    print("\nExplicación SHAP de la predicción:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
