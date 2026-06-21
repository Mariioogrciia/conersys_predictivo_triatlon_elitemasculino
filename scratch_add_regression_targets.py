import pandas as pd

csv_path = r'c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\data\raw\elite_masculina_triatlon\dataset\dataset_automl_entrenamiento.csv'

print("Reading CSV...")
df = pd.read_csv(csv_path)

# Añadir trucos matemáticos para regresión
# 1. Inversa de la posición (prioriza brutalmente los primeros puestos)
df['inversa_posicion'] = 1.0 / df['finish_position']

# 2. Logaritmo de la posición (suaviza la curva, buen punto intermedio)
import numpy as np
df['log_posicion'] = np.log1p(df['finish_position']) # log(1 + pos)

df.to_csv(csv_path, index=False)
print("Añadidas columnas 'inversa_posicion' y 'log_posicion' con éxito.")
