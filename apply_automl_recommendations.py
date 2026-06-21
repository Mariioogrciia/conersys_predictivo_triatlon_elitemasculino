import pandas as pd
import numpy as np
import os

csv_path = r'c:\Users\mario\PycharmProjects\conersys_predictivo_triatlon_elitemasculino\data\raw\elite_masculina_triatlon\dataset\dataset_automl_entrenamiento.csv'

print(f"Reading CSV from {csv_path}")
df = pd.read_csv(csv_path)

def assign_category(pos):
    if pd.isna(pos):
        return 'Peloton'
    if pos <= 10:
        return 'Elite_Top10'
    elif pos <= 25:
        return 'Aspirantes_Top25'
    else:
        return 'Peloton'

def assign_weight(pos):
    if pd.isna(pos):
        return 1.0
    if pos <= 3:
        return 10.0
    elif pos <= 10:
        return 5.0
    elif pos <= 25:
        return 2.5
    else:
        return 1.0

# Add new columns based on recommendations
df['categoria_target'] = df['finish_position'].apply(assign_category)
df['peso_ejemplo'] = df['finish_position'].apply(assign_weight)

print(f"Added columns: 'categoria_target' and 'peso_ejemplo'")
print("\nTarget categories distribution:")
print(df['categoria_target'].value_counts())

print("\nSample weights distribution:")
print(df['peso_ejemplo'].value_counts())

# Save back to CSV
df.to_csv(csv_path, index=False)
print("\nCSV successfully updated and saved!")
