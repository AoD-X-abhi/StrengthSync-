import pandas as pd
import numpy as np
import os

def main():
    np.random.seed(42)
    n_records = 1500

    age = np.random.randint(18, 66, size=n_records)

    gender = np.random.choice(["Male", "Female"], size=n_records)

    height = np.zeros(n_records)
    height[gender == "Male"] = np.random.normal(1.78, 0.07, size=sum(gender == "Male"))
    height[gender == "Female"] = np.random.normal(1.63, 0.06, size=sum(gender == "Female"))
    height = np.round(height, 2)

    bmi_base = np.random.normal(24.5, 3.5, size=n_records)
    bmi_base = np.clip(bmi_base, 17.0, 38.0)
    weight = np.round(bmi_base * (height ** 2), 1)

    bmi = np.round(weight / (height ** 2), 2)

    workout_frequency = np.random.randint(1, 7, size=n_records)

    experience_level = []
    for freq in workout_frequency:
        if freq <= 2:
            exp = np.random.choice([1, 2], p=[0.8, 0.2])
        elif freq <= 4:
            exp = np.random.choice([1, 2, 3], p=[0.1, 0.7, 0.2])
        else:
            exp = np.random.choice([2, 3], p=[0.2, 0.8])
        experience_level.append(exp)
    experience_level = np.array(experience_level)

    resting_bpm = []
    for freq in workout_frequency:
        if freq >= 5:
            r_bpm = int(np.random.normal(58, 4))
        elif freq >= 3:
            r_bpm = int(np.random.normal(66, 5))
        else:
            r_bpm = int(np.random.normal(74, 6))
        resting_bpm.append(np.clip(r_bpm, 45, 90))
    resting_bpm = np.array(resting_bpm)

    workout_type = np.random.choice(["Cardio", "HIIT", "Strength", "Yoga"], size=n_records)

    max_bpm = np.round(220 - age + np.random.normal(0, 3, size=n_records)).astype(int)

    avg_bpm = []
    for idx in range(n_records):
        w_type = workout_type[idx]
        m_bpm = max_bpm[idx]
        r_bpm = resting_bpm[idx]

        hrr = m_bpm - r_bpm

        if w_type == "HIIT":
            intensity = np.random.uniform(0.80, 0.90)
        elif w_type == "Cardio":
            intensity = np.random.uniform(0.70, 0.82)
        elif w_type == "Strength":
            intensity = np.random.uniform(0.58, 0.68)
        else:
            intensity = np.random.uniform(0.35, 0.50)

        bpm_val = int(r_bpm + intensity * hrr + np.random.normal(0, 2))
        bpm_val = np.clip(bpm_val, r_bpm + 10, m_bpm - 2)
        avg_bpm.append(bpm_val)
    avg_bpm = np.array(avg_bpm)

    session_duration = []
    for w_type in workout_type:
        if w_type == "HIIT":
            duration = np.random.normal(0.5, 0.1)
        elif w_type == "Cardio":
            duration = np.random.normal(0.8, 0.15)
        elif w_type == "Strength":
            duration = np.random.normal(1.2, 0.2)
        else:
            duration = np.random.normal(1.0, 0.1)
        session_duration.append(np.round(np.clip(duration, 0.3, 2.0), 2))
    session_duration = np.array(session_duration)

    calories_burned = []
    for idx in range(n_records):
        hr = avg_bpm[idx]
        wt = weight[idx]
        ag = age[idx]
        dur = session_duration[idx] * 60.0
        gend = gender[idx]

        if gend == "Male":
            c_min = (hr * 0.6309 + wt * 0.1988 - ag * 0.2017 - 55.0969) / 4.184
        else:
            c_min = (hr * 0.4472 - wt * 0.1263 + ag * 0.074 - 20.4022) / 4.184

        calories_val = round(max(50.0, c_min * dur), 1)
        calories_burned.append(calories_val)
    calories_burned = np.array(calories_burned)

    fat_percentage = []
    for idx in range(n_records):
        b = bmi[idx]
        g = gender[idx]
        if g == "Female":
            fat = b * 1.25 + np.random.normal(2, 3)
        else:
            fat = b * 1.05 - np.random.normal(3, 3)
        fat_percentage.append(np.round(np.clip(fat, 5.0, 50.0), 1))
    fat_percentage = np.array(fat_percentage)

    water_intake = []
    for idx in range(n_records):
        wt = weight[idx]
        dur = session_duration[idx]
        w_type = workout_type[idx]

        base_water = wt * 0.035
        loss_factor = 0.8 if w_type in ["HIIT", "Cardio"] else 0.4
        intake = base_water + dur * loss_factor + np.random.normal(0, 0.2)
        water_intake.append(np.round(max(1.0, intake), 1))
    water_intake = np.array(water_intake)

    df = pd.DataFrame({
        "Age": age,
        "Gender": gender,
        "Weight (kg)": weight,
        "Height (m)": height,
        "Max_BPM": max_bpm,
        "Avg_BPM": avg_bpm,
        "Resting_BPM": resting_bpm,
        "Session_Duration (hours)": session_duration,
        "Calories_Burned": calories_burned,
        "Workout_Type": workout_type,
        "Fat_Percentage": fat_percentage,
        "Water_Intake (liters)": water_intake,
        "Workout_Frequency (days/week)": workout_frequency,
        "Experience_Level": experience_level,
        "BMI": bmi
    })

    target_path = os.path.join("data", "Exercise_tracking-Data", "gym_members_exercise_tracking.csv")
    df.to_csv(target_path, index=False)
    print(f"Successfully generated and saved {n_records} realistic records to {target_path}!")

if __name__ == "__main__":
    main()
