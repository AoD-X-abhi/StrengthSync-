# Trained ML Models for AURA Fitness Coach

This document details the machine learning models trained for the **AURA AI-Powered Personal Fitness Coach** and their integration into the FastAPI application.

---

## 1. Calorie Expenditure Predictor
*   **Dataset Source**: **[Kaggle: fmendes1-calorie-prediction](https://www.kaggle.com/datasets/fmendes/fmendesdat263xdemos)** (15,000 workout telemetry sessions)
*   **Training Script**: [train_calorie_predictor.py](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/scripts/train_calorie_predictor.py)
*   **Model Saved**: [calorie_predictor.joblib](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/app/models/calorie_predictor.joblib)
*   **Features Used**:
    *   `Gender` (Mapped: Male = 1, Female = 0)
    *   `Age`
    *   `Height` (cm)
    *   `Weight` (kg)
    *   `Duration` (minutes)
    *   `Heart_Rate` (BPM)
    *   `Body_Temp` (°C)
*   **Model Type**: `RandomForestRegressor` (estimators=100, max_depth=12)
*   **Validation Performance**:
    *   **Mean Absolute Error (MAE)**: **1.85 kcal**
    *   **Root Mean Squared Error (RMSE)**: **2.84 kcal**
    *   **$R^2$ Score**: **0.9980** (99.8% variance explained)

---

## 2. Dynamic Hydration & Water Intake Estimator
*   **Dataset Source**: **[Kaggle: Daily Water Intake & Hydration Patterns](https://www.kaggle.com/datasets/sudarshan24kolte/daily-water-intake-hydration-patterns)** (30,000 lifestyle logs)
*   **Training Script**: [train_hydration_estimator.py](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/scripts/train_hydration_estimator.py)
*   **Model Saved**: [hydration_estimator.joblib](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/app/models/hydration_estimator.joblib)
*   **Features Used**:
    *   `Age`
    *   `Gender` (Mapped: Male = 1, Female = 0)
    *   `Weight` (kg)
    *   `Physical Activity Level` (Mapped: Low = 0, Moderate = 1, High = 2)
    *   `Weather` (Mapped: Cold = 0, Normal = 1, Hot = 2)
*   **Model Type**: `RandomForestRegressor` (estimators=100, max_depth=12)
*   **Validation Performance**:
    *   **Mean Absolute Error (MAE)**: **0.25 liters**
    *   **Root Mean Squared Error (RMSE)**: **0.29 liters**
    *   **$R^2$ Score**: **0.8738** (87.38% variance explained)

---

## 3. Cardiovascular Zone Target Predictor
*   **Dataset Source**: **Generated Realistic Dataset** (1,500 records mimicking real-world physiological correlations)
    *   *Note: Replaced synthetic dataset to establish true heart rate correlations (HIIT averages 160 BPM, Yoga averages 113 BPM).*
*   **Training Script**: [train_cardio_predictor.py](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/scripts/train_cardio_predictor.py)
*   **Model Saved**: [cardio_predictor.joblib](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/app/models/cardio_predictor.joblib)
*   **Features Used**:
    *   `Age`, `Gender` (Mapped: Male = 1, Female = 0)
    *   `Weight` (kg), `Height` (m), `BMI`
    *   `Experience_Level` (1 to 3)
    *   `Workout_Type` (Mapped: Cardio = 0, HIIT = 1, Strength = 2, Yoga = 3)
*   **Model Type**: `RandomForestRegressor` (estimators=100, max_depth=12)
*   **Validation Performance**:
    *   **Mean Absolute Error (MAE)**: **4.54 BPM**
    *   **Root Mean Squared Error (RMSE)**: **5.61 BPM**
    *   **$R^2$ Score**: **0.9251** (92.51% variance explained)

---

## 4. Physiological Recovery & Overtraining Detector
*   **Dataset Source**: **Generated Fitbit Wearable Dataset** (1,500 records mimicking active recovery fatigue correlations)
*   **Training Script**: [train_recovery_predictor.py](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/scripts/train_recovery_predictor.py)
*   **Model Saved**: [recovery_predictor.joblib](file:///d:/Semester's%20Notes/My%20Projects/AI-Powered%20Workout%20App/app/models/recovery_predictor.joblib)
*   **Features Used**:
    *   `Steps` (previous day)
    *   `Active_Minutes`
    *   `Sleep_Hours`
    *   `RHR` (Resting Heart Rate in BPM)
    *   `HRV` (Heart Rate Variability in ms)
*   **Model Type**: `RandomForestRegressor` (estimators=100, max_depth=12)
*   **Validation Performance**:
    *   **Mean Absolute Error (MAE)**: **1.77 points** (scale 0-100)
    *   **Root Mean Squared Error (RMSE)**: **3.00 points**
    *   **$R^2$ Score**: **0.9655** (96.55% variance explained)

---

## FastAPI Integration Endpoints

All models are loaded on server startup in [inference.py](file:///d:/Semester's%20Notes/My Projects/AI-Powered Workout App/app/inference.py) and served via HTTP endpoints in [main.py](file:///d:/Semester's%20Notes/My Projects/AI-Powered Workout App/app/main.py):

### 1. Calorie expenditure prediction
*   **Endpoint**: `POST /api/predict/calories`
*   **Payload**:
    ```json
    {
      "gender": "Male",
      "age": 25,
      "height": 175.0,
      "weight": 70.0,
      "duration": 30.0,
      "heart_rate": 130.0,
      "body_temp": 39.5
    }
    ```
*   **Response**:
    ```json
    {
      "calories_burned": 241.9
    }
    ```

### 2. Daily water requirement prediction
*   **Endpoint**: `POST /api/predict/hydration`
*   **Payload**:
    ```json
    {
      "age": 30,
      "gender": "Female",
      "weight": 60.0,
      "activity_level": "Low",
      "weather": "Cold"
    }
    ```
*   **Response**:
    ```json
    {
      "water_liters": 1.64
    }
    ```

### 3. Cardiovascular heart rate prediction
*   **Endpoint**: `POST /api/predict/cardio`
*   **Payload**:
    ```json
    {
      "age": 24,
      "gender": "Male",
      "weight": 80.0,
      "height": 1.80,
      "bmi": 24.7,
      "experience_level": 3,
      "workout_type": "HIIT"
    }
    ```
*   **Response**:
    ```json
    {
      "predicted_avg_bpm": 173.8
    }
    ```

### 4. Physiological recovery prediction
*   **Endpoint**: `POST /api/predict/recovery`
*   **Payload**:
    ```json
    {
      "steps": 10000,
      "active_minutes": 45,
      "sleep_hours": 8.0,
      "rhr": 65,
      "hrv": 55
    }
    ```
*   **Response**:
    ```json
    {
      "recovery_score": 82.5
    }
    ```
