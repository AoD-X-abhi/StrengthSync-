import os
import joblib
import numpy as np
import pandas as pd

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

calorie_model_path = os.path.join(MODELS_DIR, "calorie_predictor.joblib")
hydration_model_path = os.path.join(MODELS_DIR, "hydration_estimator.joblib")
cardio_model_path = os.path.join(MODELS_DIR, "cardio_predictor.joblib")
recovery_model_path = os.path.join(MODELS_DIR, "recovery_predictor.joblib")

calorie_model = None
if os.path.exists(calorie_model_path):
    try:
        calorie_model = joblib.load(calorie_model_path)
        print("Calorie expenditure model loaded successfully.")
    except Exception as e:
        print(f"Warning: Failed to load calorie predictor model: {e}")

hydration_model = None
if os.path.exists(hydration_model_path):
    try:
        hydration_model = joblib.load(hydration_model_path)
        print("Hydration estimator model loaded successfully.")
    except Exception as e:
        print(f"Warning: Failed to load hydration estimator model: {e}")

cardio_model = None
if os.path.exists(cardio_model_path):
    try:
        cardio_model = joblib.load(cardio_model_path)
        print("Cardiovascular target model loaded successfully.")
    except Exception as e:
        print(f"Warning: Failed to load cardio predictor model: {e}")

recovery_model = None
if os.path.exists(recovery_model_path):
    try:
        recovery_model = joblib.load(recovery_model_path)
        print("Physiological recovery model loaded successfully.")
    except Exception as e:
        print(f"Warning: Failed to load recovery predictor model: {e}")



def predict_calories_expenditure(
    gender: str,
    age: int,
    height: float,
    weight: float,
    duration: float,
    heart_rate: float,
    body_temp: float
) -> float:
    """
    Predicts calorie burn based on exercise telemetry and biometrics.
    """
    if calorie_model is None:
        factor = 1.0
        if heart_rate > 150:
            factor = 12.0
        elif heart_rate > 120:
            factor = 8.0
        else:
            factor = 4.0
        return round(factor * weight * (duration / 60.0), 1)

    try:
        gender_encoded = 1 if gender.lower() == "male" else 0
        features = pd.DataFrame(
            [[gender_encoded, age, height, weight, duration, heart_rate, body_temp]],
            columns=["Gender", "Age", "Height", "Weight", "Duration", "Heart_Rate", "Body_Temp"]
        )
        prediction = calorie_model.predict(features)[0]
        return round(float(prediction), 1)
    except Exception as e:
        print(f"Error predicting calories: {e}")
        factor = 8.0 if heart_rate > 120 else 4.0
        return round(factor * weight * (duration / 60.0), 1)


def predict_hydration_requirement(
    age: int,
    gender: str,
    weight: float,
    activity_level: str,
    weather: str
) -> float:
    """
    Predicts optimal daily water intake in liters based on biometrics and environment.
    """
    if hydration_model is None:
        base = weight * 0.035
        if activity_level.lower() == "high":
            base += 1.0
        elif activity_level.lower() == "moderate":
            base += 0.5

        if weather.lower() == "hot":
            base += 0.8
        elif weather.lower() == "cold":
            base -= 0.3
        return round(max(1.5, base), 2)

    try:
        gender_encoded = 1 if gender.lower() == "male" else 0

        activity_map = {"low": 0, "moderate": 1, "high": 2}
        activity_encoded = activity_map.get(activity_level.lower(), 1)

        weather_map = {"cold": 0, "normal": 1, "warm": 1, "hot": 2}
        weather_encoded = weather_map.get(weather.lower(), 1)

        features = pd.DataFrame(
            [[age, gender_encoded, weight, activity_encoded, weather_encoded]],
            columns=["Age", "Gender", "Weight", "Physical Activity Level", "Weather"]
        )
        prediction = hydration_model.predict(features)[0]
        return round(float(prediction), 2)
    except Exception as e:
        print(f"Error predicting hydration requirement: {e}")
        base = weight * 0.035 + (0.5 if activity_level.lower() == "high" else 0.2)
        return round(max(1.5, base), 2)


def predict_average_bpm(
    age: int,
    gender: str,
    weight: float,
    height: float,
    bmi: float,
    experience_level: int,
    workout_type: str
) -> float:
    """
    Predicts average heart rate (Avg_BPM) response during workout based on biometrics.
    """
    if cardio_model is None:
        base = 146.0
        if workout_type.lower() == "hiit":
            base = 150.0
        elif workout_type.lower() == "cardio":
            base = 145.0
        elif workout_type.lower() == "strength":
            base = 135.0
        elif workout_type.lower() == "yoga":
            base = 110.0
        return round(base, 1)

    try:
        gender_encoded = 1 if gender.lower() == "male" else 0

        workout_map = {"cardio": 0, "hiit": 1, "strength": 2, "yoga": 3}
        workout_encoded = workout_map.get(workout_type.lower(), 2)

        features = pd.DataFrame(
            [[age, gender_encoded, weight, height, bmi, experience_level, workout_encoded]],
            columns=["Age", "Gender", "Weight", "Height", "BMI", "Experience_Level", "Workout_Type"]
        )
        prediction = cardio_model.predict(features)[0]
        return round(float(prediction), 1)
    except Exception as e:
        print(f"Error predicting average BPM: {e}")
        return 146.0


def predict_recovery_score(
    steps: int,
    active_minutes: int,
    sleep_hours: float,
    rhr: int,
    hrv: int
) -> float:
    """
    Predicts physiological recovery score (0 to 100) based on wearable telemetry.
    """
    if recovery_model is None:
        score = 50.0
        if 7.0 <= sleep_hours <= 9.0:
            score += 25.0
        elif sleep_hours < 6.0:
            score -= 15.0

        if hrv and hrv > 60:
            score += 15.0
        elif hrv and hrv < 40:
            score -= 10.0

        if rhr and rhr < 60:
            score += 10.0
        elif rhr and rhr > 75:
            score -= 10.0

        if 6000 <= steps <= 12000:
            score += 10.0
        elif steps > 18000:
            score -= 15.0
        return round(float(np.clip(score, 0.0, 100.0)), 1)

    try:
        features = pd.DataFrame(
            [[steps, active_minutes, sleep_hours, rhr, hrv]],
            columns=["Steps", "Active_Minutes", "Sleep_Hours", "RHR", "HRV"]
        )
        prediction = recovery_model.predict(features)[0]
        return round(float(prediction), 1)
    except Exception as e:
        print(f"Error predicting recovery score: {e}")
        return 65.0

