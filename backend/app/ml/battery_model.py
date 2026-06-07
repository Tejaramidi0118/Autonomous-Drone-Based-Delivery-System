"""
Battery Consumption Prediction Model
=====================================
Predicts the percentage of battery consumed by a drone during a delivery flight.

Physics Model
-------------
Power consumption is derived from actuator disk theory (Leishman, 2006) and
Glauert's forward-flight model, widely used in UAV energy literature:

    P_hover = sqrt( (m*g)^3 / (2 * rho * A) )          [actuator disk theory]
    P_forward = P_induced + P_parasite                   [forward flight]
    E [Wh] = P_forward [W] * t [h]

Air density rho is computed from temperature and humidity using the
Buck equation for saturation vapor pressure (WMO standard).

Battery efficiency degradation at extreme temperatures follows the
Li-ion Peukert effect (temperature below 20°C or above 35°C reduces
effective capacity).

Drone Parameters (DJI Matrice 300-class delivery drone)
-------------------------------------------------------
- Empty mass          : 6.3 kg
- Rotor disk area     : 4 × 0.065 = 0.26 m²
- Cruise speed        : 10.5 m/s (~38 km/h)
- Battery capacity    : 274 Wh (DJI TB60)

References
----------
[1] Leishman, J.G. (2006). Principles of Helicopter Aerodynamics.
    Cambridge University Press.
[2] Stolaroff, J.K. et al. (2018). Energy use and life cycle greenhouse
    gas emissions of drones for commercial package delivery.
    Nature Communications. DOI: 10.1038/s41467-017-02088-w
[3] Dorling, K. et al. (2017). Vehicle Routing Problems for Drone Delivery.
    IEEE Transactions on Systems, Man, and Cybernetics.
    DOI: 10.1109/TSMC.2016.2582745
[4] Buck, A.L. (1981). New equations for computing vapor pressure and
    enhancement factor. Journal of Applied Meteorology.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ---------------------------------------------------------------------------
# Drone constants (DJI Matrice 300-class)
# ---------------------------------------------------------------------------
_DRONE_MASS_KG       = 6.3          # empty airframe mass [kg]
_ROTOR_DISK_AREA_M2  = 4 * 0.065   # 4 rotors × 0.065 m² each [m²]
_CRUISE_SPEED_MS     = 10.5         # cruise speed [m/s] (~38 km/h)
_BATTERY_CAPACITY_WH = 274.0        # usable battery capacity [Wh]
_GRAVITY             = 9.81         # [m/s²]
_FRONTAL_AREA_M2     = 0.25         # drone frontal area for parasite drag [m²]
_DRAG_COEFF          = 0.031        # body drag coefficient (empirical, M300-class)

MODEL_PATH = Path(__file__).with_name("battery_rf.joblib")


# ---------------------------------------------------------------------------
# Physics helpers
# ---------------------------------------------------------------------------

def _air_density(temperature_c: np.ndarray, humidity_pct: np.ndarray) -> np.ndarray:
    """
    Compute air density [kg/m³] from temperature [°C] and relative humidity [%].

    Uses the Buck (1981) equation for saturation vapor pressure and the
    ideal gas law for moist air:
        rho = P_dry/(Rd*T) + P_vapor/(Rv*T)
    """
    T_k   = temperature_c + 273.15
    P_atm = 101_325.0                          # Pa, sea-level (Hyderabad ≈ 500 m; correction < 0.6%)
    Rd, Rv = 287.05, 461.5                     # specific gas constants [J/(kg·K)]

    # Magnus–Buck saturation vapor pressure [Pa]
    e_sat    = 611.2 * np.exp(17.67 * temperature_c / (temperature_c + 243.5))
    e_actual = (humidity_pct / 100.0) * e_sat
    P_dry    = P_atm - e_actual

    return P_dry / (Rd * T_k) + e_actual / (Rv * T_k)


def _forward_flight_power(
    total_mass_kg: np.ndarray,
    rho: np.ndarray,
    wind_speed_ms: np.ndarray,
    wind_headwind_fraction: np.ndarray,
) -> np.ndarray:
    """
    Estimate forward-flight power [W] using Glauert's model.

    Steps:
    1. Hover thrust = m*g
    2. Induced hover velocity: v_h = sqrt(T / (2*rho*A))
    3. Effective airspeed = cruise + headwind component
    4. Glauert's induced power ratio: 1 / (mu + sqrt(mu² + 1)), mu = v_eff / (2*v_h)
    5. Parasite drag power: 0.5 * rho * Cd * A_frontal * v_eff³
    """
    thrust   = total_mass_kg * _GRAVITY
    P_hover  = np.sqrt(thrust**3 / (2.0 * rho * _ROTOR_DISK_AREA_M2))
    v_h      = np.sqrt(thrust / (2.0 * rho * _ROTOR_DISK_AREA_M2))

    v_eff    = _CRUISE_SPEED_MS + wind_speed_ms * wind_headwind_fraction
    mu       = v_eff / (2.0 * v_h)
    P_induced  = P_hover / (mu + np.sqrt(mu**2 + 1.0))
    P_parasite = 0.5 * rho * _DRAG_COEFF * _FRONTAL_AREA_M2 * v_eff**3

    return P_induced + P_parasite


def _temperature_efficiency_penalty(temperature_c: np.ndarray) -> np.ndarray:
    """
    Li-ion capacity reduction at extreme temperatures (Peukert effect).
    Above 35°C or below 20°C, effective battery capacity decreases.
    """
    penalty = np.zeros_like(temperature_c)
    penalty += np.where(temperature_c > 35, (temperature_c - 35) * 0.008, 0.0)
    penalty += np.where(temperature_c < 20, (20 - temperature_c) * 0.006, 0.0)
    return penalty


def _compute_battery_pct(
    distance_km: np.ndarray,
    payload_kg: np.ndarray,
    wind_speed_ms: np.ndarray,
    humidity_pct: np.ndarray,
    temperature_c: np.ndarray,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Physics-based ground-truth battery consumption [%] with sensor noise.
    Used only during dataset generation for training.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    rho          = _air_density(temperature_c, humidity_pct)
    total_mass   = _DRONE_MASS_KG + payload_kg
    headwind_frac = rng.uniform(0.3, 1.0, len(distance_km))
    P_forward    = _forward_flight_power(total_mass, rho, wind_speed_ms, headwind_frac)

    flight_time_h = distance_km / (_CRUISE_SPEED_MS * 3.6)
    E_wh          = P_forward * flight_time_h
    batt_pct      = (E_wh / _BATTERY_CAPACITY_WH) * 100.0
    batt_pct     *= 1.0 + _temperature_efficiency_penalty(temperature_c)

    noise = rng.normal(0, 0.8, len(distance_km))
    return np.clip(batt_pct + noise, 2.0, 95.0)


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def _build_features(
    distance_km: np.ndarray,
    payload_kg: np.ndarray,
    wind_speed_ms: np.ndarray,
    humidity_pct: np.ndarray,
    temperature_c: np.ndarray,
) -> np.ndarray:
    """
    Construct the 9-feature matrix used by the Random Forest.

    Features
    --------
    0  distance_km        : flight distance
    1  payload_kg         : cargo mass
    2  wind_speed_ms      : wind speed
    3  humidity_pct       : relative humidity
    4  temperature_c      : ambient temperature
    5  dist_x_payload     : distance × payload (nonlinear interaction)
    6  wind_squared       : wind² (drag scales quadratically with speed)
    7  total_mass_kg      : drone + payload (drives hover power)
    8  air_density        : rho from temp & humidity (drives actuator disk power)
    """
    rho        = _air_density(temperature_c, humidity_pct)
    total_mass = _DRONE_MASS_KG + payload_kg
    return np.column_stack([
        distance_km,
        payload_kg,
        wind_speed_ms,
        humidity_pct,
        temperature_c,
        distance_km * payload_kg,
        wind_speed_ms ** 2,
        total_mass,
        rho,
    ])


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------

def train_model(n_samples: int = 2_000, verbose: bool = True) -> RandomForestRegressor:
    """
    Generate a physics-grounded dataset and train a Random Forest Regressor.

    Dataset generation uses actuator disk theory and Glauert's forward-flight
    model to produce realistic battery consumption values. The Random Forest
    then learns the nonlinear mapping, enabling fast inference during dispatch.

    Evaluation
    ----------
    Reports R², MAE, RMSE on a held-out 20% test set and 5-fold CV R².
    """
    rng = np.random.default_rng(42)

    # --- Realistic Hyderabad delivery scenario ranges ---
    distance_km   = rng.uniform(0.5,  30.0, n_samples)
    payload_kg    = rng.uniform(0.1,   5.5, n_samples)
    wind_speed_ms = rng.uniform(0.0,  14.0, n_samples)
    humidity_pct  = rng.uniform(30.0, 95.0, n_samples)
    temperature_c = rng.uniform(18.0, 44.0, n_samples)

    y = _compute_battery_pct(distance_km, payload_kg, wind_speed_ms, humidity_pct, temperature_c, rng)
    X = _build_features(distance_km, payload_kg, wind_speed_ms, humidity_pct, temperature_c)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    if verbose:
        y_pred = model.predict(X_test)
        cv     = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_r2  = cross_val_score(model, X_train, y_train, cv=cv, scoring="r2")
        print("[BatteryModel] Training complete")
        print(f"  R²   (test)  : {r2_score(y_test, y_pred):.4f}")
        print(f"  MAE  (test)  : {mean_absolute_error(y_test, y_pred):.3f} %")
        print(f"  RMSE (test)  : {np.sqrt(mean_squared_error(y_test, y_pred)):.3f} %")
        print(f"  CV R² (5-fold): {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")

    joblib.dump(model, MODEL_PATH)
    return model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_model() -> RandomForestRegressor:
    """Load persisted model from disk, training it first if absent."""
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return train_model()


def predict_battery_usage(
    distance_km: float,
    payload_kg: float,
    wind_speed: float,
    humidity: float,
    temperature: float,
) -> float:
    """
    Predict battery percentage consumed for a single flight.

    Parameters
    ----------
    distance_km  : planned route distance in kilometres
    payload_kg   : cargo weight in kilograms
    wind_speed   : wind speed in m/s (from weather service)
    humidity     : relative humidity in % (0–100)
    temperature  : ambient temperature in °C

    Returns
    -------
    float : predicted battery consumption [%], clamped to [4, 95]
    """
    model = load_model()
    X = _build_features(
        np.array([distance_km]),
        np.array([payload_kg]),
        np.array([wind_speed]),
        np.array([humidity]),
        np.array([temperature]),
    )
    prediction = model.predict(X)[0]
    return float(np.clip(prediction, 4.0, 95.0))

# if __name__ == "__main__":
#     train_model()