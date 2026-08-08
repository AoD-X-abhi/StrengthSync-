from app.inference import (
    predict_calories_expenditure,
    predict_hydration_requirement,
    predict_average_bpm,
    predict_recovery_score
)

def main():
    print("=== Testing ML Predictor Inference Functions ===")

    print("\n1. Testing Calorie Predictor:")
    cal_pred_male = predict_calories_expenditure(
        gender="Male", age=25, height=175.0, weight=70.0,
        duration=30.0, heart_rate=130.0, body_temp=39.5
    )
    print(f"Predicted calories for Male (25 yo, 70kg, 30m, 130bpm): {cal_pred_male} kcal")

    cal_pred_female = predict_calories_expenditure(
        gender="Female", age=45, height=160.0, weight=55.0,
        duration=45.0, heart_rate=140.0, body_temp=40.1
    )
    print(f"Predicted calories for Female (45 yo, 55kg, 45m, 140bpm): {cal_pred_female} kcal")

    print("\n2. Testing Hydration Estimator:")
    water_sedentary_cold = predict_hydration_requirement(
        age=30, gender="Female", weight=60.0, activity_level="Low", weather="Cold"
    )
    print(f"Predicted hydration (30 yo Female, 60kg, Low activity, Cold weather): {water_sedentary_cold} L")

    water_active_hot = predict_hydration_requirement(
        age=22, gender="Male", weight=85.0, activity_level="High", weather="Hot"
    )
    print(f"Predicted hydration (22 yo Male, 85kg, High activity, Hot weather): {water_active_hot} L")

    print("\n3. Testing Cardiovascular Zone Target Predictor:")
    avg_bpm_yoga = predict_average_bpm(
        age=28, gender="Female", weight=60.0, height=1.65, bmi=22.0, experience_level=2, workout_type="Yoga"
    )
    print(f"Predicted average BPM for Yoga: {avg_bpm_yoga} BPM")

    avg_bpm_hiit = predict_average_bpm(
        age=24, gender="Male", weight=80.0, height=1.80, bmi=24.7, experience_level=3, workout_type="HIIT"
    )
    print(f"Predicted average BPM for HIIT: {avg_bpm_hiit} BPM")

    print("\n4. Testing Physiological Recovery Predictor:")
    rec_score_poor = predict_recovery_score(
        steps=2500, active_minutes=15, sleep_hours=4.5, rhr=82, hrv=28
    )
    print(f"Predicted recovery score (Poor recovery profile): {rec_score_poor} / 100")

    rec_score_good = predict_recovery_score(
        steps=8500, active_minutes=45, sleep_hours=8.0, rhr=58, hrv=78
    )
    print(f"Predicted recovery score (Good recovery profile): {rec_score_good} / 100")

    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    main()
