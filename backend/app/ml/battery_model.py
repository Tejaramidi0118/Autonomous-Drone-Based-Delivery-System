from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor


MODEL_PATH = Path(__file__).with_name("battery_rf.joblib")


def train_model() -> RandomForestRegressor:
    rng = np.random.default_rng(42)
    distance = rng.uniform(1, 35, 800)
    payload = rng.uniform(0.1, 6, 800)
    wind = rng.uniform(0, 16, 800)
    humidity = rng.uniform(20, 95, 800)
    temp = rng.uniform(18, 42, 800)
    noise = rng.normal(0, 1.2, 800)
    y = distance * 1.7 + payload * 4.5 + wind * 1.1 + humidity * 0.035 + np.maximum(temp - 25, 0) * 0.25 + noise
    x = np.column_stack([distance, payload, wind, humidity, temp])
    model = RandomForestRegressor(n_estimators=120, random_state=42)
    model.fit(x, y)
    joblib.dump(model, MODEL_PATH)
    return model


def load_model() -> RandomForestRegressor:
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return train_model()


def predict_battery_usage(distance_km: float, payload_kg: float, wind_speed: float, humidity: float, temperature: float) -> float:
    model = load_model()
    prediction = model.predict([[distance_km, payload_kg, wind_speed, humidity, temperature]])[0]
    return max(4.0, min(95.0, float(prediction)))
