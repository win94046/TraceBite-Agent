// ==============================================================================
// TraceBite 前端互動與 API 串接邏輯 (static/app.js)
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
    // 獲取 DOM 元素
    const mealForm = document.getElementById("meal-form");
    const imageInput = document.getElementById("image-file");
    const filenamePreview = document.getElementById("filename-preview");
    const advancedToggle = document.getElementById("advanced-toggle");
    const advancedFields = document.getElementById("advanced-fields");
    const btnSubmit = document.getElementById("btn-submit");
    const submitSpinner = document.getElementById("submit-spinner");
    
    // Tab 控制
    const tabToday = document.getElementById("tab-today");
    const tabWeek = document.getElementById("tab-week");
    const panelToday = document.getElementById("panel-today");
    const panelWeek = document.getElementById("panel-week");
    
    // 今日統計數據
    const todayCal = document.getElementById("today-cal");
    const todayProtein = document.getElementById("today-protein");
    const todayFat = document.getElementById("today-fat");
    const todayCarbs = document.getElementById("today-carbs");
    const todayMealsList = document.getElementById("today-meals-list");
    
    // 本週平均數據
    const weekCalAvg = document.getElementById("week-cal-avg");
    const weekProteinAvg = document.getElementById("week-protein-avg");
    const weekFatAvg = document.getElementById("week-fat-avg");
    const weekCarbsAvg = document.getElementById("week-carbs-avg");
    const weeklyChart = document.getElementById("weekly-chart");

    // ==========================================================================
    // 1. 互動效果：展開/收合進階手動欄位
    // ==========================================================================
    advancedToggle.addEventListener("click", () => {
        advancedFields.classList.toggle("hidden");
        if (advancedFields.classList.contains("hidden")) {
            advancedToggle.innerHTML = "⚙️ 展開進階手動輸入欄位 (選填)";
        } else {
            advancedToggle.innerHTML = "⚙️ 收合進階手動輸入欄位";
        }
    });

    // ==========================================================================
    // 2. 互動效果：圖片選擇預覽檔名
    // ==========================================================================
    imageInput.addEventListener("change", () => {
        if (imageInput.files && imageInput.files.length > 0) {
            filenamePreview.innerText = imageInput.files[0].name;
            filenamePreview.style.color = "#38bdf8"; // 天藍色高亮
        } else {
            filenamePreview.innerText = "未選擇任何檔案";
            filenamePreview.style.color = "#94a3b8";
        }
    });

    // ==========================================================================
    // 3. Tab 切換與資料加載
    // ==========================================================================
    tabToday.addEventListener("click", () => {
        tabToday.classList.add("active");
        tabWeek.classList.remove("active");
        panelToday.classList.add("active");
        panelWeek.classList.remove("active");
        loadTodaySummary();
    });

    tabWeek.addEventListener("click", () => {
        tabWeek.classList.add("active");
        tabToday.classList.remove("active");
        panelWeek.classList.add("active");
        panelToday.classList.remove("active");
        loadWeeklySummary();
    });

    // ==========================================================================
    // 4. API 查詢今日摘要 (GET /api/summary/today)
    // ==========================================================================
    async function loadTodaySummary() {
        try {
            const response = await fetch("/api/summary/today");
            if (!response.ok) throw new Error("取得今日摘要失敗");
            
            const data = await response.json();
            
            // 更新數值
            todayCal.innerText = Math.round(data.total.calories_kcal);
            todayProtein.innerText = Math.round(data.total.protein_g);
            todayFat.innerText = Math.round(data.total.fat_g);
            todayCarbs.innerText = Math.round(data.total.carbs_g);
            
            // 更新餐點列表
            todayMealsList.innerHTML = "";
            
            if (!data.meals || data.meals.length === 0) {
                todayMealsList.innerHTML = '<div class="empty-state">今天尚未新增任何飲食紀錄。</div>';
                return;
            }
            
            data.meals.forEach(meal => {
                // 翻譯餐別
                const mealTypeMap = {
                    "breakfast": "早餐 🍳",
                    "lunch": "午餐 🍱",
                    "dinner": "晚餐 🍜",
                    "snack": "點心/宵夜 🍪"
                };
                
                const mealItem = document.createElement("div");
                mealItem.className = "meal-item";
                
                // 拼接食物項目名稱
                const itemsStr = meal.detected_items.map(item => `${item.name}(${item.estimated_weight_g}g)`).join("、") || "手動紀錄";
                
                // 格式化時間 (HH:MM)
                const timeStr = meal.created_at ? new Date(meal.created_at).toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", hour12: false }) : "";
                
                mealItem.innerHTML = `
                    <div class="meal-item-info">
                        <span class="meal-title">${mealTypeMap[meal.meal_type] || meal.meal_type} ${meal.restaurant_name ? `@ ${meal.restaurant_name}` : ''}</span>
                        <span class="meal-meta">${timeStr ? timeStr + ' | ' : ''}${itemsStr}</span>
                    </div>
                    <div class="meal-item-calories">
                        <span class="kcal-val">${Math.round(meal.total.calories_kcal)}</span>
                        <span class="kcal-lbl">kcal</span>
                    </div>
                `;
                todayMealsList.appendChild(mealItem);
            });
        } catch (error) {
            console.error("Error loading today summary:", error);
        }
    }

    // ==========================================================================
    // 5. API 查詢本週趨勢 (GET /api/summary/week)
    // ==========================================================================
    async function loadWeeklySummary() {
        try {
            const response = await fetch("/api/summary/week");
            if (!response.ok) throw new Error("取得本週統計失敗");
            
            const data = await response.json();
            
            // 更新平均數值
            weekCalAvg.innerText = Math.round(data.weekly_average.calories_kcal);
            weekProteinAvg.innerText = Math.round(data.weekly_average.protein_g);
            weekFatAvg.innerText = Math.round(data.weekly_average.fat_g);
            weekCarbsAvg.innerText = Math.round(data.weekly_average.carbs_g);
            
            // 動態繪製直條圖
            weeklyChart.innerHTML = "";
            
            const dailyTotals = data.daily_totals;
            if (!dailyTotals || dailyTotals.length === 0) return;
            
            // 找到本週最高熱量值做為比例分母 (防呆最少 1000 kcal)
            const maxCal = Math.max(...dailyTotals.map(d => d.calories_kcal), 1000);
            
            dailyTotals.forEach(day => {
                const barHeight = (day.calories_kcal / maxCal) * 150; // 最大高度 150px
                
                const barWrapper = document.createElement("div");
                barWrapper.className = "chart-bar-wrapper";
                
                // 月/日格式 (例如: 07-06)
                const dateParts = day.date.split("-");
                const shortDate = dateParts.length >= 3 ? `${dateParts[1]}/${dateParts[2]}` : day.date;
                
                barWrapper.innerHTML = `
                    <div class="chart-bar" style="height: 0px;" title="${Math.round(day.calories_kcal)} kcal"></div>
                    <span class="chart-date">${shortDate}</span>
                `;
                weeklyChart.appendChild(barWrapper);
                
                // 利用 setTimeout 達成直條圖緩緩生長的動畫效果
                setTimeout(() => {
                    barWrapper.querySelector(".chart-bar").style.height = `${barHeight}px`;
                }, 100);
            });
        } catch (error) {
            console.error("Error loading weekly summary:", error);
        }
    }

    // ==========================================================================
    // 6. API 提交飲食表單 (POST /api/meals/today)
    // ==========================================================================
    mealForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // 顯示 Loading Spinner，停用按鈕
        submitSpinner.classList.remove("hidden");
        btnSubmit.disabled = true;
        btnSubmit.style.opacity = "0.7";
        
        const formData = new FormData(mealForm);
        
        try {
            const response = await fetch("/api/meals/today", {
                method: "POST",
                body: formData
            });
            
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "儲存紀錄時發生錯誤");
            }
            
            const result = await response.json();
            
            // 成功提示與重置表單
            alert(`紀錄成功！\n此餐預估熱量為 ${Math.round(result.summary.calories_kcal)} kcal`);
            mealForm.reset();
            filenamePreview.innerText = "未選擇任何檔案";
            filenamePreview.style.color = "#94a3b8";
            
            // 收合進階選項
            advancedFields.classList.add("hidden");
            advancedToggle.innerHTML = "⚙️ 展開進階手動輸入欄位 (選填)";
            
            // 重新讀取數據
            loadTodaySummary();
        } catch (error) {
            alert(`儲存失敗: ${error.message}`);
            console.error("Error submitting meal log:", error);
        } finally {
            // 還原 Loading 狀態
            submitSpinner.classList.add("hidden");
            btnSubmit.disabled = false;
            btnSubmit.style.opacity = "1";
        }
    });

    // 頁面初次載入，預設拉取今日資料
    loadTodaySummary();
});
