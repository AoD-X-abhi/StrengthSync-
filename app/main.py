from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import io
import re
import google.generativeai as genai

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip()
    except Exception as e:
        print(f"Warning: Failed to load .env file: {e}")


from app.database import engine, get_db, Base
from app.models import User, WorkoutSession, NutritionLog, FatigueLog, Goal, UserBadge, ProgressPhoto
from app.recommendation import (
    predict_workout_recommendation,
    calculate_acwr_for_user,
    calculate_acwr_for_day
)
from app.inference import (
    predict_calories_expenditure,
    predict_hydration_requirement,
    predict_average_bpm,
    predict_recovery_score
)
from pydantic import BaseModel, EmailStr
import bcrypt

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Personal Fitness Coach API")


class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    age: int
    gender: str
    height: float
    weight: float
    fitness_objective: str
    structural_injuries: str = ""
    daily_activity_level: str
    dietary_preferences: str = ""

class WorkoutLogCreate(BaseModel):
    exercise_name: str
    sets: int
    reps: int
    weight_load: float
    duration_minutes: int

class NutritionLogCreate(BaseModel):
    calories: int
    protein: float
    carbs: float
    fats: float
    water_liters: float

class FatigueLogCreate(BaseModel):
    soreness: int
    sleep_hours: float
    hrv: int = None


class ChatRequest(BaseModel):
    message: str


class CaloriePredictionRequest(BaseModel):
    gender: str
    age: int
    height: float
    weight: float
    duration: float
    heart_rate: float
    body_temp: float


class HydrationPredictionRequest(BaseModel):
    age: int
    gender: str
    weight: float
    activity_level: str
    weather: str


class CardioPredictionRequest(BaseModel):
    age: int
    gender: str
    weight: float
    height: float
    bmi: float
    experience_level: int
    workout_type: str


class RecoveryPredictionRequest(BaseModel):
    steps: int
    active_minutes: int
    sleep_hours: float
    rhr: int
    hrv: int


class GoalCreateRequest(BaseModel):
    goal_name: str
    target_value: float
    current_value: float = None


class GoalUpdateRequest(BaseModel):
    current_value: float




class ProgressPhotoCreateRequest(BaseModel):
    photo_url: str
    weight: float = None




class DietRequest(BaseModel):
    meal_type: str
    workout_relation: str
    notes: str = ""


def get_user_from_request(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please register or log in."
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    return user



@app.post("/api/register")
def register(user_data: UserRegister, response: Response, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    hashed_pwd = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(email=user_data.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response.set_cookie(key="user_id", value=str(new_user.id), samesite="lax")
    return {"message": "Registration successful", "user_id": new_user.id, "email": new_user.email}


@app.post("/api/login")
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not bcrypt.checkpw(user_data.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password."
        )

    response.set_cookie(key="user_id", value=str(user.id), samesite="lax")
    return {"message": "Login successful", "user_id": user.id, "email": user.email}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("user_id")
    return {"message": "Logged out successfully"}


@app.get("/api/me")
def get_me(user: User = Depends(get_user_from_request)):
    return {
        "id": user.id,
        "email": user.email,
        "age": user.age,
        "gender": user.gender,
        "height": user.height,
        "weight": user.weight,
        "bmi": user.bmi,
        "fitness_objective": user.fitness_objective,
        "structural_injuries": user.structural_injuries,
        "daily_activity_level": user.daily_activity_level,
        "dietary_preferences": user.dietary_preferences
    }


@app.post("/api/profile/update")
def update_profile(profile_data: ProfileUpdate, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    user.age = profile_data.age
    user.gender = profile_data.gender
    user.height = profile_data.height
    user.weight = profile_data.weight
    user.fitness_objective = profile_data.fitness_objective
    user.structural_injuries = profile_data.structural_injuries
    user.daily_activity_level = profile_data.daily_activity_level
    user.dietary_preferences = profile_data.dietary_preferences

    if user.height and user.weight:
        height_m = user.height / 100.0
        user.bmi = round(user.weight / (height_m ** 2), 2)

    db.commit()
    db.refresh(user)
    return {"message": "Profile updated successfully", "bmi": user.bmi}


@app.post("/api/workouts/log")
def log_workout(workout_data: WorkoutLogCreate, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    session = WorkoutSession(
        user_id=user.id,
        exercise_name=workout_data.exercise_name,
        sets=workout_data.sets,
        reps=workout_data.reps,
        weight_load=workout_data.weight_load,
        duration_minutes=workout_data.duration_minutes
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"message": "Workout session logged successfully", "id": session.id}


@app.get("/api/workouts")
def get_workouts(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    sessions = db.query(WorkoutSession).filter(WorkoutSession.user_id == user.id).order_by(WorkoutSession.date.desc()).all()
    return [{
        "id": s.id,
        "date": s.date.isoformat(),
        "exercise_name": s.exercise_name,
        "sets": s.sets,
        "reps": s.reps,
        "weight_load": s.weight_load,
        "duration_minutes": s.duration_minutes
    } for s in sessions]


@app.post("/api/nutrition/log")
def log_nutrition(nutrition_data: NutritionLogCreate, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    log = NutritionLog(
        user_id=user.id,
        calories=nutrition_data.calories,
        protein=nutrition_data.protein,
        carbs=nutrition_data.carbs,
        fats=nutrition_data.fats,
        water_liters=nutrition_data.water_liters
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Nutrition logged successfully", "id": log.id}


@app.get("/api/nutrition")
def get_nutrition(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    logs = db.query(NutritionLog).filter(NutritionLog.user_id == user.id).order_by(NutritionLog.date.desc()).all()
    return [{
        "id": l.id,
        "date": l.date.isoformat(),
        "calories": l.calories,
        "protein": l.protein,
        "carbs": l.carbs,
        "fats": l.fats,
        "water_liters": l.water_liters
    } for l in logs]




@app.post("/api/fatigue/log")
def log_fatigue(fatigue_data: FatigueLogCreate, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    acwr, risk = calculate_acwr_for_user(user.id, db)

    if fatigue_data.soreness >= 8 or fatigue_data.sleep_hours < 5.0:
        risk = "High"
    elif fatigue_data.soreness >= 6 or fatigue_data.sleep_hours < 6.5:
        if risk == "Low":
            risk = "Medium"

    log = FatigueLog(
        user_id=user.id,
        soreness=fatigue_data.soreness,
        sleep_hours=fatigue_data.sleep_hours,
        hrv=fatigue_data.hrv,
        injury_risk_tier=risk
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Fatigue log saved successfully", "id": log.id, "injury_risk_tier": risk, "acwr": acwr}


@app.get("/api/analytics/progress")
def get_progress_analytics(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    daily_loads = []
    acwr_values = []
    labels = []

    for i in reversed(range(14)):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%b %d"))

        start_dt = datetime.combine(day, datetime.min.time())
        end_dt = datetime.combine(day, datetime.max.time())
        workouts = db.query(WorkoutSession).filter(
            WorkoutSession.user_id == user.id,
            WorkoutSession.date >= start_dt,
            WorkoutSession.date <= end_dt
        ).all()

        load = 0.0
        for w in workouts:
            if w.weight_load and w.weight_load > 0:
                load += w.sets * w.reps * w.weight_load
            else:
                load += w.duration_minutes * 10.0
        daily_loads.append(load)

        acwr_val = calculate_acwr_for_day(user.id, day, db)
        acwr_values.append(acwr_val)

    squat_logs = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user.id,
        WorkoutSession.exercise_name.like("%Squat%")
    ).order_by(WorkoutSession.date.asc()).all()

    pushup_logs = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user.id,
        WorkoutSession.exercise_name.like("%Push-up%") | WorkoutSession.exercise_name.like("%Press%")
    ).order_by(WorkoutSession.date.asc()).all()

    def extract_1rm_history(logs):
        history = []
        dates = []
        for l in logs:
            w = l.weight_load if (l.weight_load and l.weight_load > 0) else (user.weight * 0.5 if user.weight else 35.0)
            one_rm = round(w * (1.0 + l.reps / 30.0), 1)
            history.append(one_rm)
            dates.append(l.date.strftime("%b %d"))
        return dates, history

    squat_dates, squat_1rm = extract_1rm_history(squat_logs)
    pushup_dates, pushup_1rm = extract_1rm_history(pushup_logs)

    if not squat_1rm:
        squat_dates = [(today - timedelta(days=d)).strftime("%b %d") for d in reversed(range(0, 15, 3))]
        base_squat = 50.0 if user.gender == "Male" else 30.0
        squat_1rm = [base_squat + i * 2.0 for i in range(len(squat_dates))]

    if not pushup_1rm:
        pushup_dates = squat_dates
        base_pushup = 40.0 if user.gender == "Male" else 20.0
        pushup_1rm = [base_pushup + i * 1.5 for i in range(len(pushup_dates))]

    def generate_forecast(history, steps=4):
        n = len(history)
        if n < 2:
            rate = 1.02
            forecast = [round(history[-1] * (rate ** (i + 1)), 1) for i in range(steps)]
            return forecast

        x = list(range(n))
        y = history
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        den = sum((x[i] - x_mean) ** 2 for i in range(n))

        m = num / den if den != 0 else 0.0
        c = y_mean - m * x_mean

        forecast = []
        for i in range(1, steps + 1):
            val = m * (n - 1 + i) + c
            val = max(val, history[-1])
            val = min(val, history[-1] * 1.25)
            forecast.append(round(val, 1))
        return forecast

    squat_forecast = generate_forecast(squat_1rm)
    pushup_forecast = generate_forecast(pushup_1rm)

    forecast_labels = ["Week 1", "Week 2", "Week 3", "Week 4"]
    current_acwr, current_risk = calculate_acwr_for_user(user.id, db)

    return {
        "workload_labels": labels,
        "daily_loads": daily_loads,
        "acwr_values": acwr_values,
        "squat_dates": squat_dates,
        "squat_1rm": squat_1rm,
        "squat_forecast_labels": forecast_labels,
        "squat_forecast": squat_forecast,
        "pushup_dates": pushup_dates,
        "pushup_1rm": pushup_1rm,
        "pushup_forecast": pushup_forecast,
        "current_acwr": current_acwr,
        "current_risk": current_risk
    }


@app.get("/api/recommendations/workout")
def get_workout_rec(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    return predict_workout_recommendation(user, db)


@app.post("/api/chat")
def chat_assistant(chat_data: ChatRequest, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    acwr, risk = calculate_acwr_for_user(user.id, db)
    latest_fatigue = db.query(FatigueLog).filter(FatigueLog.user_id == user.id).order_by(FatigueLog.id.desc()).first()
    soreness = latest_fatigue.soreness if latest_fatigue else 0
    sleep = latest_fatigue.sleep_hours if latest_fatigue else 8.0

    target_tdee = 2000
    protein_g = 140
    carbs_g = 220
    fats_g = 65
    if user.height and user.weight and user.age:
        bmr = (10 * user.weight) + (6.25 * user.height) - (5 * user.age)
        bmr = bmr + 5 if user.gender == "Male" else bmr - 161
        active_mult = 1.2
        if user.daily_activity_level == "Moderately Active":
            active_mult = 1.4
        elif user.daily_activity_level == "Very Active":
            active_mult = 1.7
        target_tdee = round(bmr * active_mult)
        if user.fitness_objective == "Muscle Gain":
            target_tdee += 300
            protein_g = round(2.0 * user.weight)
            fats_g = round((target_tdee * 0.25) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)
        elif user.fitness_objective == "Weight Loss":
            target_tdee -= 400
            protein_g = round(2.2 * user.weight)
            fats_g = round((target_tdee * 0.20) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)
        else:
            protein_g = round(1.6 * user.weight)
            fats_g = round((target_tdee * 0.25) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)

    prompt_context = f"""
    You are StrengthSync, an elite AI Personal Fitness Coach and Sports Science Expert.
    You have access to the user's real-time biometric and physiological state:
    - User Profile: Age {user.age}, Weight {user.weight}kg, Height {user.height}cm, Gender {user.gender}.
    - Fitness Objective: {user.fitness_objective or 'General Health'}.
    - Structural Injuries / Joint Pain: {user.structural_injuries or 'None reported'}.
    - Current Recovery Metrics: Rolling ACWR is {acwr} (Fatigue Risk: {risk}), Soreness is {soreness}/10, Sleep is {sleep} hours.
    - Calorie & Macronutrient Targets: TDEE {target_tdee} kcal, Protein {protein_g}g, Carbs {carbs_g}g, Fats {fats_g}g.

    Keep your response motivating, concise, and scientifically accurate. Restrict answers to 3-4 sentences max.
    If the user asks about their macros, diet, or injuries, refer directly to the targets and metrics listed above.
    """

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content([prompt_context, chat_data.message])
            except Exception as inner_e:
                print(f"Primary gemini-1.5-flash model failed ({inner_e}), trying gemini-pro fallback...")
                model = genai.GenerativeModel("gemini-pro")
                response = model.generate_content([prompt_context, chat_data.message])
            return {"response": response.text}
        except Exception as e:
            print(f"Gemini API execution error: {e}")
            pass

    msg_lower = chat_data.message.lower()
    if "macro" in msg_lower or "diet" in msg_lower or "nutrition" in msg_lower or "protein" in msg_lower or "eat" in msg_lower:
        reply = f"Based on your profile (Goal: {user.fitness_objective or 'General Health'}), your target calorie intake is TDEE of {target_tdee} kcal. We suggest taking {protein_g}g of Protein, {carbs_g}g of Carbs, and {fats_g}g of Fats daily."
    elif "injury" in msg_lower or "pain" in msg_lower or "sore" in msg_lower or "knee" in msg_lower or "back" in msg_lower or "shoulder" in msg_lower:
        reply = f"I see you reported: '{user.structural_injuries or 'no active injuries'}'. Your current Fatigue Risk Tier is {risk} (ACWR: {acwr}). I recommend avoiding heavy compound loads and substituting joint-straining exercises."
    elif "squat" in msg_lower or "bench" in msg_lower or "pushup" in msg_lower or "exercise" in msg_lower:
        reply = "For your Squat and Press training, prioritize technique and control. Focus on maintaining a neutral spine and controlled eccentric phases. Let me know if you need specific form tips!"
    else:
        reply = f"Hello! As your AI Coach, I'm analyzing your goals ({user.fitness_objective or 'General Health'}). Your current training workload ratio is {acwr} ({risk} risk). Feel free to ask me about your macros, active recovery, or injury overrides!"

    reply += "\n\n[StrengthSync Chat is running in simulation mode. Set the GEMINI_API_KEY environment variable to enable live Gemini LLM coaching.]"
    return {"response": reply}


@app.get("/api/dashboard/summary")
def get_dashboard_summary(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    week_ago = datetime.utcnow() - timedelta(days=7)
    workouts_this_week = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user.id,
        WorkoutSession.date >= week_ago
    ).count()

    total_minutes = db.query(func.sum(WorkoutSession.duration_minutes)).filter(
        WorkoutSession.user_id == user.id
    ).scalar() or 0

    latest_nutrition = db.query(NutritionLog).filter(
        NutritionLog.user_id == user.id
    ).order_by(NutritionLog.id.desc()).first()

    current_calories = latest_nutrition.calories if latest_nutrition else 0

    latest_fatigue = db.query(FatigueLog).filter(
        FatigueLog.user_id == user.id
    ).order_by(FatigueLog.id.desc()).first()

    injury_risk = latest_fatigue.injury_risk_tier if latest_fatigue else "Low"
    soreness = latest_fatigue.soreness if latest_fatigue else 0
    sleep = latest_fatigue.sleep_hours if latest_fatigue else 8.0

    target_tdee = 2000
    protein_g = 140
    carbs_g = 220
    fats_g = 65

    if user.height and user.weight and user.age:
        bmr = (10 * user.weight) + (6.25 * user.height) - (5 * user.age)
        bmr = bmr + 5 if user.gender == "Male" else bmr - 161

        active_mult = 1.2
        if user.daily_activity_level == "Moderately Active":
            active_mult = 1.4
        elif user.daily_activity_level == "Very Active":
            active_mult = 1.7

        target_tdee = round(bmr * active_mult)

        if user.fitness_objective == "Muscle Gain":
            target_tdee += 300
            protein_g = round(2.0 * user.weight)
            fats_g = round((target_tdee * 0.25) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)
        elif user.fitness_objective == "Weight Loss":
            target_tdee -= 400
            protein_g = round(2.2 * user.weight)
            fats_g = round((target_tdee * 0.20) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)
        else:
            protein_g = round(1.6 * user.weight)
            fats_g = round((target_tdee * 0.25) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)

    return {
        "workouts_this_week": workouts_this_week,
        "total_minutes": total_minutes,
        "current_calories": current_calories,
        "injury_risk": injury_risk,
        "soreness": soreness,
        "sleep": sleep,
        "bmi": user.bmi or 0.0,
        "fitness_objective": user.fitness_objective or "Not set",
        "target_tdee": target_tdee,
        "target_protein": protein_g,
        "target_carbs": carbs_g,
        "target_fats": fats_g
    }


@app.post("/api/predict/calories")
def predict_calories(data: CaloriePredictionRequest, user: User = Depends(get_user_from_request)):
    calories_burned = predict_calories_expenditure(
        gender=data.gender,
        age=data.age,
        height=data.height,
        weight=data.weight,
        duration=data.duration,
        heart_rate=data.heart_rate,
        body_temp=data.body_temp
    )
    return {"calories_burned": calories_burned}


@app.post("/api/predict/hydration")
def predict_hydration(data: HydrationPredictionRequest, user: User = Depends(get_user_from_request)):
    water_liters = predict_hydration_requirement(
        age=data.age,
        gender=data.gender,
        weight=data.weight,
        activity_level=data.activity_level,
        weather=data.weather
    )
    return {"water_liters": water_liters}


@app.post("/api/predict/cardio")
def predict_cardio(data: CardioPredictionRequest, user: User = Depends(get_user_from_request)):
    avg_bpm = predict_average_bpm(
        age=data.age,
        gender=data.gender,
        weight=data.weight,
        height=data.height,
        bmi=data.bmi,
        experience_level=data.experience_level,
        workout_type=data.workout_type
    )
    return {"predicted_avg_bpm": avg_bpm}


@app.post("/api/predict/recovery")
def predict_recovery(data: RecoveryPredictionRequest, user: User = Depends(get_user_from_request)):
    score = predict_recovery_score(
        steps=data.steps,
        active_minutes=data.active_minutes,
        sleep_hours=data.sleep_hours,
        rhr=data.rhr,
        hrv=data.hrv
    )
    return {"recovery_score": score}


@app.get("/api/goals")
def get_goals(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    user_goals = db.query(Goal).filter(Goal.user_id == user.id).all()
    if not user_goals:
        default_goals = [
            ("Daily Steps", 10000.0, 0.0),
            ("Daily Water Intake (L)", 3.0, 0.0),
            ("Weekly Workouts", 4.0, 0.0),
            ("Sleep Hours", 8.0, 0.0)
        ]
        for name, target, current in default_goals:
            g = Goal(user_id=user.id, goal_name=name, target_value=target, current_value=current)
            db.add(g)
        db.commit()
        user_goals = db.query(Goal).filter(Goal.user_id == user.id).all()
    return [{"id": g.id, "goal_name": g.goal_name, "target_value": g.target_value, "current_value": g.current_value, "status": g.status} for g in user_goals]


@app.post("/api/goals")
def create_or_update_goal(data: GoalCreateRequest, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    existing = db.query(Goal).filter(Goal.user_id == user.id, Goal.goal_name == data.goal_name).first()
    if existing:
        existing.target_value = data.target_value
        if data.current_value is not None:
            existing.current_value = data.current_value
        existing.status = "completed" if existing.current_value >= existing.target_value else "active"
        g = existing
    else:
        curr = data.current_value if data.current_value is not None else 0.0
        status_str = "completed" if curr >= data.target_value else "active"
        g = Goal(user_id=user.id, goal_name=data.goal_name, target_value=data.target_value, current_value=curr, status=status_str)
        db.add(g)
    db.commit()
    db.refresh(g)
    return {"message": "Goal updated", "id": g.id, "goal_name": g.goal_name, "status": g.status}


@app.post("/api/goals/{goal_id}/progress")
def update_goal_progress(goal_id: int, data: GoalUpdateRequest, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    g = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    g.current_value = data.current_value
    g.status = "completed" if g.current_value >= g.target_value else "active"
    db.commit()
    return {"message": "Progress updated", "goal_name": g.goal_name, "current_value": g.current_value, "status": g.status}




@app.get("/api/achievements")
def get_achievements(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    badges = db.query(UserBadge).filter(UserBadge.user_id == user.id).all()
    workouts_count = db.query(WorkoutSession).filter(WorkoutSession.user_id == user.id).count()
    water_count = db.query(NutritionLog).filter(NutritionLog.user_id == user.id, NutritionLog.water_liters >= 3.0).count()

    unlocked_names = [b.badge_name for b in badges]
    new_badges = []

    if workouts_count >= 1 and "First Step" not in unlocked_names:
        b = UserBadge(user_id=user.id, badge_name="First Step", badge_description="Logged your first workout session!")
        db.add(b)
        new_badges.append(b)

    if workouts_count >= 5 and "Century Lifer" not in unlocked_names:
        b = UserBadge(user_id=user.id, badge_name="Century Lifer", badge_description="Completed 5 total workout sessions.")
        db.add(b)
        new_badges.append(b)

    if water_count >= 3 and "Hydration Master" not in unlocked_names:
        b = UserBadge(user_id=user.id, badge_name="Hydration Master", badge_description="Drank 3.0L+ of water on 3 separate days.")
        db.add(b)
        new_badges.append(b)

    if new_badges:
        db.commit()
        badges = db.query(UserBadge).filter(UserBadge.user_id == user.id).all()

    sessions = db.query(WorkoutSession).filter(WorkoutSession.user_id == user.id).order_by(WorkoutSession.date.desc()).all()
    workout_dates = sorted(list({s.date.date() for s in sessions}), reverse=True)

    streak = 0
    today_completed = False
    if workout_dates:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        if workout_dates[0] == today:
            today_completed = True

        if workout_dates[0] in (today, yesterday):
            streak = 1
            current_date = workout_dates[0]
            for next_date in workout_dates[1:]:
                if current_date - next_date == timedelta(days=1):
                    streak += 1
                    current_date = next_date
                elif current_date - next_date > timedelta(days=1):
                    break

    return {
        "streak_days": streak,
        "today_completed": today_completed,
        "total_workouts": workouts_count,
        "badges": [{"badge_name": b.badge_name, "badge_description": b.badge_description, "unlocked_at": b.date.strftime("%Y-%m-%d")} for b in badges]
    }


@app.get("/api/photos")
def get_photos(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    photos = db.query(ProgressPhoto).filter(ProgressPhoto.user_id == user.id).order_by(ProgressPhoto.date.desc()).all()
    return [{"id": p.id, "date": p.date.strftime("%b %d, %Y"), "photo_url": p.photo_url, "weight": p.weight} for p in photos]


@app.post("/api/photos")
def add_photo(data: ProgressPhotoCreateRequest, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    photo = ProgressPhoto(
        user_id=user.id,
        photo_url=data.photo_url,
        weight=data.weight if data.weight else user.weight
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {"message": "Photo uploaded successfully", "id": photo.id, "date": photo.date.strftime("%b %d, %Y")}


@app.get("/api/profile/assessment")
def get_fitness_assessment(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    workouts_count = db.query(WorkoutSession).filter(WorkoutSession.user_id == user.id).count()

    fitness_level = "Beginner"
    if workouts_count >= 15:
        fitness_level = "Advanced"
    elif workouts_count >= 5:
        fitness_level = "Intermediate"

    bmi_status = "Normal"
    if user.bmi:
        if user.bmi > 25:
            bmi_status = "Overweight"
        elif user.bmi < 18.5:
            bmi_status = "Underweight"

    rec_route = predict_workout_recommendation(user, db)

    assessment = {
        "fitness_level": fitness_level,
        "bmi_status": bmi_status,
        "workouts_logged": workouts_count,
        "recommended_plan": rec_route["title"],
        "recommended_plan_desc": rec_route["description"],
        "biomechanical_feedback": rec_route["injury_note"] if rec_route["injury_lock"] else "No structural joint limitations reported. Clear for compound training."
    }
    return assessment


@app.get("/api/weather/recommendation")
def get_weather_recommendation(weather: str = "Sunny", user: User = Depends(get_user_from_request)):
    w_lower = weather.lower()
    if "rain" in w_lower or "snow" in w_lower or "storm" in w_lower:
        rec = "Indoor HIIT / Strength training"
        details = "Due to poor outdoor weather, prioritize indoor training. We recommend a bodyweight HIIT circuit or progressive overload resistance lifting in the gym."
    elif "cold" in w_lower:
        rec = "Indoor Active Recovery (Yoga / Mobility)"
        details = "Cold weather can restrict joint fluid movement. Prioritize indoor yoga, full-body foam rolling, and mobility routines to stay warm and fluid."
    elif "hot" in w_lower:
        rec = "Indoor Gym Cardio / Swimming"
        details = "High temperatures increase cardiac strain. Hydrate heavily and prefer climate-controlled cardio or indoor swimming."
    else:
        rec = "Outdoor Aerobic Running / Cycling"
        details = "Clear skies and perfect temperatures! We recommend an outdoor running or cycling route to enhance aerobic capacity and get sunlight."

    return {
        "weather_input": weather,
        "recommendation": rec,
        "details": details
    }




@app.get("/api/notifications")
def get_notifications(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    notifications = []
    latest_nut = db.query(NutritionLog).filter(NutritionLog.user_id == user.id).order_by(NutritionLog.id.desc()).first()
    water = latest_nut.water_liters if latest_nut else 0.0
    if water < 3.0:
        notifications.append({
            "type": "hydration",
            "title": "Hydration Reminder",
            "message": f"You've logged {water}L today. Aim for at least 3.0L to support muscle recovery.",
            "severity": "medium"
        })

    latest_fat = db.query(FatigueLog).filter(FatigueLog.user_id == user.id).order_by(FatigueLog.id.desc()).first()
    sleep = latest_fat.sleep_hours if latest_fat else 8.0
    if sleep < 7.0:
        notifications.append({
            "type": "sleep",
            "title": "Sleep Recovery Alert",
            "message": f"Only {sleep} hours of sleep logged. Prioritize 8 hours tonight to lower fatigue risk.",
            "severity": "high"
        })



    if not notifications:
        notifications.append({
            "type": "general",
            "title": "Status Clear",
            "message": "All goals, hydration, and sleep logs are in the sweet spot. Keep it up!",
            "severity": "low"
        })
    return notifications


@app.post("/api/diet/recommendation")
def get_diet_recommendation(data: DietRequest, user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    target_tdee = 2000
    protein_g = 140
    carbs_g = 220
    fats_g = 65
    if user.height and user.weight and user.age:
        bmr = (10 * user.weight) + (6.25 * user.height) - (5 * user.age)
        bmr = bmr + 5 if user.gender == "Male" else bmr - 161
        active_mult = 1.4 if user.daily_activity_level == "Moderately Active" else (1.7 if user.daily_activity_level == "Very Active" else 1.2)
        target_tdee = round(bmr * active_mult)
        if user.fitness_objective == "Muscle Gain":
            target_tdee += 300
            protein_g = round(2.0 * user.weight)
            fats_g = round((target_tdee * 0.25) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)
        elif user.fitness_objective == "Weight Loss":
            target_tdee -= 400
            protein_g = round(2.2 * user.weight)
            fats_g = round((target_tdee * 0.20) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)
        else:
            protein_g = round(1.6 * user.weight)
            fats_g = round((target_tdee * 0.25) / 9.0)
            carbs_g = round((target_tdee - (protein_g * 4 + fats_g * 9)) / 4.0)

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    todays_workouts = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user.id,
        WorkoutSession.date >= today_start
    ).all()

    workout_summary = "None logged yet today."
    if todays_workouts:
        workout_list = []
        for w in todays_workouts:
            workout_list.append(f"- {w.exercise_name}: {w.sets} sets x {w.reps} reps @ {w.weight_load} kg ({w.duration_minutes} mins)")
        workout_summary = "\n".join(workout_list)

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            prompt = f"""
            You are StrengthSync, an elite AI sports nutritionist and fitness dietitian.
            Generate a highly customized, scientifically grounded meal plan suggestion.

            ### Target Context
            - Meal Requested: {data.meal_type}
            - Timing Context: {data.workout_relation} (e.g. Pre-workout, Post-workout, or Regular meal)
            - Additional Notes/Requirements: {data.notes or 'None'}

            ### User Biometric Profile (Baseline Data)
            - Gender: {user.gender or 'Not specified'}
            - Age: {user.age or 'Not specified'}
            - Height: {user.height or 'Not specified'} cm
            - Weight: {user.weight or 'Not specified'} kg
            - Calculated BMI: {user.bmi or 'Not specified'}
            - Daily Activity Level: {user.daily_activity_level or 'Not specified'}
            - Fitness Goal/Objective: {user.fitness_objective or 'Not specified'}
            - Dietary Preferences: {user.dietary_preferences or 'None'}
            - Structural Joint Injuries: {user.structural_injuries or 'None'}

            ### User's Logged Workouts Today
            {workout_summary}

            ### Dynamic Nutrient targets for the whole day
            - Daily Target: {target_tdee} kcal (Protein: {protein_g}g | Carbs: {carbs_g}g | Fats: {fats_g}g)

            ### Output Format Requirement (Strictly Follow This Structure)
            You must format your response exactly matching the structure below.
            Do not write any bullet lists or regular paragraphs for sections 1 and 2. They MUST be markdown tables.
            Do not use any emojis.

            ### Suggested Meal
            | Ingredient | Portion / Details |
            | :--- | :--- |
            | [Ingredient Name 1] | [Amount and prep details] |
            | [Ingredient Name 2] | [Amount and prep details] |

            ### Macronutrient Estimates
            | Nutrient | Amount | % of Daily Target |
            | :--- | :--- | :--- |
            | Calories | [Value] kcal | [Value]% |
            | Protein | [Value] g | [Value]% |
            | Carbohydrates | [Value] g | [Value]% |
            | Fats | [Value] g | [Value]% |

            ### Why this fits you
            [Write exactly 50 to 60 words here in a single cohesive paragraph explaining how this meal matches their biometrics, targets, and today's workout logs. Do not use headers, bold text, or lists within this paragraph.]
            """
            try:
                model = genai.GenerativeModel("gemini-3.5-flash")
                response = model.generate_content(prompt)
            except Exception as inner_e:
                print(f"Primary gemini-3.5-flash model failed for diet ({inner_e}), trying gemini-3.6-flash fallback...")
                model = genai.GenerativeModel("gemini-3.6-flash")
                response = model.generate_content(prompt)

            diet_text = response.text
            diet_text = re.sub(r'[\U00010000-\U0010ffff]', '', diet_text)
            return {"diet_plan": diet_text, "target_calories": target_tdee, "target_protein": protein_g, "target_carbs": carbs_g, "target_fats": fats_g}
        except Exception as e:
            print(f"Gemini API error for diet: {e}")

    fallback_plan = f"""
### Suggested {data.meal_type} ({data.workout_relation})

| Ingredient | Portion / Details |
| --- | --- |
| Greek Yogurt | 200g (0% Fat) |
| Mixed Berries | 50g |
| Chia Seeds | 10g |
| Rolled Oats | 30g |

#### Nutrition Estimates (Approximate)

| Nutrient | Amount | % of Daily Target |
| --- | --- | --- |
| Calories | ~450 kcal | ~21% |
| Protein | ~30 g | ~25% |
| Carbohydrates | ~45 g | ~16% |
| Fats | ~15 g | ~25% |

#### Why this fits you
This balanced meal supports your goal of {user.fitness_objective or 'General Fitness'} with a total target of {target_tdee} kcal, providing steady energy and recovery for your {data.workout_relation} routine without bloating or heavy digestion.
"""
    return {
        "diet_plan": fallback_plan,
        "target_calories": target_tdee,
        "target_protein": protein_g,
        "target_carbs": carbs_g,
        "target_fats": fats_g
    }


@app.get("/api/report/download")
def download_report(user: User = Depends(get_user_from_request), db: Session = Depends(get_db)):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor('#0F172A'), spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#64748B'), spaceAfter=25
    )
    section_heading = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#3B82F6'), spaceBefore=15, spaceAfter=10
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#334155'), leading=14
    )

    story = []
    story.append(Paragraph("StrengthSync - AI Fitness Progress Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%B %d, %Y')} | Patient ID: StrengthSync-{user.id:04d}", subtitle_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Biometric Profile", section_heading))
    bio_data = [
        ["Age", f"{user.age or 'N/A'} yrs", "Gender", f"{user.gender or 'N/A'}"],
        ["Height", f"{user.height or 'N/A'} cm", "Weight", f"{user.weight or 'N/A'} kg"],
        ["BMI", f"{user.bmi or 'N/A'}", "Fitness Goal", f"{user.fitness_objective or 'General Fitness'}"],
        ["Activity Level", f"{user.daily_activity_level or 'Moderate'}", "Injuries", f"{user.structural_injuries or 'None reported'}"]
    ]
    t_bio = Table(bio_data, colWidths=[120, 120, 120, 120])
    t_bio.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1E293B')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t_bio)
    story.append(Spacer(1, 15))

    story.append(Paragraph("2. Recent Workout Session Log", section_heading))
    workouts = db.query(WorkoutSession).filter(WorkoutSession.user_id == user.id).order_by(WorkoutSession.date.desc()).limit(5).all()
    work_data = [["Date", "Exercise Name", "Sets", "Reps", "Load (kg)", "Duration"]]
    for w in workouts:
        work_data.append([
            w.date.strftime("%Y-%m-%d"),
            w.exercise_name,
            str(w.sets),
            str(w.reps),
            f"{w.weight_load} kg" if w.weight_load else "0 kg",
            f"{w.duration_minutes} min"
        ])
    if len(work_data) == 1:
        work_data.append(["No workouts logged yet.", "", "", "", "", ""])
    t_work = Table(work_data, colWidths=[90, 150, 50, 50, 70, 70])
    t_work.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3B82F6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t_work)
    story.append(Spacer(1, 15))

    story.append(Paragraph("3. Neural Workload & Fatigue Summary", section_heading))
    acwr, risk = calculate_acwr_for_user(user.id, db)
    rec = predict_workout_recommendation(user, db)
    summary_text = (
        f"StrengthSync's adaptive engine has evaluated your current rolling training ratio. Your current Acute-to-Chronic Workload Ratio (ACWR) is <b>{acwr:.2f}</b>, which represents a <b>{risk} Risk</b> level. "
        f"Based on your biometrics and injury log, our AI Recommendation Engine has structured your daily training routine around <b>{rec['workout_type']}</b> movements, specifically: <i>{rec['routine']}</i>."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Report verified by **StrengthSync Adaptive Sports Science Core**.", body_style))
    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=StrengthSync_Fitness_Report_{user.id}.pdf"}
    )


os.makedirs("app/static", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")
