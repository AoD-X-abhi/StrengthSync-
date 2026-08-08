import pandas as pd
import numpy as np
import os

def main():
    np.random.seed(42)
    n_records = 1500

    sleep_hours = np.random.normal(7.2, 1.2, size=n_records)
    sleep_hours = np.round(np.clip(sleep_hours, 3.0, 11.5), 1)

    hrv = np.random.normal(55, 15, size=n_records)
    hrv = np.round(np.clip(hrv, 15.0, 110.0)).astype(int)

    rhr = []
    for h in hrv:
        base_rhr = 80 - (h / 2.5)
        rhr_val = int(np.random.normal(base_rhr, 4))
        rhr.append(np.clip(rhr_val, 48, 88))
    rhr = np.array(rhr)

    steps = np.random.negative_binomial(10, 0.001, size=n_records)
    steps = np.clip(steps, 1000, 32000)

    active_minutes = np.zeros(n_records)
    for idx in range(n_records):
        step_count = steps[idx]
        act_min = int(step_count / 150.0 + np.random.normal(15, 8))
        active_minutes[idx] = np.clip(act_min, 10, 240)
    active_minutes = active_minutes.astype(int)

    recovery_score = []
    for idx in range(n_records):
        sleep = sleep_hours[idx]
        hr_var = hrv[idx]
        resting_hr = rhr[idx]
        step_count = steps[idx]
        act_min = active_minutes[idx]

        score = 50

        if 7.5 <= sleep <= 9.0:
            score += 35
        elif 6.5 <= sleep < 7.5:
            score += 20
        elif sleep < 6.5:
            score -= (6.5 - sleep) * 8
        else:
            score += 15 - (sleep - 9.0) * 5

        if hr_var >= 70:
            score += 20
        elif hr_var >= 50:
            score += 10
        elif hr_var < 35:
            score -= (35 - hr_var) * 0.8

        if resting_hr <= 58:
            score += 15
        elif resting_hr <= 66:
            score += 8
        elif resting_hr >= 74:
            score -= (resting_hr - 74) * 1.2

        if 6000 <= step_count <= 12000:
            score += 10
        elif step_count > 16000:
            score -= (step_count - 16000) * 0.0015
        elif step_count < 3000:
            score -= 5

        score += np.random.normal(0, 2)

        recovery_score.append(int(np.clip(score, 5, 100)))

    recovery_score = np.array(recovery_score)

    df = pd.DataFrame({
        "Steps": steps,
        "Active_Minutes": active_minutes,
        "Sleep_Hours": sleep_hours,
        "RHR": rhr,
        "HRV": hrv,
        "Recovery_Score": recovery_score
    })

    os.makedirs(os.path.join("data", "Recovery-Data"), exist_ok=True)
    target_path = os.path.join("data", "Recovery-Data", "fitbit_recovery_data.csv")
    df.to_csv(target_path, index=False)
    print(f"Successfully generated and saved {n_records} recovery telemetry records to {target_path}!")

if __name__ == "__main__":
    main()
