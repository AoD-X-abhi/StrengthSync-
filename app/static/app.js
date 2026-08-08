document.addEventListener("DOMContentLoaded", () => {

    let currentUser = null;
    let chartWorkload = null;
    let chartProgression = null;
    let chartDietPie = null;
    
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif";
        Chart.defaults.color = "rgba(255, 255, 255, 0.7)";
    }


    const panels = document.querySelectorAll(".content-panel");
    const menuItems = document.querySelectorAll(".menu-item");
    const authModal = document.getElementById("auth-modal");


    const tabLogin = document.getElementById("btn-tab-login");
    const tabRegister = document.getElementById("btn-tab-register");
    const formLogin = document.getElementById("form-auth-login");
    const formRegister = document.getElementById("form-auth-register");
    const btnGuest = document.getElementById("btn-guest-access");
    const btnLogout = document.getElementById("btn-logout");
    const sidebarEmail = document.getElementById("sidebar-user-email");


    const formOnboarding = document.getElementById("form-onboarding");
    const formWorkout = document.getElementById("form-log-workout");
    const formNutrition = document.getElementById("form-log-nutrition");
    const formFatigue = document.getElementById("form-quick-fatigue");
    const sliderSoreness = document.getElementById("fatigue-soreness");
    const txtSorenessVal = document.getElementById("soreness-val");


    const dashWorkoutsWeek = document.getElementById("dash-workouts-week");
    const dashTrainingTime = document.getElementById("dash-training-time");
    const dashCalories = document.getElementById("dash-calories");
    const dashCalorieTarget = document.getElementById("dash-calorie-target");
    const dashInjuryRisk = document.getElementById("dash-injury-risk");
    const dashInjuryDetail = document.getElementById("dash-injury-detail");
    const cardInjuryRisk = document.getElementById("card-injury-risk");
    const xaiExplanationBox = document.getElementById("xai-explanation-box");


    const analyticACWR = document.getElementById("analytic-acwr");
    const analyticACWRStatus = document.getElementById("analytic-acwr-status");
    const cardAnalyticRisk = document.getElementById("card-analytic-risk");
    const analyticRiskTier = document.getElementById("analytic-risk-tier");
    const analyticSquat1RM = document.getElementById("analytic-squat-1rm");
    const analyticSquatChange = document.getElementById("analytic-squat-change");


    const workoutHistoryList = document.getElementById("workout-history-list");
    const nutritionHistoryList = document.getElementById("nutrition-history-list");


    const btnToggleCamera = document.getElementById("btn-toggle-camera");
    const webcamViewport = document.getElementById("webcam-viewport");
    const webcamEl = document.getElementById("webcam-el");
    const canvasOverlay = document.getElementById("canvas-overlay");
    const viewportOverlay = document.getElementById("viewport-overlay");
    let isWebcamOn = false;
    let localStream = null;


    const formChat = document.getElementById("form-chat");
    const chatInput = document.getElementById("chat-input-text");
    const chatContainer = document.getElementById("chat-messages-container");


    function navigateToPanel(hash) {
        const targetId = hash.replace("#", "") || "dashboard";


        menuItems.forEach(item => {
            if (item.getAttribute("href") === hash) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });


        panels.forEach(panel => {
            if (panel.id === `panel-${targetId}`) {
                panel.classList.add("active");
            } else {
                panel.classList.remove("active");
            }
        });


        if (targetId === "dashboard") {
            loadDashboardData();
        } else if (targetId === "workout") {
            loadWorkoutHistory();
        } else if (targetId === "nutrition") {
            loadNutritionHistory();
        } else if (targetId === "analytics") {
            loadAnalyticsData();

        } else if (targetId === "photos") {
            loadPhotosData();
        }
    }


    window.addEventListener("hashchange", () => {
        navigateToPanel(window.location.hash || "#dashboard");
    });


    menuItems.forEach(item => {
        item.addEventListener("click", (e) => {
            const hash = item.getAttribute("href");
            if (hash.startsWith("#")) {
                window.location.hash = hash;
            }
        });
    });


    if (sliderSoreness) {
        sliderSoreness.addEventListener("input", (e) => {
            txtSorenessVal.textContent = `${e.target.value}/10`;
        });
    }


    tabLogin.addEventListener("click", () => {
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
        formLogin.classList.remove("hide");
        formRegister.classList.add("hide");
    });

    tabRegister.addEventListener("click", () => {
        tabRegister.classList.add("active");
        tabLogin.classList.remove("active");
        formRegister.classList.remove("hide");
        formLogin.classList.add("hide");
    });


    async function checkAuth() {
        try {
            const res = await fetch("/api/me");
            if (res.ok) {
                currentUser = await res.json();
                sidebarEmail.textContent = currentUser.email;
                const mobileEmail = document.getElementById("mobile-welcome-email");
                if (mobileEmail) {
                    mobileEmail.textContent = currentUser.email;
                }
                authModal.classList.add("hide");


                populateProfileForm();


                navigateToPanel(window.location.hash || "#dashboard");
            } else {
                authModal.classList.remove("hide");
            }
        } catch (err) {
            console.error("Auth check failed:", err);
            authModal.classList.remove("hide");
        }
    }

    function populateProfileForm() {
        if (!currentUser) return;
        document.getElementById("profile-age").value = currentUser.age || "";
        document.getElementById("profile-gender").value = currentUser.gender || "";
        document.getElementById("profile-height").value = currentUser.height || "";
        document.getElementById("profile-weight").value = currentUser.weight || "";
        document.getElementById("profile-objective").value = currentUser.fitness_objective || "";
        document.getElementById("profile-activity").value = currentUser.daily_activity_level || "";
        document.getElementById("profile-injuries").value = currentUser.structural_injuries || "";
        document.getElementById("profile-diet").value = currentUser.dietary_preferences || "";

        if (currentUser.bmi) {
            const badge = document.getElementById("bmi-display-badge");
            badge.classList.remove("hide");
            document.getElementById("calculated-bmi").textContent = currentUser.bmi;
        }
    }


    formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;

        try {
            const res = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            if (res.ok) {
                await checkAuth();
            } else {
                const data = await res.json();
                alert(data.detail || "Login failed");
            }
        } catch (err) {
            alert("Error connecting to server.");
        }
    });

    formRegister.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;

        try {
            const res = await fetch("/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            if (res.ok) {
                await checkAuth();
            } else {
                const data = await res.json();
                alert(data.detail || "Registration failed");
            }
        } catch (err) {
            alert("Error connecting to server.");
        }
    });


    btnGuest.addEventListener("click", async () => {
        const guestEmail = "guest@strengthsync.fit";
        const guestPassword = "GuestPassword123!";

        try {

            let res = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: guestEmail, password: guestPassword })
            });

            if (!res.ok) {

                res = await fetch("/api/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email: guestEmail, password: guestPassword })
                });
            }

            if (res.ok) {
                await checkAuth();
            } else {
                alert("Failed to establish guest connection.");
            }
        } catch (err) {
            alert("Server connection failed.");
        }
    });

    btnLogout.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/logout", { method: "POST" });
            if (res.ok) {
                currentUser = null;
                window.location.reload();
            }
        } catch (err) {
            console.error("Logout failed", err);
        }
    });


    formOnboarding.addEventListener("submit", async (e) => {
        e.preventDefault();
        const profile = {
            age: parseInt(document.getElementById("profile-age").value),
            gender: document.getElementById("profile-gender").value,
            height: parseFloat(document.getElementById("profile-height").value),
            weight: parseFloat(document.getElementById("profile-weight").value),
            fitness_objective: document.getElementById("profile-objective").value,
            daily_activity_level: document.getElementById("profile-activity").value,
            structural_injuries: document.getElementById("profile-injuries").value,
            dietary_preferences: document.getElementById("profile-diet").value
        };

        try {
            const res = await fetch("/api/profile/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(profile)
            });

            if (res.ok) {
                const data = await res.json();
                alert("Biometric profile successfully mapped.");
                await checkAuth();
                navigateToPanel("#dashboard");
            } else {
                alert("Failed to save profile.");
            }
        } catch (err) {
            console.error(err);
        }
    });


    formWorkout.addEventListener("submit", async (e) => {
        e.preventDefault();
        const workout = {
            exercise_name: document.getElementById("workout-exercise").value,
            sets: parseInt(document.getElementById("workout-sets").value),
            reps: parseInt(document.getElementById("workout-reps").value),
            weight_load: parseFloat(document.getElementById("workout-weight").value),
            duration_minutes: parseInt(document.getElementById("workout-duration").value)
        };

        try {
            const res = await fetch("/api/workouts/log", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(workout)
            });

            if (res.ok) {
                alert("Workout session added.");
                formWorkout.reset();

                document.getElementById("workout-sets").value = 3;
                document.getElementById("workout-reps").value = 10;
                document.getElementById("workout-weight").value = 0;
                document.getElementById("workout-duration").value = 45;
                loadWorkoutHistory();
                loadDashboardData();
            } else {
                alert("Failed to log workout.");
            }
        } catch (err) {
            console.error(err);
        }
    });


    formNutrition.addEventListener("submit", async (e) => {
        e.preventDefault();
        const nutrition = {
            calories: parseInt(document.getElementById("nut-calories").value),
            protein: parseFloat(document.getElementById("nut-protein").value),
            carbs: parseFloat(document.getElementById("nut-carbs").value),
            fats: parseFloat(document.getElementById("nut-fats").value),
            water_liters: parseFloat(document.getElementById("nut-water").value)
        };

        try {
            const res = await fetch("/api/nutrition/log", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(nutrition)
            });

            if (res.ok) {
                alert("Nutrition data logged successfully.");
                formNutrition.reset();
                document.getElementById("nut-protein").value = 120;
                document.getElementById("nut-carbs").value = 200;
                document.getElementById("nut-fats").value = 65;
                document.getElementById("nut-water").value = 2.5;
                loadNutritionHistory();
                loadDashboardData();
            } else {
                alert("Failed to log nutrition.");
            }
        } catch (err) {
            console.error(err);
        }
    });


    formFatigue.addEventListener("submit", async (e) => {
        e.preventDefault();
        const soreness = parseInt(document.getElementById("fatigue-soreness").value);
        const sleep_hours = parseFloat(document.getElementById("fatigue-sleep").value);
        const steps = parseInt(document.getElementById("recovery-steps").value) || 10000;
        const active_minutes = parseInt(document.getElementById("recovery-active-min").value) || 45;
        const hrv = parseInt(document.getElementById("recovery-hrv").value) || 55;
        const rhr = parseInt(document.getElementById("recovery-rhr").value) || 65;

        const fatigue = {
            soreness: soreness,
            sleep_hours: sleep_hours,
            hrv: hrv
        };

        try {

            const res = await fetch("/api/fatigue/log", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(fatigue)
            });

            if (res.ok) {

                const recRes = await fetch("/api/predict/recovery", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ steps, active_minutes, sleep_hours, rhr, hrv })
                });

                if (recRes.ok) {
                    const recData = await recRes.json();
                    const recoveryVal = recData.recovery_score;
                    document.getElementById("predicted-recovery-val").textContent = recoveryVal;

                    const badge = document.getElementById("recovery-output-badge");
                    badge.classList.remove("hide");


                    if (recoveryVal >= 80) {
                        badge.style.background = "rgba(0, 255, 210, 0.15)";
                        badge.style.borderColor = "var(--neon-green)";
                    } else if (recoveryVal >= 60) {
                        badge.style.background = "rgba(157, 78, 221, 0.15)";
                        badge.style.borderColor = "var(--neon-purple)";
                    } else {
                        badge.style.background = "rgba(255, 56, 56, 0.15)";
                        badge.style.borderColor = "var(--neon-red)";
                    }
                }

                alert("Fatigue logged & ML recovery index calculated!");
                loadDashboardData();
            } else {
                alert("Failed to log recovery stats.");
            }
        } catch (err) {
            console.error(err);
        }
    });


    async function loadDashboardData() {
        if (!currentUser) return;


        loadGoalsData();
        loadAchievementsData();
        loadNotifications();

        try {
            const res = await fetch("/api/dashboard/summary");
            if (res.ok) {
                const data = await res.json();

                dashWorkoutsWeek.textContent = data.workouts_this_week;
                dashTrainingTime.textContent = `${data.total_minutes}m`;
                dashCalories.textContent = `${data.current_calories} kcal`;

                // Update Weekly Progress Card
                const progressWorkouts = document.getElementById("progress-card-workouts");
                const progressCalories = document.getElementById("progress-card-calories");
                const progressSteps = document.getElementById("progress-card-steps");
                const progressCircle = document.getElementById("weekly-progress-circle-conic");
                const progressPct = document.getElementById("weekly-progress-pct-val");
                
                if (progressWorkouts) progressWorkouts.textContent = `${data.workouts_this_week} Workout${data.workouts_this_week === 1 ? '' : 's'} Completed`;
                if (progressCalories) progressCalories.textContent = `${data.current_calories} kcal Burned`;
                
                let stepsLogged = 5820;
                let stepsTarget = 8000;
                if (progressSteps) progressSteps.textContent = `${stepsLogged.toLocaleString()} / ${stepsTarget.toLocaleString()} Steps`;
                
                let pct = Math.min(100, Math.round((data.workouts_this_week / 4) * 100));
                if (progressPct) progressPct.textContent = `${pct}%`;
                if (progressCircle) {
                    let deg = Math.round(pct * 3.6);
                    progressCircle.style.background = `conic-gradient(#050505 ${deg}deg, rgba(5, 5, 5, 0.12) 0deg)`;
                }

                // Render Calendar
                renderCalendarSlider();
                dashInjuryRisk.textContent = data.injury_risk;
                dashInjuryDetail.textContent = `Soreness: ${data.soreness}/10 | Sleep: ${data.sleep}h`;


                cardInjuryRisk.className = "metric-card neon-red";
                if (data.injury_risk === "Low") {
                    cardInjuryRisk.style.borderBottomColor = "var(--neon-green)";
                    dashInjuryRisk.style.color = "var(--neon-green)";
                    dashInjuryRisk.style.textShadow = "0 0 6px var(--neon-green-glow)";
                } else if (data.injury_risk === "Medium") {
                    cardInjuryRisk.style.borderBottomColor = "var(--neon-purple)";
                    dashInjuryRisk.style.color = "var(--neon-purple)";
                    dashInjuryRisk.style.textShadow = "0 0 6px var(--neon-purple-glow)";
                } else {
                    cardInjuryRisk.style.borderBottomColor = "var(--neon-red)";
                    dashInjuryRisk.style.color = "var(--neon-red)";
                    dashInjuryRisk.style.textShadow = "0 0 6px var(--neon-red-glow)";
                }


                if (currentUser.height && currentUser.weight) {
                    dashCalorieTarget.textContent = `Target TDEE: ${data.target_tdee} kcal (P: ${data.target_protein}g | C: ${data.target_carbs}g | F: ${data.target_fats}g)`;
                    loadWorkoutRecommendation();
                } else {
                    dashCalorieTarget.textContent = "Complete onboarding to set target.";
                    xaiExplanationBox.innerHTML = `
                        <div class="rec-alert warning">
                            <i class="fa-solid fa-circle-info"></i>
                            <span><strong>XAI Layer:</strong> Please complete your <strong>Onboarding Profile</strong> to generate personalized workout recommendations.</span>
                        </div>
                    `;
                }
            }
        } catch (err) {
            console.error("Dashboard fetch error:", err);
        }
    }

    async function loadWorkoutRecommendation() {
        if (!currentUser) return;

        try {
            const res = await fetch("/api/recommendations/workout");
            if (res.ok) {
                const rec = await res.json();

                let alertClass = "success";
                if (rec.injury_lock) {
                    alertClass = "warning";
                }
                if (rec.workout_type === "HIIT") {
                    alertClass = "success";
                }

                let injuryAlert = "";
                if (rec.injury_lock && rec.injury_note) {
                    injuryAlert = `<br><br><strong style="color: var(--neon-red);"><i class="fa-solid fa-triangle-exclamation"></i> Safety Adjustment:</strong> <em>${rec.injury_note}</em>`;
                }

                // Split and generate horizontal list items for each exercise
                let listHtml = '<div class="horizontal-list" style="margin-top: 15px; width: 100%;">';
                const movements = rec.routine.split(",").map(m => m.trim());
                movements.forEach(m => {
                    let duration = "12 min";
                    let calories = "165 kcal";
                    let iconClass = "fa-dumbbell";
                    
                    const m_lower = m.toLowerCase();
                    if (m_lower.includes("squat") || m_lower.includes("leg") || m_lower.includes("lung")) {
                        duration = "15 min";
                        calories = "210 kcal";
                        iconClass = "fa-child-reaching";
                    } else if (m_lower.includes("stretch") || m_lower.includes("yoga") || m_lower.includes("mobility") || m_lower.includes("flex")) {
                        duration = "10 min";
                        calories = "80 kcal";
                        iconClass = "fa-spa";
                    } else if (m_lower.includes("press") || m_lower.includes("push") || m_lower.includes("bench")) {
                        duration = "12 min";
                        calories = "180 kcal";
                        iconClass = "fa-dumbbell";
                    } else if (m_lower.includes("bicep") || m_lower.includes("curl") || m_lower.includes("deadlift")) {
                        duration = "20 min";
                        calories = "295 kcal";
                        iconClass = "fa-weight-hanging";
                    }
                    
                    listHtml += `
                        <div class="horizontal-item">
                            <div class="horizontal-item-left">
                                <div class="horizontal-item-icon">
                                    <i class="fa-solid ${iconClass}"></i>
                                </div>
                                <div class="horizontal-item-details">
                                    <span class="horizontal-item-title">${m}</span>
                                    <div class="horizontal-item-meta">
                                        <span><i class="fa-regular fa-clock"></i> ${duration}</span>
                                        <span><i class="fa-solid fa-fire"></i> ${calories}</span>
                                    </div>
                                </div>
                            </div>
                            <button class="horizontal-item-action" onclick="window.location.hash='#workout'" title="Log Exercise">
                                <i class="fa-solid fa-play"></i>
                            </button>
                        </div>
                    `;
                });
                listHtml += '</div>';

                xaiExplanationBox.innerHTML = `
                    <div class="rec-alert ${alertClass}">
                        <i class="fa-solid fa-gears"></i>
                        <div>
                            <h4><strong>Recommendation:</strong> ${rec.title}</h4>
                            <p style="font-size: 13px; opacity: 0.95; line-height: 1.4; margin: 8px 0 12px 0;">${rec.explanation}${injuryAlert}</p>
                            ${listHtml}
                        </div>
                    </div>
                `;
            }
        } catch (err) {
            console.error("Failed to load workout recommendation:", err);
        }
    }


    async function loadWorkoutHistory() {
        try {
            const res = await fetch("/api/workouts");
            if (res.ok) {
                const data = await res.json();
                workoutHistoryList.innerHTML = "";

                if (data.length === 0) {
                    workoutHistoryList.innerHTML = `<li class="history-empty">No workouts logged yet. Your metrics will appear here.</li>`;
                    return;
                }

                data.forEach(s => {
                    const dateFormatted = new Date(s.date).toLocaleDateString(undefined, {month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'});
                    const li = document.createElement("li");
                    li.className = "history-item";
                    li.innerHTML = `
                        <div>
                            <div class="history-title">${s.exercise_name}</div>
                            <div class="history-meta"><i class="fa-regular fa-calendar"></i> ${dateFormatted} | <i class="fa-regular fa-clock"></i> ${s.duration_minutes}m</div>
                        </div>
                        <div class="history-stats">
                            <div class="history-reps">${s.sets} x ${s.reps}</div>
                            <div class="history-sub">${s.weight_load} kg</div>
                        </div>
                    `;
                    workoutHistoryList.appendChild(li);
                });
            }
        } catch (err) {
            console.error("Failed to load workouts:", err);
        }
    }


    async function loadNutritionHistory() {
        try {
            const res = await fetch("/api/nutrition");
            if (res.ok) {
                const data = await res.json();
                nutritionHistoryList.innerHTML = "";

                if (data.length === 0) {
                    nutritionHistoryList.innerHTML = `<li class="history-empty">No nutritional entries logged today.</li>`;
                    return;
                }

                data.forEach(l => {
                    const dateFormatted = new Date(l.date).toLocaleDateString(undefined, {month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'});
                    const li = document.createElement("li");
                    li.className = "history-item";
                    li.innerHTML = `
                        <div>
                            <div class="history-title">${l.calories} kcal</div>
                            <div class="history-meta"><i class="fa-regular fa-calendar"></i> ${dateFormatted}</div>
                        </div>
                        <div class="history-stats">
                            <div class="history-reps" style="color:var(--neon-green);">${l.protein}g P</div>
                            <div class="history-sub">Carbs: ${l.carbs}g | Fats: ${l.fats}g | Water: ${l.water_liters}L</div>
                        </div>
                    `;
                    nutritionHistoryList.appendChild(li);
                });
            }
        } catch (err) {
            console.error("Failed to load nutrition logs:", err);
        }
    }


    let cvRepCount = 0;
    let cvRepState = "UP";
    let cvLastExercise = "Squats";
    let cvPlankDuration = 0;
    let cvPlankActive = false;
    let cvPlankStartTime = null;
    let poseInstance = null;
    let cameraInstance = null;
    const btnSaveCamWorkout = document.getElementById("btn-save-cam-workout");


    function calculateAngle(a, b, c) {
        const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
        let angle = Math.abs((radians * 180.0) / Math.PI);
        if (angle > 180.0) {
            angle = 360.0 - angle;
        }
        return angle;
    }


    function drawSkeleton(ctx, landmarks, width, height) {
        const getCoords = (lm) => ({
            x: lm.x * width,
            y: lm.y * height,
            visibility: lm.visibility
        });

        const connections = [
            [11, 12],
            [11, 13], [13, 15],
            [12, 14], [14, 16],
            [11, 23], [12, 24],
            [23, 24],
            [23, 25], [25, 27],
            [24, 26], [26, 28]
        ];


        ctx.strokeStyle = "#00ffd2";
        ctx.lineWidth = 4;
        ctx.shadowBlur = 15;
        ctx.shadowColor = "rgba(0, 255, 210, 0.6)";

        connections.forEach(([i, j]) => {
            const lmA = landmarks[i];
            const lmB = landmarks[j];
            if (lmA && lmB && lmA.visibility > 0.5 && lmB.visibility > 0.5) {
                const ptA = getCoords(lmA);
                const ptB = getCoords(lmB);
                ctx.beginPath();
                ctx.moveTo(ptA.x, ptA.y);
                ctx.lineTo(ptB.x, ptB.y);
                ctx.stroke();
            }
        });


        ctx.shadowBlur = 10;
        ctx.shadowColor = "rgba(0, 242, 254, 0.6)";
        ctx.fillStyle = "#00f2fe";
        for (let i = 11; i <= 28; i++) {
            const lm = landmarks[i];
            if (lm && lm.visibility > 0.5) {
                const pt = getCoords(lm);
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 6, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        ctx.shadowBlur = 0;
    }


    function onPoseResults(results) {
        if (!isWebcamOn) return;

        const ctx = canvasOverlay.getContext("2d");
        canvasOverlay.width = webcamViewport.clientWidth;
        canvasOverlay.height = webcamViewport.clientHeight;
        ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);

        canvasOverlay.classList.remove("hide");

        if (!results.poseLandmarks) {
            return;
        }


        drawSkeleton(ctx, results.poseLandmarks, canvasOverlay.width, canvasOverlay.height);

        const selectedExercise = document.getElementById("cam-exercise-select").value;
        const landmarks = results.poseLandmarks;


        if (cvLastExercise !== selectedExercise) {
            cvLastExercise = selectedExercise;
            cvRepCount = 0;
            cvRepState = "UP";
            cvPlankDuration = 0;
            cvPlankActive = false;
            cvPlankStartTime = null;
            document.getElementById("tel-rep-count").textContent = "0";
            document.getElementById("tel-rep-state").textContent = "UP";
            document.getElementById("tel-rep-state").style.color = "var(--neon-green)";
            if (btnSaveCamWorkout) btnSaveCamWorkout.disabled = true;
        }


        const lShoulder = landmarks[11];
        const lElbow = landmarks[13];
        const lWrist = landmarks[15];
        const lHip = landmarks[23];
        const lKnee = landmarks[25];
        const lAnkle = landmarks[27];

        const rShoulder = landmarks[12];
        const rElbow = landmarks[14];
        const rWrist = landmarks[16];
        const rHip = landmarks[24];
        const rKnee = landmarks[26];
        const rAnkle = landmarks[28];

        let postureQuality = 100;
        let feedbackText = "Analyzing posture...";

        if (selectedExercise === "Squats") {
            let kneeAngle = 180;
            let hipAngle = 180;


            const useLeft = (lHip.visibility + lKnee.visibility + lAnkle.visibility) >
                            (rHip.visibility + rKnee.visibility + rAnkle.visibility);

            if (useLeft) {
                kneeAngle = calculateAngle(lHip, lKnee, lAnkle);
                hipAngle = calculateAngle(lShoulder, lHip, lKnee);
            } else {
                kneeAngle = calculateAngle(rHip, rKnee, rAnkle);
                hipAngle = calculateAngle(rShoulder, rHip, rKnee);
            }


            if (cvRepState === "UP") {
                if (kneeAngle < 110) {
                    cvRepState = "DOWN";
                    document.getElementById("tel-rep-state").textContent = "DOWN";
                    document.getElementById("tel-rep-state").style.color = "var(--neon-purple)";
                }
            } else if (cvRepState === "DOWN") {
                if (kneeAngle > 150) {
                    cvRepState = "UP";
                    cvRepCount += 1;
                    document.getElementById("tel-rep-count").textContent = cvRepCount;
                    document.getElementById("tel-rep-state").textContent = "UP";
                    document.getElementById("tel-rep-state").style.color = "var(--neon-green)";
                    if (btnSaveCamWorkout) btnSaveCamWorkout.disabled = false;
                }
            }


            if (kneeAngle < 125) {
                if (hipAngle < 85) {
                    postureQuality = Math.max(50, Math.round(hipAngle * 1.1));
                    feedbackText = "Keep chest up, don't lean forward!";
                } else {
                    postureQuality = 95;
                    feedbackText = "Good depth and vertical chest alignment!";
                }
            } else {
                feedbackText = "Squat down until thighs are parallel to floor.";
            }

        } else if (selectedExercise === "Pushups") {
            let elbowAngle = 180;
            const useLeft = (lShoulder.visibility + lElbow.visibility + lWrist.visibility) >
                            (rShoulder.visibility + rElbow.visibility + rWrist.visibility);

            if (useLeft) {
                elbowAngle = calculateAngle(lShoulder, lElbow, lWrist);
            } else {
                elbowAngle = calculateAngle(rShoulder, rElbow, rWrist);
            }


            if (cvRepState === "UP") {
                if (elbowAngle < 95) {
                    cvRepState = "DOWN";
                    document.getElementById("tel-rep-state").textContent = "DOWN";
                    document.getElementById("tel-rep-state").style.color = "var(--neon-purple)";
                }
            } else if (cvRepState === "DOWN") {
                if (elbowAngle > 145) {
                    cvRepState = "UP";
                    cvRepCount += 1;
                    document.getElementById("tel-rep-count").textContent = cvRepCount;
                    document.getElementById("tel-rep-state").textContent = "UP";
                    document.getElementById("tel-rep-state").style.color = "var(--neon-green)";
                    if (btnSaveCamWorkout) btnSaveCamWorkout.disabled = false;
                }
            }


            let bodyAngle = 180;
            if (useLeft) {
                bodyAngle = calculateAngle(lShoulder, lHip, lKnee);
            } else {
                bodyAngle = calculateAngle(rShoulder, rHip, rKnee);
            }
            const alignmentDiff = Math.abs(180 - bodyAngle);
            postureQuality = Math.max(50, Math.min(100, Math.round(100 - alignmentDiff * 1.8)));
            feedbackText = postureQuality < 80 ? "Core loose! Keep your hips aligned straight." : "Good rigid body alignment.";

        } else if (selectedExercise === "Plank") {
            let hipAngle = 180;
            let kneeAngle = 180;
            const useLeft = (lShoulder.visibility + lHip.visibility + lKnee.visibility) >
                            (rShoulder.visibility + rHip.visibility + rKnee.visibility);

            if (useLeft) {
                hipAngle = calculateAngle(lShoulder, lHip, lKnee);
                kneeAngle = calculateAngle(lHip, lKnee, lAnkle);
            } else {
                hipAngle = calculateAngle(rShoulder, rHip, rKnee);
                kneeAngle = calculateAngle(rHip, rKnee, rAnkle);
            }


            const hipAligned = hipAngle > 155 && hipAngle < 205;
            const kneeAligned = kneeAngle > 155;

            if (hipAligned && kneeAligned) {
                if (!cvPlankActive) {
                    cvPlankActive = true;
                    cvPlankStartTime = Date.now() - (cvPlankDuration * 1000);
                }
                cvPlankDuration = Math.round((Date.now() - cvPlankStartTime) / 1000);
                document.getElementById("tel-rep-count").textContent = cvPlankDuration + "s";
                document.getElementById("tel-rep-state").textContent = "HOLDING";
                document.getElementById("tel-rep-state").style.color = "var(--neon-green)";

                if (cvPlankDuration > 3 && btnSaveCamWorkout) {
                    btnSaveCamWorkout.disabled = false;
                }

                const hipDiff = Math.abs(180 - hipAngle);
                postureQuality = Math.max(50, Math.min(100, Math.round(100 - hipDiff * 1.5)));
                feedbackText = "Excellent straight alignment! Hold the position.";
            } else {
                if (cvPlankActive) {
                    cvPlankActive = false;
                }
                document.getElementById("tel-rep-state").textContent = "INCORRECT";
                document.getElementById("tel-rep-state").style.color = "var(--neon-red)";

                postureQuality = 60;
                feedbackText = !hipAligned ? "Adjust hips to keep back straight!" : "Lock your knees straight.";
            }
        }


        const indicator = document.querySelector(".indicator-fill");
        if (indicator) {
            indicator.style.width = `${postureQuality}%`;
            indicator.className = "indicator-fill";
            if (postureQuality > 85) {
                indicator.classList.add("green");
            } else if (postureQuality > 70) {
                indicator.classList.add("yellow");
            } else {
                indicator.classList.add("red");
            }
        }
        document.getElementById("tel-joint-feedback").textContent = feedbackText;
    }


    function initMediaPipe() {
        if (poseInstance) return;

        poseInstance = new Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
        });

        poseInstance.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        poseInstance.onResults(onPoseResults);
    }


    btnToggleCamera.addEventListener("click", async () => {
        if (!isWebcamOn) {
            try {

                initMediaPipe();


                localStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 360 } });
                webcamEl.srcObject = localStream;
                webcamEl.classList.remove("hide");
                viewportOverlay.classList.add("hide");
                btnToggleCamera.textContent = "Disable Video Stream";
                isWebcamOn = true;


                cameraInstance = new Camera(webcamEl, {
                    onFrame: async () => {
                        if (isWebcamOn && poseInstance) {
                            await poseInstance.send({ image: webcamEl });
                        }
                    },
                    width: 640,
                    height: 360
                });
                cameraInstance.start();

            } catch (err) {
                console.error("Webcam startup failed:", err);
                alert("Camera access denied or device not found. Please verify permissions.");
                stopCamera();
            }
        } else {
            stopCamera();
        }
    });

    function stopCamera() {
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
        }
        if (cameraInstance) {
            try {
                cameraInstance.stop();
            } catch (e) {
                console.warn("Failed stopping cameraInstance:", e);
            }
            cameraInstance = null;
        }
        webcamEl.srcObject = null;
        webcamEl.classList.add("hide");
        canvasOverlay.classList.add("hide");
        viewportOverlay.classList.remove("hide");
        btnToggleCamera.textContent = "Enable Video Stream";
        isWebcamOn = false;

        cvPlankActive = false;
    }


    if (btnSaveCamWorkout) {
        btnSaveCamWorkout.addEventListener("click", async () => {
            const selectedExercise = document.getElementById("cam-exercise-select").value;
            const workout = {
                exercise_name: selectedExercise === "Pushups" ? "Push-ups" : selectedExercise === "Squats" ? "Barbell Squat" : "Plank",
                sets: 1,
                reps: selectedExercise === "Plank" ? 0 : cvRepCount,
                weight_load: 0.0,
                duration_minutes: selectedExercise === "Plank" ? Math.max(1, Math.round(cvPlankDuration / 60)) : 1
            };

            try {
                const res = await fetch("/api/workouts/log", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(workout)
                });

                if (res.ok) {
                    alert(`Successfully logged tracked CV session: ${workout.exercise_name}!`);

                    cvRepCount = 0;
                    cvPlankDuration = 0;
                    document.getElementById("tel-rep-count").textContent = "0";
                    btnSaveCamWorkout.disabled = true;
                    loadWorkoutHistory();
                    loadDashboardData();
                } else {
                    alert("Failed to log tracked workout.");
                }
            } catch (err) {
                console.error("Save tracked session failed:", err);
            }
        });
    }


    window.addEventListener("hashchange", () => {
        if (window.location.hash !== "#camera") {
            stopCamera();
        }
    });


    formChat.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;


        appendChatMessage("user", text);
        chatInput.value = "";


        const typingEl = appendChatMessage("agent", `<span class="pulse">...</span> typing`);

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });

            typingEl.remove();

            if (res.ok) {
                const data = await res.json();
                appendChatMessage("agent", data.response);
            } else {
                appendChatMessage("agent", "I'm sorry, I encountered an issue processing that query. Please try again.");
            }
        } catch (err) {
            typingEl.remove();
            appendChatMessage("agent", "Error connecting to assistant server.");
            console.error(err);
        }
    });

    function appendChatMessage(sender, text) {
        const time = new Date().toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'});
        const msg = document.createElement("div");
        msg.className = `chat-message ${sender}`;
        msg.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid ${sender === 'agent' ? 'fa-bolt-lightning' : 'fa-user'}"></i></div>
            <div class="msg-content">
                <p>${text}</p>
                <span class="msg-time">${time}</span>
            </div>
        `;
        chatContainer.appendChild(msg);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return msg;
    }


    async function loadAnalyticsData() {
        if (!currentUser) return;

        try {
            const res = await fetch("/api/analytics/progress");
            if (res.ok) {
                const data = await res.json();


                if (analyticACWR) {
                    analyticACWR.textContent = data.current_acwr.toFixed(2);

                    let acwrStatusText = "Optimal training ratio";
                    if (data.current_acwr > 1.5) {
                        acwrStatusText = "Danger: Overtraining Zone";
                        analyticACWRStatus.style.color = "var(--neon-red)";
                    } else if (data.current_acwr > 1.2) {
                        acwrStatusText = "Warning: Elevated Injury Risk";
                        analyticACWRStatus.style.color = "var(--neon-purple)";
                    } else if (data.current_acwr < 0.8) {
                        acwrStatusText = "Under-training Zone";
                        analyticACWRStatus.style.color = "var(--neon-blue)";
                    } else {
                        acwrStatusText = "Sweet Spot: Progressive Overload";
                        analyticACWRStatus.style.color = "var(--neon-green)";
                    }
                    analyticACWRStatus.textContent = acwrStatusText;
                }

                if (analyticRiskTier) {
                    analyticRiskTier.textContent = data.current_risk;

                    cardAnalyticRisk.className = "metric-card neon-red";
                    if (data.current_risk === "Low") {
                        cardAnalyticRisk.style.borderBottomColor = "var(--neon-green)";
                        analyticRiskTier.style.color = "var(--neon-green)";
                        analyticRiskTier.style.textShadow = "0 0 6px var(--neon-green-glow)";
                    } else if (data.current_risk === "Medium") {
                        cardAnalyticRisk.style.borderBottomColor = "var(--neon-purple)";
                        analyticRiskTier.style.color = "var(--neon-purple)";
                        analyticRiskTier.style.textShadow = "0 0 6px var(--neon-purple-glow)";
                    } else {
                        cardAnalyticRisk.style.borderBottomColor = "var(--neon-red)";
                        analyticRiskTier.style.color = "var(--neon-red)";
                        analyticRiskTier.style.textShadow = "0 0 6px var(--neon-red-glow)";
                    }
                }

                if (analyticSquat1RM && data.squat_1rm.length > 0) {
                    const currentSquatMax = data.squat_1rm[data.squat_1rm.length - 1];
                    analyticSquat1RM.textContent = `${currentSquatMax} kg`;

                    if (data.squat_1rm.length > 1) {
                        const change = currentSquatMax - data.squat_1rm[0];
                        const changeSign = change >= 0 ? "+" : "";
                        analyticSquatChange.textContent = `${changeSign}${change.toFixed(1)} kg since onboarding`;
                        analyticSquatChange.style.color = change >= 0 ? "var(--neon-green)" : "var(--neon-red)";
                    } else {
                        analyticSquatChange.textContent = "Baseline calibration";
                    }
                }


                renderWorkloadChart(data);
                renderProgressionChart(data);
            }
        } catch (err) {
            console.error("Failed to load analytics data:", err);
        }
    }

    function renderWorkloadChart(data) {
        const canvasEl = document.getElementById("canvas-workload");
        if (!canvasEl) return;
        const ctx = canvasEl.getContext("2d");

        if (chartWorkload) {
            chartWorkload.destroy();
        }

        chartWorkload = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.workload_labels,
                datasets: [
                    {
                        label: "Daily Workload (Volume Load)",
                        data: data.daily_loads,
                        backgroundColor: "rgba(163, 230, 53, 0.25)",
                        borderColor: "rgba(163, 230, 53, 0.95)",
                        borderWidth: 2,
                        yAxisID: "y-load",
                        borderRadius: 6
                    },
                    {
                        label: "Rolling ACWR",
                        data: data.acwr_values,
                        type: "line",
                        borderColor: "#c084fc",
                        borderWidth: 3.5,
                        pointBackgroundColor: "#c084fc",
                        pointBorderColor: "#ffffff",
                        pointHoverRadius: 7,
                        pointHoverBackgroundColor: "#ffffff",
                        fill: false,
                        yAxisID: "y-acwr",
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { color: "rgba(255, 255, 255, 0.03)" },
                        ticks: { color: "rgba(255, 255, 255, 0.7)" }
                    },
                    "y-load": {
                        type: "linear",
                        position: "left",
                        grid: { color: "rgba(255, 255, 255, 0.03)" },
                        ticks: { color: "rgba(255, 255, 255, 0.7)" },
                        title: { display: true, text: "Training Volume", color: "rgba(255, 255, 255, 0.7)" }
                    },
                    "y-acwr": {
                        type: "linear",
                        position: "right",
                        grid: { drawOnChartArea: false },
                        ticks: { color: "rgba(255, 255, 255, 0.7)" },
                        title: { display: true, text: "ACWR Ratio", color: "rgba(255, 255, 255, 0.7)" },
                        min: 0.0,
                        max: 2.5
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: "#fff" }
                    }
                }
            }
        });
    }

    function renderProgressionChart(data) {
        const canvasEl = document.getElementById("canvas-progression");
        if (!canvasEl) return;
        const ctx = canvasEl.getContext("2d");

        if (chartProgression) {
            chartProgression.destroy();
        }

        const squatHist = data.squat_1rm;
        const pushupHist = data.pushup_1rm;

        const squatForecastData = [squatHist[squatHist.length - 1], ...data.squat_forecast];
        const pushupForecastData = [pushupHist[pushupHist.length - 1], ...data.pushup_forecast];

        const totalLabels = [...data.squat_dates, ...data.squat_forecast_labels];

        const squatHistDataset = Array(totalLabels.length).fill(null);
        squatHist.forEach((v, idx) => { squatHistDataset[idx] = v; });

        const squatForecastDataset = Array(totalLabels.length).fill(null);
        squatForecastData.forEach((v, idx) => { squatForecastDataset[squatHist.length - 1 + idx] = v; });

        const pushupHistDataset = Array(totalLabels.length).fill(null);
        pushupHist.forEach((v, idx) => { pushupHistDataset[idx] = v; });

        const pushupForecastDataset = Array(totalLabels.length).fill(null);
        pushupForecastData.forEach((v, idx) => { pushupForecastDataset[pushupHist.length - 1 + idx] = v; });

        chartProgression = new Chart(ctx, {
            type: "line",
            data: {
                labels: totalLabels,
                datasets: [
                    {
                        label: "Squats 1RM History (kg)",
                        data: squatHistDataset,
                        borderColor: "#a3e635",
                        backgroundColor: "rgba(163, 230, 53, 0.05)",
                        borderWidth: 3.5,
                        pointBackgroundColor: "#a3e635",
                        pointBorderColor: "#ffffff",
                        pointHoverRadius: 6,
                        fill: false,
                        tension: 0.25
                    },
                    {
                        label: "Squats ML Forecast (kg)",
                        data: squatForecastDataset,
                        borderColor: "#a3e635",
                        borderDash: [6, 6],
                        borderWidth: 2,
                        pointBackgroundColor: "#a3e635",
                        fill: false,
                        tension: 0.25
                    },
                    {
                        label: "Pushups/Press 1RM History (kg)",
                        data: pushupHistDataset,
                        borderColor: "#c084fc",
                        backgroundColor: "rgba(192, 132, 252, 0.05)",
                        borderWidth: 3.5,
                        pointBackgroundColor: "#c084fc",
                        pointBorderColor: "#ffffff",
                        pointHoverRadius: 6,
                        fill: false,
                        tension: 0.25
                    },
                    {
                        label: "Pushups/Press ML Forecast (kg)",
                        data: pushupForecastDataset,
                        borderColor: "#c084fc",
                        borderDash: [6, 6],
                        borderWidth: 2,
                        pointBackgroundColor: "#c084fc",
                        fill: false,
                        tension: 0.25
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { color: "rgba(255, 255, 255, 0.03)" },
                        ticks: { color: "rgba(255, 255, 255, 0.7)" }
                    },
                    y: {
                        grid: { color: "rgba(255, 255, 255, 0.03)" },
                        ticks: { color: "rgba(255, 255, 255, 0.7)" },
                        title: { display: true, text: "Estimated 1RM (kg)", color: "rgba(255, 255, 255, 0.7)" }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: "#fff" }
                    }
                }
            }
        });
    }


    const btnNotifications = document.getElementById("btn-notifications");
    const dropdown = document.getElementById("notifications-dropdown");
    if (btnNotifications && dropdown) {
        btnNotifications.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("hide");
        });
        document.addEventListener("click", () => {
            dropdown.classList.add("hide");
        });
        dropdown.addEventListener("click", (e) => e.stopPropagation());
    }

    async function loadNotifications() {
        const list = document.getElementById("notifications-list");
        const badge = document.getElementById("noti-badge-dot");
        if (!list) return;
        try {
            const res = await fetch("/api/notifications");
            if (res.ok) {
                const data = await res.json();
                list.innerHTML = "";

                const highAlerts = data.filter(n => n.severity === "high" || n.severity === "medium");
                if (highAlerts.length > 0 && badge) {
                    badge.classList.remove("hide");
                } else if (badge) {
                    badge.classList.add("hide");
                }

                data.forEach(item => {
                    const div = document.createElement("div");
                    div.className = `notification-item ${item.severity}`;
                    div.innerHTML = `
                        <h4>${item.title}</h4>
                        <p>${item.message}</p>
                    `;
                    list.appendChild(div);
                });
            }
        } catch (err) {
            console.error(err);
        }
    }


    const btnPdf = document.getElementById("btn-download-pdf");
    if (btnPdf) {
        btnPdf.addEventListener("click", () => {
            window.location.href = "/api/report/download";
        });
    }


    const btnWeather = document.getElementById("btn-get-weather-suggestion");
    if (btnWeather) {
        btnWeather.addEventListener("click", async () => {
            const weather = document.getElementById("dashboard-weather-select").value;
            try {
                const res = await fetch(`/api/weather/recommendation?weather=${weather}`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById("weather-rec-title").textContent = data.recommendation;
                    document.getElementById("weather-rec-details").textContent = data.details;
                    document.getElementById("weather-output-box").classList.remove("hide");
                }
            } catch (err) {
                console.error(err);
            }
        });
    }


    async function loadGoalsData() {
        const container = document.getElementById("dashboard-goals-container");
        if (!container) return;
        try {
            const res = await fetch("/api/goals");
            if (res.ok) {
                const data = await res.json();
                window.loadedGoals = data;
                container.innerHTML = "";
                data.forEach(goal => {
                    const pct = Math.min(100, Math.round((goal.current_value / goal.target_value) * 100)) || 0;
                    const div = document.createElement("div");
                    div.style.background = "rgba(255,255,255,0.02)";
                    div.style.padding = "10px";
                    div.style.borderRadius = "8px";
                    div.style.border = "1px solid var(--border-color)";
                    div.innerHTML = `
                        <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 6px;">
                            <span style="font-weight: 500; color: var(--text-primary);">${goal.goal_name}</span>
                            <span style="color: var(--text-secondary);">${goal.current_value} / ${goal.target_value} (${pct}%)</span>
                        </div>
                        <div style="height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; position: relative;">
                            <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #00ffd2); border-radius: 3px; transition: width 0.5s ease;"></div>
                        </div>
                        <div style="margin-top: 8px; display: flex; gap: 8px; align-items: center;">
                            <input type="number" id="update-goal-input-${goal.id}" placeholder="Progress" class="form-input" style="padding: 4px 8px; font-size: 0.8rem; width: 85px; height: 28px;">
                            <button type="button" class="btn btn-primary" onclick="updateGoalProgress(${goal.id}, ${goal.target_value})" style="padding: 4px 10px; font-size: 0.8rem; height: 28px; line-height: 1;">Update</button>
                        </div>
                     `;
                     container.appendChild(div);
                });
            }
        } catch (err) {
            console.error(err);
        }
    }

    window.updateGoalProgress = async function(goalId, targetVal) {
        const inputEl = document.getElementById(`update-goal-input-${goalId}`);
        if (!inputEl) return;
        const current_value = parseFloat(inputEl.value);
        if (isNaN(current_value)) {
            alert("Please enter a valid progress number.");
            return;
        }
        try {
            const res = await fetch(`/api/goals/${goalId}/progress`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ current_value })
            });
            if (res.ok) {
                alert("Goal progress updated!");
                loadGoalsData();
            }
        } catch (err) {
            console.error(err);
        }
    };

    const formAddGoal = document.getElementById("form-add-goal");
    if (formAddGoal) {
        formAddGoal.addEventListener("submit", async (e) => {
            e.preventDefault();
            const goal_name = document.getElementById("goal-name-input").value.trim();
            const target_value = parseFloat(document.getElementById("goal-target-input").value);

            const existingGoals = window.loadedGoals || [];
            const duplicate = existingGoals.find(g => g.goal_name.toLowerCase() === goal_name.toLowerCase());

            if (duplicate) {
                const confirmUpdate = confirm(`Goal "${duplicate.goal_name}" already exists with a target of ${duplicate.target_value}. Do you want to update its target value to ${target_value}?`);
                if (!confirmUpdate) return;
            }

            try {
                const res = await fetch("/api/goals", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ goal_name: duplicate ? duplicate.goal_name : goal_name, target_value })
                });
                if (res.ok) {
                    alert(duplicate ? "Goal target updated!" : "New goal registered!");
                    formAddGoal.reset();
                    loadGoalsData();
                }
            } catch (err) {
                console.error(err);
            }
        });
    }


    async function loadAchievementsData() {
        const streakEl = document.getElementById("dashboard-streak-count");
        const badgesList = document.getElementById("dashboard-badges-list");
        const topbarStreakText = document.getElementById("topbar-streak-text");
        const topbarStreakBadge = document.getElementById("topbar-streak-badge");
        const topbarFireball = document.getElementById("topbar-fireball");
        try {
            const res = await fetch("/api/achievements");
            if (res.ok) {
                const data = await res.json();
                if (streakEl) {
                    streakEl.textContent = data.streak_days;
                }
                if (topbarStreakText) {
                    topbarStreakText.textContent = `${data.streak_days} Day${data.streak_days === 1 ? '' : 's'}`;
                }
                if (topbarStreakBadge && topbarFireball) {
                    if (data.today_completed) {
                        topbarFireball.style.color = "#ff3838";
                        topbarFireball.style.filter = "drop-shadow(0 0 5px rgba(255, 56, 56, 0.8))";
                        topbarStreakBadge.style.border = "1.5px solid rgba(255, 56, 56, 0.4)";
                        topbarStreakBadge.style.background = "rgba(255, 56, 56, 0.15)";
                    } else {
                        topbarFireball.style.color = "#cbd5e1";
                        topbarFireball.style.filter = "none";
                        topbarStreakBadge.style.border = "2px dotted #8e9cae";
                        topbarStreakBadge.style.background = "transparent";
                    }
                }
                if (badgesList) {
                    badgesList.innerHTML = "";
                    if (data.badges.length === 0) {
                        badgesList.innerHTML = `<span style="font-size: 0.9rem; color: #94a3b8;">Log your first workout or drink water to unlock badges!</span>`;
                    } else {
                        data.badges.forEach(b => {
                            const span = document.createElement("span");
                            span.className = "badge-item";
                            span.style.padding = "5px 10px";
                            span.style.background = "rgba(168, 85, 247, 0.15)";
                            span.style.border = "1px solid rgba(168, 85, 247, 0.3)";
                            span.style.borderRadius = "15px";
                            span.style.fontSize = "0.8rem";
                            span.style.color = "#c084fc";
                            span.title = b.badge_description;
                            span.innerHTML = `<i class="fa-solid fa-award"></i> ${b.badge_name}`;
                            badgesList.appendChild(span);
                        });
                    }
                }
            }
        } catch (err) {
            console.error(err);
        }
    }

    function parseMarkdownToHtml(markdown) {

        let text = markdown.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F1E0}-\u{1F1FF}]/gu, '');


        const lines = text.split('\n');
        let inTable = false;
        let tableHtml = "";
        let processedLines = [];

        for (let line of lines) {
            let trimmed = line.trim();
            if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
                const cells = trimmed.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
                const isSeparator = cells.every(c => c.match(/^[\s\-:]+$/));

                if (isSeparator) {
                    continue;
                }

                if (!inTable) {
                    inTable = true;
                    tableHtml = '<table class="diet-table"><thead><tr>';
                    cells.forEach(c => {
                        tableHtml += `<th>${c}</th>`;
                    });
                    tableHtml += '</tr></thead><tbody>';
                } else {
                    tableHtml += '<tr>';
                    cells.forEach(c => {
                        tableHtml += `<td>${c}</td>`;
                    });
                    tableHtml += '</tr>';
                }
            } else {
                if (inTable) {
                    inTable = false;
                    tableHtml += '</tbody></table>';
                    processedLines.push(tableHtml);
                    tableHtml = "";
                }
                processedLines.push(line);
            }
        }
        if (inTable) {
            tableHtml += '</tbody></table>';
            processedLines.push(tableHtml);
        }

        text = processedLines.join('\n');


        text = text.replace(/^### (.*?)$/gm, '<h4>$1</h4>');
        text = text.replace(/^## (.*?)$/gm, '<h3>$1</h3>');
        text = text.replace(/^# (.*?)$/gm, '<h2>$1</h2>');


        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');


        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');


        text = text.replace(/^\- (.*?)$/gm, '<li>$1</li>');
        text = text.replace(/^\* (.*?)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>');
        text = text.replace(/<\/ul>\s*<ul>/g, '');


        text = text.replace(/\n\n/g, '<br><br>');
        text = text.replace(/\n/g, '<br>');

        return text;
    }

    function extractMealMacros(text) {

        const cleanText = text.replace(/[\*\#\|]/g, ' ');

        const proteinMatch = cleanText.match(/Protein\s*(?:~|estimates|approximate)?\s*([\d\.]+)\s*g/i);
        const carbsMatch = cleanText.match(/(?:Carbohydrates|Carbs)\s*(?:~|estimates|approximate)?\s*([\d\.]+)\s*g/i);
        const fatsMatch = cleanText.match(/Fats?\s*(?:~|estimates|approximate)?\s*([\d\.]+)\s*g/i);

        const protein = proteinMatch ? parseFloat(proteinMatch[1]) : 30.0;
        const carbs = carbsMatch ? parseFloat(carbsMatch[1]) : 45.0;
        const fats = fatsMatch ? parseFloat(fatsMatch[1]) : 15.0;

        console.log("Extracted meal macros:", { protein, carbs, fats });
        return { protein, carbs, fats };
    }

    function animateTextStreaming(container, htmlContent) {

        container.innerHTML = htmlContent;


        const textNodes = [];
        function findTextNodes(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                if (node.textContent.trim() !== "") {
                    textNodes.push(node);
                }
            } else {
                for (let child of node.childNodes) {
                    findTextNodes(child);
                }
            }
        }
        findTextNodes(container);


        const spansToReveal = [];
        textNodes.forEach(node => {
            const parent = node.parentNode;
            const textVal = node.textContent;
            const parts = textVal.split(/(\s+)/);

            const fragment = document.createDocumentFragment();
            parts.forEach(part => {
                if (part.trim() === "") {
                    fragment.appendChild(document.createTextNode(part));
                } else {
                    const span = document.createElement("span");
                    span.textContent = part;
                    span.style.opacity = "0";
                    span.style.transition = "opacity 0.15s ease";
                    fragment.appendChild(span);
                    spansToReveal.push(span);
                }
            });
            parent.replaceChild(fragment, node);
        });


        let spanIndex = 0;
        function revealNext() {
            if (spanIndex < spansToReveal.length) {
                spansToReveal[spanIndex].style.opacity = "1";
                spanIndex++;
                setTimeout(revealNext, 18);
            }
        }
        revealNext();
    }


    const btnDiet = document.getElementById("btn-generate-diet");
    if (btnDiet) {
        btnDiet.addEventListener("click", async () => {
            const meal_type = document.getElementById("diet-meal-type").value;
            const workout_relation = document.getElementById("diet-workout-relation").value;
            const notes = document.getElementById("diet-extra-notes").value.trim();
            const loader = document.getElementById("diet-loading-indicator");
            const outputBox = document.getElementById("diet-output-box");
            const textContainer = document.getElementById("diet-plan-markdown");


            btnDiet.disabled = true;
            btnDiet.textContent = "AI Processing...";
            textContainer.innerHTML = "";
            outputBox.classList.add("hide");
            loader.classList.remove("hide");

            try {
                const res = await fetch("/api/diet/recommendation", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ meal_type, workout_relation, notes })
                });
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById("diet-calories-val").textContent = data.target_calories;
                    document.getElementById("diet-protein-val").textContent = data.target_protein;
                    document.getElementById("diet-carbs-val").textContent = data.target_carbs;
                    document.getElementById("diet-fats-val").textContent = data.target_fats;

                    loader.classList.add("hide");
                    outputBox.classList.remove("hide");

                    const html = parseMarkdownToHtml(data.diet_plan);
                    animateTextStreaming(textContainer, html);


                    if (chartDietPie) {
                        chartDietPie.destroy();
                    }


                    const mealMacros = extractMealMacros(data.diet_plan);


                    const canvasEl = document.getElementById("canvas-diet-pie");
                    if (canvasEl) {
                        const ctx = canvasEl.getContext("2d");
                        const isLightMode = document.body.classList.contains("light-theme");
                        const textColor = isLightMode ? "#1e293b" : "#fff";
                        chartDietPie = new Chart(ctx, {
                            type: "doughnut",
                            data: {
                                labels: ["Protein", "Carbs", "Fats"],
                                datasets: [{
                                    data: [mealMacros.protein, mealMacros.carbs, mealMacros.fats],
                                    backgroundColor: ["#a855f7", "#00ffd2", "#ff007f"],
                                    borderColor: isLightMode ? "#fff" : "rgba(255, 255, 255, 0.1)",
                                    borderWidth: 1
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'bottom',
                                        labels: {
                                            color: textColor,
                                            font: { size: 10, family: 'Outfit' },
                                            padding: 10
                                        }
                                    }
                                },
                                cutout: '70%'
                            }
                        });
                    }
                }
            } catch (err) {
                console.error(err);
                loader.classList.add("hide");
            } finally {
                btnDiet.disabled = false;
                btnDiet.textContent = "Generate AI Meal Plan";
            }
        });
    }




    const formPhoto = document.getElementById("form-upload-photo");
    if (formPhoto) {
        formPhoto.addEventListener("submit", async (e) => {
            e.preventDefault();
            const urlInput = document.getElementById("photo-url-input").value;
            const weightInput = parseFloat(document.getElementById("photo-weight").value);
            const fileInput = document.getElementById("photo-file-input");

            let photo_url = urlInput || "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=400";

            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const reader = new FileReader();
                reader.onloadend = async () => {
                    photo_url = reader.result;
                    await savePhoto(photo_url, weightInput);
                };
                reader.readAsDataURL(file);
            } else {
                await savePhoto(photo_url, weightInput);
            }
        });
    }

    async function savePhoto(photo_url, weight) {
        try {
            const res = await fetch("/api/photos", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ photo_url, weight })
            });
            if (res.ok) {
                alert("Progress photo logged!");
                formPhoto.reset();
                loadPhotosData();
            }
        } catch (err) {
            console.error(err);
        }
    }

    async function loadPhotosData() {
        const gallery = document.getElementById("photos-gallery");
        if (!gallery) return;
        try {
            const res = await fetch("/api/photos");
            if (res.ok) {
                const data = await res.json();
                gallery.innerHTML = "";
                if (data.length === 0) {
                    gallery.innerHTML = `<p class="history-empty" style="grid-column: span 3;">No progress photos uploaded yet.</p>`;
                } else {
                    data.forEach(item => {
                        const div = document.createElement("div");
                        div.className = "photo-card";
                        div.innerHTML = `
                            <img src="${item.photo_url}" alt="Progress Photo">
                            <div class="photo-info">
                                <span>${item.date}</span>
                                <span>${item.weight} kg</span>
                            </div>
                        `;
                        gallery.appendChild(div);
                    });
                }
            }
        } catch (err) {
            console.error(err);
        }
    }


});