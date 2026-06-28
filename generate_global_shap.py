import sys, os
from pathlib import Path
import pandas as pd
import shap
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from chatbot.shap_explainer import _load_model, DATA_PATH, FEATURE_COLS, CAT_COLS, FEATURE_LABELS

def generate_shap_plot():
    print("Cargando modelo...")
    bundle = _load_model()
    model = bundle["model"]
    encoders = bundle.get("encoders", {})

    print("Cargando datos reales...")
    df = pd.read_csv(DATA_PATH)
    for col in CAT_COLS:
        df[col] = df[col].astype(str).replace('nan', 'missing')
        if col in encoders:
            df[col] = encoders[col].transform(df[[col]])

    df = df.dropna(subset=FEATURE_COLS)
    
    # Tomamos 300 muestras para que el gráfico quede bien denso
    X = df[FEATURE_COLS].sample(min(300, len(df)), random_state=42)

    print("Calculando SHAP values globales...")
    # XGBoost suele tener TreeExplainer
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
    except Exception as e:
        print(f"Fallo TreeExplainer: {e}. Usando genérico.")
        explainer = shap.Explainer(model.predict, X, algorithm="permutation")
        shap_values_obj = explainer(X)
        shap_values = shap_values_obj.values

    # Renombramos a nombres amigables
    X_labeled = X.rename(columns=FEATURE_LABELS)

    print("Generando imagen...")
    plt.figure(figsize=(14, 10))
    # Forzamos estilo oscuro
    plt.style.use('dark_background')
    
    # max_display=15 para que se lean bien los más importantes
    shap.summary_plot(shap_values, X_labeled, max_display=15, show=False)
    
    # Ajustar estilos de los ejes
    ax = plt.gca()
    ax.tick_params(axis='both', colors='white', labelsize=12)
    ax.xaxis.label.set_color('white')
    ax.xaxis.label.set_fontsize(14)

    out_dir = BASE_DIR / "frontend" / "public" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Beeswarm Plot
    plt.figure(figsize=(14, 10))
    plt.style.use('dark_background')
    shap.summary_plot(shap_values, X_labeled, max_display=15, show=False)
    ax = plt.gca()
    ax.tick_params(axis='both', colors='white', labelsize=12)
    ax.xaxis.label.set_color('white')
    ax.xaxis.label.set_fontsize(14)
    plt.savefig(out_dir / "shap_summary.png", bbox_inches='tight', dpi=300, facecolor='#0f111a', edgecolor='none')
    plt.close()
    
    # 2. Bar Plot (Magnitud Absoluta)
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_labeled, plot_type="bar", max_display=15, show=False, color="#3b82f6")
    ax = plt.gca()
    ax.tick_params(axis='both', colors='white', labelsize=12)
    ax.xaxis.label.set_color('white')
    ax.xaxis.label.set_fontsize(14)
    plt.savefig(out_dir / "shap_bar.png", bbox_inches='tight', dpi=300, facecolor='#0f111a', edgecolor='none')
    plt.close()

    # Identificar top features
    import numpy as np
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    top_idxs = np.argsort(mean_abs_shap)[::-1]
    top1 = X_labeled.columns[top_idxs[0]]
    top2 = X_labeled.columns[top_idxs[1]]

    # 3. Dependence Plot Top 1
    plt.figure(figsize=(10, 6))
    shap.dependence_plot(top1, shap_values, X_labeled, show=False, interaction_index=None, color="#f59e0b")
    ax = plt.gca()
    ax.tick_params(axis='both', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    plt.savefig(out_dir / "shap_dependence_1.png", bbox_inches='tight', dpi=300, facecolor='#0f111a', edgecolor='none')
    plt.close()

    # 4. Dependence Plot Top 2 (con interacción automática)
    plt.figure(figsize=(10, 6))
    shap.dependence_plot(top2, shap_values, X_labeled, show=False)
    ax = plt.gca()
    ax.tick_params(axis='both', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    # Ajustar la barra de color (interacción)
    fig = plt.gcf()
    for cb in fig.axes:
        cb.tick_params(colors='white')
        if cb.yaxis.label: cb.yaxis.label.set_color('white')
    plt.savefig(out_dir / "shap_dependence_2.png", bbox_inches='tight', dpi=300, facecolor='#0f111a', edgecolor='none')
    plt.close()
    
    print(f"¡Todos los gráficos guardados en {out_dir}!")

if __name__ == "__main__":
    generate_shap_plot()
