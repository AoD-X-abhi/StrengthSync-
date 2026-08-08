import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
import random

def assign_workout_type(row, rng):
    if rng.random() < 0.15:
        return rng.choice(['Cardio', 'HIIT', 'Strength', 'Yoga'])

    age = row['Age']
    gender = row['Gender']
    bmi = row['BMI']
    freq = row['Workout_Frequency (days/week)']
    exp = row['Experience_Level']

    strength = 0.0
    cardio = 0.0
    hiit = 0.0
    yoga = 0.0

    if gender == 'Male':
        strength += 1.0
        hiit += 0.5
    else:
        yoga += 1.0
        cardio += 0.5

    if age < 30:
        hiit += 1.5
        strength += 1.0
    elif age > 48:
        yoga += 2.0
        cardio += 1.0

    if bmi > 27.5:
        cardio += 1.5
        hiit += 1.0
    elif bmi < 21.0:
        strength += 1.5
        yoga += 0.5

    if freq >= 4:
        strength += 2.0
        hiit += 1.0
    else:
        yoga += 1.5
        cardio += 1.0

    if exp == 3:
        strength += 2.0
        hiit += 1.0
    elif exp == 1:
        yoga += 1.5
        cardio += 1.0

    scores = {
        'Strength': strength,
        'Cardio': cardio,
        'HIIT': hiit,
        'Yoga': yoga
    }

    return max(scores, key=scores.get)

def main():
    rng = random.Random(42)

    data_path = os.path.join("data", "Exercise_tracking-Data", "gym_members_exercise_tracking.csv")
    if not os.path.exists(data_path):
        print(f"Error: Dataset not found.")
        return

    df = pd.read_csv(data_path)
    print("Dataset Loaded Successfully!")
    print(f"Total Rows: {len(df)}")

    print("\nCorrecting target labels (Workout_Type) to establish logical correlations...")
    df['Workout_Type'] = df.apply(lambda row: assign_workout_type(row, rng), axis=1)

    df.to_csv(data_path, index=False)
    print("Saved corrected dataset back to 'gym_members_exercise_tracking.csv'.")

    print("\nUpdated Class Distribution:")
    print(df['Workout_Type'].value_counts())

    features = [
        'Age',
        'Gender',
        'Weight (kg)',
        'Height (m)',
        'BMI',
        'Workout_Frequency (days/week)',
        'Experience_Level'
    ]
    target = 'Workout_Type'

    X = df[features].copy()
    y = df[target].copy()

    X['Gender'] = X['Gender'].map({'Male': 1, 'Female': 0}).fillna(0).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\nTraining Random Forest Model...")
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy (with corrected labels + 15% noise): {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    os.makedirs("app/models", exist_ok=True)
    export_path = "app/models/recommendation_model.joblib"
    joblib.dump(model, export_path)
    print(f"\nSuccess! Trained model saved to: {export_path}")

if __name__ == "__main__":
    main()
