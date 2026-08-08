import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

def main():
    data_path = os.path.join("data", "Exercise_tracking-Data", "gym_members_exercise_tracking.csv")
    if not os.path.exists(data_path):
        print("Error: Exercise tracking dataset gym_members_exercise_tracking.csv not found.")
        return

    df = pd.read_csv(data_path)
    print(f"Dataset Loaded Successfully! Rows: {len(df)}")

    print("Checking for missing values...")
    missing_vals = df.isnull().sum()
    if missing_vals.any():
        print("Missing values found and will be handled:")
        df["Gender"] = df["Gender"].fillna(df["Gender"].mode()[0])
        df["Experience_Level"] = df["Experience_Level"].fillna(df["Experience_Level"].mode()[0])
        df["Age"] = df["Age"].fillna(df["Age"].median())
        df["Weight (kg)"] = df["Weight (kg)"].fillna(df["Weight (kg)"].median())
        df["Height (m)"] = df["Height (m)"].fillna(df["Height (m)"].median())
        df["BMI"] = df["BMI"].fillna(df["BMI"].median())
        df["Avg_BPM"] = df["Avg_BPM"].fillna(df["Avg_BPM"].median())
    else:
        print("No missing values found.")

    features = ["Age", "Gender", "Weight (kg)", "Height (m)", "BMI", "Experience_Level", "Workout_Type"]
    target = "Avg_BPM"

    X = df[features].copy()
    y = df[target].copy()

    X["Gender"] = X["Gender"].map({"Male": 1, "Female": 0}).fillna(0).astype(int)
    X["Workout_Type"] = X["Workout_Type"].map({"Cardio": 0, "HIIT": 1, "Strength": 2, "Yoga": 3}).fillna(0).astype(int)
    X["Experience_Level"] = X["Experience_Level"].astype(int)

    X = X.rename(columns={"Weight (kg)": "Weight", "Height (m)": "Height"})

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training RandomForestRegressor for Cardio Avg_BPM prediction...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n--- Model Evaluation ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f} BPM")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} BPM")
    print(f"R-squared (R2) Score: {r2:.4f}")

    os.makedirs(os.path.join("app", "models"), exist_ok=True)
    export_path = os.path.join("app", "models", "cardio_predictor.joblib")
    joblib.dump(model, export_path)
    print(f"\nSuccess! Trained model saved to: {export_path}")

if __name__ == "__main__":
    main()
