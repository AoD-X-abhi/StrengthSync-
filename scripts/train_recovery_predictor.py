import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

def main():
    data_path = os.path.join("data", "Recovery-Data", "fitbit_recovery_data.csv")
    if not os.path.exists(data_path):
        print(f"Error: Recovery dataset not found at {data_path}")
        return

    df = pd.read_csv(data_path)
    print(f"Dataset Loaded Successfully! Rows: {len(df)}")

    features = ["Steps", "Active_Minutes", "Sleep_Hours", "RHR", "HRV"]
    target = "Recovery_Score"

    X = df[features].copy()
    y = df[target].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training RandomForestRegressor for Recovery Score prediction...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n--- Model Evaluation ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f} points (scale 0-100)")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} points")
    print(f"R-squared (R2) Score: {r2:.4f}")

    os.makedirs(os.path.join("app", "models"), exist_ok=True)
    export_path = os.path.join("app", "models", "recovery_predictor.joblib")
    joblib.dump(model, export_path)
    print(f"\nSuccess! Trained model saved to: {export_path}")

if __name__ == "__main__":
    main()
