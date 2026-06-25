import joblib
import pickle

try:
    with open('models/model.pkl', 'rb') as f:
        model = pickle.load(f)
    print("Loaded with pickle:", type(model))
except Exception as e:
    print("Pickle failed:", e)

try:
    model2 = joblib.load('models/model_local.pkl')
    print("Loaded model_local with joblib:", type(model2))
except Exception as e:
    print("Joblib failed:", e)
