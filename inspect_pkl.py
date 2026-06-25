import joblib

model_dict = joblib.load('models/model_local.pkl')
print(type(model_dict))
if isinstance(model_dict, dict):
    print("Keys in dict:", model_dict.keys())
    for k, v in model_dict.items():
        print(f"Key: {k}, Type: {type(v)}")
