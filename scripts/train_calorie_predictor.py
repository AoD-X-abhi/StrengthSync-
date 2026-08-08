import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

def main():
    exercise_path = os.path.join("data", "Calories-Exercise-Data", "exercise.csv")
    calories_path = os.path.join("data", "Calories-Exercise-Data", "calories.csv")

    if not os.path.exists(exercise_path) or not os.path.exists(calories_path):
        print("Error: Calorie-Exercise datasets not found.")
        return

    df_exercise = pd.read_csv(exercise_path)
    df_calories = pd.read_csv(calories_path)

    df = pd.merge(df_exercise, df_calories, on="User_ID")
    print(f"Dataset Loaded Successfully! Rows: {len(df)}")

    print("Checking for missing values...")
    missing_vals = df.isnull().sum()
    if missing_vals.any():
        print("Missing values found:")
        print(missing_vals[missing_vals > 0])
        df = df.dropna()
    else:
        print("No missing values found.")

    features = ["Gender", "Age", "Height", "Weight", "Duration", "Heart_Rate", "Body_Temp"]
    target = "Calories"

    X = df[features].copy()
    y = df[target].copy()

    X["Gender"] = X["Gender"].map({"male": 1, "female": 0}).fillna(0).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training RandomForestRegressor for Calorie prediction...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n--- Model Evaluation ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f} kcal")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} kcal")
    print(f"R-squared (R2) Score: {r2:.4f}")

    os.makedirs(os.path.join("app", "models"), exist_ok=True)
    export_path = os.path.join("app", "models", "calorie_predictor.joblib")
    joblib.dump(model, export_path)
    print(f"\nSuccess! Trained model saved to: {export_path}")

if __name__ == "__main__":
    main()
