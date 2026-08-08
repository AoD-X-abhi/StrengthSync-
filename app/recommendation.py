import os
import joblib
import numpy as np
from datetime import datetime, timedelta
from app.models import WorkoutSession, FatigueLog
from sqlalchemy.orm import Session

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "recommendation_model.joblib")

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print(f"ML Recommendation Model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        print(f"Warning: Failed to load ML model: {e}")
else:
    print("Warning: ML model not found. Using rule-based fallback.")


def calculate_acwr_for_user(user_id: int, db: Session) -> tuple[float, str]:
    today = datetime.utcnow().date()
    daily_loads = {}
    for i in range(28):
        day = today - timedelta(days=i)
        daily_loads[day] = 0.0

    start_date = datetime.combine(today - timedelta(days=27), datetime.min.time())
    workouts = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.date >= start_date
    ).all()

    for w in workouts:
        w_date = w.date.date()
        if w_date in daily_loads:
            if w.weight_load and w.weight_load > 0:
                load = w.sets * w.reps * w.weight_load
            else:
                load = w.duration_minutes * 10.0
            daily_loads[w_date] += load

    acute_sum = sum(daily_loads[today - timedelta(days=i)] for i in range(7))
    acute_workload = acute_sum / 7.0

    chronic_sum = sum(daily_loads.values())
    chronic_workload = chronic_sum / 28.0

    if chronic_workload <= 0:
        acwr = 1.0
    else:
        acwr = round(acute_workload / chronic_workload, 2)

    if acwr > 1.5:
        risk = "High"
    elif acwr > 1.2:
        risk = "Medium"
    else:
        risk = "Low"

    return acwr, risk


def calculate_acwr_for_day(user_id: int, target_day, db: Session) -> float:
    daily_loads = {}
    for i in range(28):
        day = target_day - timedelta(days=i)
        daily_loads[day] = 0.0

    start_date = datetime.combine(target_day - timedelta(days=27), datetime.min.time())
    workouts = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= datetime.combine(target_day, datetime.max.time())
    ).all()

    for w in workouts:
        w_date = w.date.date()
        if w_date in daily_loads:
            if w.weight_load and w.weight_load > 0:
                load = w.sets * w.reps * w.weight_load
            else:
                load = w.duration_minutes * 10.0
            daily_loads[w_date] += load

    acute_sum = sum(daily_loads[target_day - timedelta(days=i)] for i in range(7))
    acute_workload = acute_sum / 7.0

    chronic_sum = sum(daily_loads.values())
    chronic_workload = chronic_sum / 28.0

    if chronic_workload <= 0:
        return 1.0
    return round(acute_workload / chronic_workload, 2)


def get_rule_based_recommendation(fitness_objective: str, age: int, daily_activity_level: str) -> str:
    if fitness_objective == "Muscle Gain":
        return "Strength"
    elif fitness_objective == "Weight Loss":
        return "HIIT"
    elif fitness_objective == "Endurance":
        return "Cardio"
    elif fitness_objective == "General Health":
        if age > 50 or daily_activity_level == "Sedentary":
            return "Yoga"
        else:
            return "Strength"
    return "Strength"


def predict_workout_recommendation(user, db: Session = None) -> dict:
    """
    Predicts the optimal workout type for a user.
    Uses the trained Random Forest model if available, otherwise falls back to heuristics.
    """
    gender_encoded = 1 if user.gender == "Male" else 0
    height_m = (user.height / 100.0) if user.height else 1.70
    weight_kg = user.weight if user.weight else 70.0
    bmi = user.bmi if user.bmi else 24.0
    age = user.age if user.age else 25

    freq = 3.5
    if user.daily_activity_level == "Sedentary":
        freq = 1.5
    elif user.daily_activity_level == "Very Active":
        freq = 5.0

    exp = 2.0

    method = "Rule-based Engine"
    predicted_type = None

    global model
    if model is None and os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
        except:
            pass

    if model is not None:
        try:
            features = np.array([[age, gender_encoded, weight_kg, height_m, bmi, freq, exp]])
            predicted_type = model.predict(features)[0]
            method = "Random Forest ML Model"
        except Exception as e:
            print(f"Error during ML prediction, falling back: {e}")
            predicted_type = get_rule_based_recommendation(user.fitness_objective, age, user.daily_activity_level)
    else:
        predicted_type = get_rule_based_recommendation(user.fitness_objective, age, user.daily_activity_level)

    routines = {
        "Strength": {
            "title": "Hypertrophy & Strength Conditioning",
            "routine": "Barbell Squats (3 sets x 8 reps), Bench Press (3 sets x 10 reps), Push-ups (3 sets x max reps)",
            "description": "Focuses on mechanical muscle tension and progressive overload to build lean mass."
        },
        "Cardio": {
            "title": "Aerobic Capacity Conditioning",
            "routine": "Steady-state jogging (30 mins at 65% max heart rate), Lunges (3 sets x 12 reps)",
            "description": "Aims to improve cardiovascular efficiency, stroke volume, and general aerobic endurance."
        },
        "HIIT": {
            "title": "High-Intensity Interval Training",
            "routine": "Burpees (40s work / 20s rest), Mountain Climbers (40s / 20s), Pushups (40s / 20s) x 4 rounds",
            "description": "Designed to maximize excess post-exercise oxygen consumption (EPOC) and optimize calorie expenditure."
        },
        "Yoga": {
            "title": "Mobility & Active Recovery Plan",
            "routine": "Deep stretching poses (Cobra, Downward Dog, Warrior Pose), Plank hold (3 sets x 30 seconds)",
            "description": "Focuses on joint mobility, myofascial release, and parasympathetic nervous system recovery."
        }
    }

    explanation = f"Using the {method}, we analyzed your profile. "
    explanation += f"Based on your biometrics (Age: {age}, BMI: {bmi:.1f}) and goal ({user.fitness_objective or 'General Health'}), "

    if predicted_type == "Strength":
        explanation += "your body profile is optimized for resistance training and muscle-mass building."
    elif predicted_type == "Cardio":
        explanation += "your plan is optimized to increase cardiovascular efficiency and aerobic capacity."
    elif predicted_type == "HIIT":
        explanation += "your plan targets rapid oxygen consumption and high calorie output."
    elif predicted_type == "Yoga":
        explanation += "your plan is focused on active recovery, joint length, and mobility."

    if db is not None:
        try:
            acwr, risk = calculate_acwr_for_user(user.id, db)
            latest_fatigue = db.query(FatigueLog).filter(FatigueLog.user_id == user.id).order_by(FatigueLog.id.desc()).first()
            soreness = latest_fatigue.soreness if latest_fatigue else 0
            sleep = latest_fatigue.sleep_hours if latest_fatigue else 8.0

            if risk == "High":
                predicted_type = "Yoga"
                explanation += f" <br><br><strong style='color:var(--neon-red);'><i class='fa-solid fa-triangle-exclamation'></i> Fatigue Override:</strong> Your rolling ACWR training ratio is {acwr:.2f} (High Risk) and soreness is {soreness}/10. To prevent soft-tissue strain, the XAI engine has downgraded your routine to Active Recovery / Yoga."
            elif risk == "Medium":
                explanation += f" <br><br><strong style='color:var(--neon-purple);'><i class='fa-solid fa-circle-exclamation'></i> Fatigue Warning:</strong> Your rolling ACWR is {acwr:.2f} (Medium Risk) with {soreness}/10 soreness. We recommend performing today's movements at 70% intensity to protect joint integrity."
            else:
                explanation += f" <br><br><strong style='color:var(--neon-green);'><i class='fa-solid fa-circle-check'></i> Fatigue Status:</strong> Your rolling ACWR ratio is {acwr:.2f} (Low Risk, Sweet Spot) with {sleep}h of sleep, indicating optimal recovery. You are clear for progressive overload."
        except Exception as e:
            print(f"XAI fatigue check error: {e}")

    routine_data = routines.get(predicted_type, routines["Strength"])

    injury_lock = False
    injury_note = ""
    if user.structural_injuries and user.structural_injuries.strip() != "":
        injuries_lower = user.structural_injuries.lower()

        if "knee" in injuries_lower:
            injury_lock = True
            routine_data["routine"] = routine_data["routine"].replace("Barbell Squats", "Leg Extensions (Low Load)").replace("Lunges", "Step-ups (Low Load)")
            injury_note = "Knee pain detected: Swapped heavy compound squatting/lunging for low-shear movements."

        if "back" in injuries_lower or "spine" in injuries_lower or "lumbar" in injuries_lower:
            injury_lock = True
            routine_data["routine"] = routine_data["routine"].replace("Barbell Squats", "Leg Press (Neutral spine)").replace("Deadlift", "Glute Bridges")
            injury_note = "Lower back pain detected: Swapped spine-loading movements for core-stabilizing and back-supported exercises."

        if "shoulder" in injuries_lower or "rotator" in injuries_lower:
            injury_lock = True
            routine_data["routine"] = routine_data["routine"].replace("Bench Press", "Incline Dumbbell Flyes (Low weight)").replace("Push-ups", "Plank Hold")
            injury_note = "Shoulder pain detected: Substituted heavy overhead or pressing movements to avoid shoulder impingement."

    return {
        "workout_type": predicted_type,
        "title": routine_data["title"],
        "routine": routine_data["routine"],
        "description": routine_data["description"],
        "explanation": explanation,
        "prediction_method": method,
        "injury_lock": injury_lock,
        "injury_note": injury_note
    }
