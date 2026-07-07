# TraceBite Agent P1 開發規格書

## 版本目標：加入個人化 Profile、運動紀錄與飲食建議

## 1. 版本定位

P1 是 TraceBite Agent 在 P0 飲食紀錄能力上的第一階段擴充。
P0 解決的是「記錄與查詢」，P1 解決的是「根據使用者狀態給出更有脈絡的建議」。

P1 主要新增：

1. 使用者基本資料 Profile。
2. 運動紀錄。
3. 根據 Profile 與運動紀錄產生今日飲食建議。
4. 根據本週飲食與運動資料產生週建議。
5. 保留 P2 所需的補登、修改、圖表、登入與多使用者擴充接口。

P1 不追求醫療級建議，僅提供一般性飲食與運動回饋。

---

## 2. P1 新增核心使用情境

### 2.1 建立使用者 Profile

使用者可以輸入：

| 欄位   | 必填 | 說明                                    |
| ---- | -- | ------------------------------------- |
| 身高   | 是  | 單位 cm                                 |
| 體重   | 是  | 單位 kg                                 |
| 性別   | 是  | male / female / other                 |
| 年齡   | 是  | 用於基礎代謝估算                              |
| 體脂率  | 否  | 若有填寫，可提供更細緻分析                         |
| 目標   | 是  | fat_loss / maintain / muscle_gain     |
| 活動等級 | 是  | sedentary / light / moderate / active |

Profile 目的：

1. 估算基礎代謝 BMR。
2. 估算每日總消耗 TDEE。
3. 判斷今日熱量攝取是否偏高或偏低。
4. 讓 Agent 給出更貼近使用者目標的建議。

---

### 2.2 新增今日運動紀錄

使用者可以輸入：

| 欄位   | 必填 | 說明                    |
| ---- | -- | --------------------- |
| 運動名稱 | 是  | 例如慢跑、重訓、游泳            |
| 運動時間 | 是  | 單位分鐘                  |
| 強度   | 是  | low / moderate / high |
| 消耗熱量 | 否  | 若使用者有穿戴裝置資料可自行輸入      |
| 備註   | 否  | 例如「腿部重訓」、「跑步機」        |

若使用者有輸入消耗熱量，系統優先採用使用者輸入。
若使用者沒有輸入，Agent 可根據運動類型、時間、強度與體重粗估，但必須標記為 estimated。

---

### 2.3 查詢今日個人化飲食建議

使用者可以詢問：

```text
我今天吃得如何？
今天熱量有超標嗎？
我今天有運動，飲食還可以嗎？
```

Agent 需要整合：

1. 今日飲食紀錄。
2. 今日運動紀錄。
3. 使用者 Profile。
4. 使用者目標。
5. 今日攝取與估算消耗。

回覆內容：

1. 今日攝取熱量。
2. 今日運動消耗。
3. 估算淨熱量。
4. 與目標相比的狀態。
5. 蛋白質是否可能不足。
6. 飲食改善建議。
7. 鼓勵語氣。
8. 資料來源列表。

---

### 2.4 查詢本週個人化摘要

使用者可以詢問：

```text
這週飲食狀況如何？
這週有沒有比較健康？
這週飲食跟運動有達標嗎？
```

Agent 需要回覆：

1. 本週平均每日熱量。
2. 本週總運動次數。
3. 本週估算總運動消耗。
4. 本週飲食與目標的差距。
5. 最需要改善的一個問題。
6. 下週建議。
7. 資料來源摘要。

---

## 3. P1 不支援範圍

| 功能         | 不支援原因           | 是否保留 P2 接口 |
| ---------- | --------------- | ---------- |
| 補登過去飲食紀錄   | 仍需避免時間資料混亂      | 是          |
| 修改 / 刪除紀錄  | 牽涉版本紀錄與資料一致性    | 是          |
| 多使用者登入     | 增加 Auth 工作量     | 是          |
| 圖表儀表板      | P1 先以文字摘要為主     | 是          |
| 餐廳菜單辨識     | 需建立菜單資料來源       | 是          |
| 醫療級建議      | 有健康風險           | 否          |
| 自動制定完整健身課表 | 超出飲食紀錄 Agent 範圍 | 否          |

---

## 4. 系統架構變更

P1 在 P0 架構上新增 Profile 與 Exercise 模組。

```text
Web UI
  ↓
FastAPI / Cloud Run Backend
  ↓
ADK DietLoggerAgent
  ├── Food Image Analyzer
  ├── Nutrition Estimator
  ├── Profile Manager
  ├── Exercise Logger
  └── Advice Generator
  ↓
Nutrition MCP Server
  ↓
Firestore / Cloud Storage
```

---

## 5. P1 Agent 設計

### 5.1 Agent 組成

```text
DietLoggerAgent
├── FoodImageAnalyzer
├── NutritionEstimator
├── RecordManager
├── ProfileManager
├── ExerciseLogger
└── AdviceGenerator
```

### 5.2 各模組職責

| 模組                 | 職責                   |
| ------------------ | -------------------- |
| FoodImageAnalyzer  | 分析食物照片               |
| NutritionEstimator | 查詢營養資料並估算熱量          |
| RecordManager      | 儲存與查詢飲食紀錄            |
| ProfileManager     | 建立與讀取使用者 Profile     |
| ExerciseLogger     | 儲存與查詢運動紀錄            |
| AdviceGenerator    | 整合飲食、運動、Profile 產生建議 |

---

## 6. P1 資料設計

### 6.1 Firestore Collection

```text
users/{userId}
users/{userId}/profiles/current
users/{userId}/meal_logs/{mealLogId}
users/{userId}/exercise_logs/{exerciseLogId}
users/{userId}/daily_summaries/{yyyyMMdd}
users/{userId}/weekly_summaries/{yyyyWeek}
```

---

### 6.2 Profile Schema

```json
{
  "user_id": "demo_user",
  "height_cm": 170,
  "weight_kg": 68,
  "body_fat_percent": 20,
  "gender": "male",
  "age": 24,
  "goal": "fat_loss",
  "activity_level": "light",
  "estimated_bmr": 1600,
  "estimated_tdee": 2100,
  "created_at": "2026-07-06T10:00:00+08:00",
  "updated_at": "2026-07-06T10:00:00+08:00",
  "version": "p1"
}
```

---

### 6.3 Exercise Log Schema

```json
{
  "id": "exercise_20260706_180000",
  "user_id": "demo_user",
  "date": "2026-07-06",
  "created_at": "2026-07-06T18:00:00+08:00",
  "activity_name": "慢跑",
  "duration_min": 30,
  "intensity": "moderate",
  "calories_burned": 250,
  "calorie_source": "estimated",
  "note": "跑步機",
  "readonly_sources": [
    {
      "type": "user_input",
      "label": "使用者輸入",
      "value": "慢跑 30 分鐘，中等強度"
    },
    {
      "type": "agent_estimation",
      "label": "Agent 粗估",
      "value": "根據體重、時間與強度估算消耗熱量"
    }
  ],
  "version": "p1"
}
```

---

### 6.4 Daily Summary Schema

```json
{
  "user_id": "demo_user",
  "date": "2026-07-06",
  "meal_total": {
    "calories_kcal": 1800,
    "protein_g": 85,
    "fat_g": 60,
    "carbs_g": 210
  },
  "exercise_total": {
    "calories_burned": 250,
    "duration_min": 30
  },
  "profile_snapshot": {
    "weight_kg": 68,
    "goal": "fat_loss",
    "estimated_tdee": 2100
  },
  "net_calorie_estimate": 1550,
  "advice_level": "personalized",
  "readonly_sources": [
    "meal_logs",
    "exercise_logs",
    "profile"
  ]
}
```

---

## 7. P1 API / Tool 規格

### 7.1 建立或更新 Profile

```text
POST /api/profile
```

Request：

```json
{
  "height_cm": 170,
  "weight_kg": 68,
  "body_fat_percent": 20,
  "gender": "male",
  "age": 24,
  "goal": "fat_loss",
  "activity_level": "light"
}
```

Response：

```json
{
  "status": "success",
  "estimated_bmr": 1600,
  "estimated_tdee": 2100,
  "message": "已建立個人資料，之後可提供較個人化的飲食建議。"
}
```

---

### 7.2 新增今日運動紀錄

```text
POST /api/exercises/today
```

Request：

```json
{
  "activity_name": "慢跑",
  "duration_min": 30,
  "intensity": "moderate",
  "calories_burned": null,
  "note": "跑步機"
}
```

Response：

```json
{
  "status": "success",
  "exercise_log_id": "exercise_20260706_180000",
  "calories_burned": 250,
  "calorie_source": "estimated",
  "message": "已完成今日運動紀錄，很讚，今天有動起來！"
}
```

---

### 7.3 查詢今日個人化建議

```text
GET /api/advice/today
```

Response：

```json
{
  "date": "2026-07-06",
  "meal_total": {
    "calories_kcal": 1800,
    "protein_g": 85,
    "fat_g": 60,
    "carbs_g": 210
  },
  "exercise_total": {
    "calories_burned": 250
  },
  "profile": {
    "goal": "fat_loss",
    "estimated_tdee": 2100
  },
  "net_calorie_estimate": 1550,
  "advice": [
    "今天整體熱量可能低於你的估算消耗，若有飢餓感可以補充高蛋白食物。",
    "蛋白質攝取表現不錯，可以繼續維持。"
  ],
  "readonly_sources": [
    "profile",
    "meal_logs",
    "exercise_logs"
  ]
}
```

---

## 8. P1 對 P2 的接口保留要求

P1 必須在程式與資料結構上保留 P2 擴充能力。

### 8.1 保留補登過去紀錄接口

P1 仍不開放補登過去飲食與運動，但 API 必須保留 date 欄位。

```json
{
  "date": "2026-07-05",
  "allow_past_date": false
}
```

目前規則：

```text
if date != today:
    block request
```

P2 可改成：

```text
if date within allowed range:
    allow request
```

---

### 8.2 保留修改紀錄接口

P1 資料 schema 必須保留：

```json
{
  "revision": 1,
  "status": "active",
  "updated_at": null,
  "update_reason": null
}
```

P2 可使用：

```text
PATCH /api/meals/{mealLogId}
PATCH /api/exercises/{exerciseLogId}
DELETE /api/meals/{mealLogId}
```

---

### 8.3 保留圖表資料接口

P1 的 daily summary 與 weekly summary 需要輸出結構化資料，不只能輸出文字。

未來 P2 可直接根據以下資料畫圖：

```json
{
  "chart_ready": {
    "dates": ["2026-07-06", "2026-07-07"],
    "calories": [1800, 1750],
    "protein": [85, 78],
    "exercise_calories": [250, 300]
  }
}
```

---

### 8.4 保留登入與多使用者接口

P1 可繼續使用 demo user，但所有 API 都必須保留 `userId` 或從 request context 取得 user。

目前：

```text
userId = demo_user
```

未來 P2：

```text
userId = authenticated_user.id
```

程式不得把資料寫死在全域單一使用者結構中。

---

### 8.5 保留餐廳與菜單資料接口

P1 仍不建立完整餐廳資料庫，但 meal log 需保留：

```json
{
  "restaurant_name": "某某便當",
  "menu_item_name": null,
  "restaurant_id": null
}
```

P2 可擴充：

```text
restaurants/{restaurantId}
restaurants/{restaurantId}/menu_items/{menuItemId}
```

---

## 9. 個人化建議規則

P1 建議內容應遵守以下規則：

### 9.1 有 Profile 時

Agent 可以回覆：

1. 今日攝取是否高於或低於估算 TDEE。
2. 今日蛋白質攝取是否可能不足。
3. 若目標是 fat_loss，可提醒避免過量油炸或含糖飲料。
4. 若目標是 muscle_gain，可提醒蛋白質與總熱量是否足夠。
5. 若目標是 maintain，可提醒穩定與均衡。

### 9.2 無 Profile 時

Agent 不得做個人化判斷，只能回覆：

```text
目前尚未建立身高、體重、年齡、目標等資料，因此我先提供一般飲食摘要。
```

---

## 10. 安全與限制

P1 必須保留 P0 的安全規則，並新增：

1. 不提供疾病治療建議。
2. 不提供極端減重建議。
3. 不建議低於安全範圍的熱量攝取。
4. 不對孕婦、病患、慢性病使用者提供專業建議。
5. 所有建議需標示為一般建議。
6. Agent 不可自行更改使用者 Profile。
7. Profile 更新需要使用者明確提交。

固定提醒：

```text
這是一般飲食與運動紀錄建議，不取代醫師、營養師或專業教練。
```

---

## 11. P1 驗收標準

P1 完成時，必須能展示：

1. 使用者可建立 Profile。
2. 系統可估算 BMR / TDEE。
3. 使用者可新增今日運動紀錄。
4. 若使用者未輸入消耗熱量，Agent 可粗估並標記 estimated。
5. 今日摘要可整合飲食與運動。
6. 有 Profile 時，Agent 能提供個人化飲食建議。
7. 無 Profile 時，Agent 只提供一般摘要。
8. 查詢結果仍附上資料來源。
9. 所有資料仍可追溯。
10. 程式保留 P2 的補登、修改、圖表、登入與餐廳資料接口。

---

## 12. P1 成功定義

P1 成功代表：

```text
TraceBite Agent 不只可以記錄飲食，也能根據使用者基本資料與運動紀錄，提供具脈絡的一般性飲食建議。
```

P1 的核心價值是：

1. 個人化。
2. 飲食與運動整合。
3. 更有脈絡的 Agent 回覆。
4. 保持資料來源可追溯。
5. 保留正式產品化擴充能力。
