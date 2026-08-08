import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

def main():
    data_path = os.path.join("data", "dynamic-Hydration-water-intake", "Daily_Water_Intake.csv")
    if not os.path.exists(data_path):
        print("Error: Hydration dataset Daily_Water_Intake.csv not found.")
        return

    df = pd.read_csv(data_path)
    print(f"Dataset Loaded Successfully! Rows: {len(df)}")

    print("Checking for missing values...")
    missing_vals = df.isnull().sum()
    if missing_vals.any():
        print("Missing values found:")
        print(missing_vals[missing_vals > 0])
        df = df.dropna()
    else:
        print("No missing values found.")

    features = ["Age", "Gender", "Weight (kg)", "Physical Activity Level", "Weather"]
    target = "Daily Water Intake (liters)"

    X = df[features].copy()
    y = df[target].copy()

    X["Gender"] = X["Gender"].map({"Male": 1, "Female": 0}).fillna(0).astype(int)
    X["Physical Activity Level"] = X["Physical Activity Level"].map({"Low": 0, "Moderate": 1, "High": 2}).fillna(1).astype(int)
    X["Weather"] = X["Weather"].map({"Cold": 0, "Normal": 1, "Hot": 2}).fillna(1).astype(int)

    X = X.rename(columns={"Weight (kg)": "Weight"})

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training RandomForestRegressor for Hydration estimation...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n--- Model Evaluation ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f} liters")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} liters")
    print(f"R-squared (R2) Score: {r2:.4f}")

    os.makedirs(os.path.join("app", "models"), exist_ok=True)
    export_path = os.path.join("app", "models", "hydration_estimator.joblib")
    joblib.dump(model, export_path)
    print(f"\nSuccess! Trained model saved to: {export_path}")

if __name__ == "__main__":
    main()
