# TraceBite Agent P0 開發規格書

## 版本目標：最小可展示版本 MVP

## 1. 版本定位

P0 是 TraceBite Agent 的最小可交付版本，目標是在最短時間內完成一個可 Demo、可部署、可寫進 Kaggle 報告的飲食紀錄 Agent。

本版本重點不是追求完整健康管理，而是完成以下核心閉環：

```text
使用者上傳今日餐點照片
→ Agent 判斷食物內容
→ 估算熱量與三大營養素
→ 儲存今日飲食紀錄
→ 使用者查詢今日 / 本週飲食摘要
→ Agent 回覆結果並附上資料來源
```

P0 必須展示：

1. ADK Agent 工作流。
2. MCP Server 或 Tool 查詢營養資料。
3. 飲食資料儲存。
4. 可追溯資料來源。
5. Cloud Run 或其他公開可存取部署方式。
6. 對 P1 / P2 功能保留擴充接口。

---

## 2. P0 核心使用情境

### 2.1 新增今日飲食紀錄

使用者透過網頁輸入：

| 欄位     | 必填   | 說明                                 |
| ------ | ---- | ---------------------------------- |
| 食物照片   | 是    | 用於 Agent 判斷餐點內容                    |
| 餐別     | 是    | breakfast / lunch / dinner / snack |
| 便當店名稱  | 否    | 提供 Agent 判斷脈絡                      |
| 食物成分重量 | 否    | 使用者可手動輸入，例如白飯 150g                 |
| 食物熱量   | 否    | 使用者已知熱量時可手動輸入                      |
| 日期     | 系統自動 | P0 僅允許今天                           |

Agent 需要完成：

1. 讀取圖片。
2. 推測食物項目。
3. 整合使用者輸入的重量或熱量。
4. 查詢營養資料。
5. 估算總熱量、蛋白質、脂肪、碳水。
6. 建立資料來源紀錄。
7. 儲存到資料庫。
8. 回覆使用者本餐估算結果。

---

### 2.2 查詢今日飲食摘要

使用者可以詢問：

```text
今天吃了多少？
今天飲食狀況如何？
幫我看今天的飲食紀錄。
```

Agent 回覆內容：

1. 今日總熱量。
2. 今日總蛋白質。
3. 今日總脂肪。
4. 今日總碳水。
5. 今日每餐紀錄列表。
6. 每筆紀錄的資料來源。
7. 一般性提醒，不做個人化健康建議。

若 P0 尚未建立使用者身高、體重、體脂、性別等資料，Agent 不應回覆「是否達標」，只能回覆目前紀錄的營養總量。

---

### 2.3 查詢本週飲食摘要

使用者可以詢問：

```text
本週飲食狀況如何？
這週吃了多少熱量？
幫我整理本週飲食紀錄。
```

Agent 回覆內容：

1. 本週每日熱量總覽。
2. 本週平均每日熱量。
3. 本週蛋白質、脂肪、碳水平均。
4. 熱量最高的一天。
5. 常見食物項目。
6. 資料來源摘要。
7. 一般性飲食觀察。

P0 不需要提供完整圖表，但資料格式需保留給 P2 生成圖表使用。

---

## 3. P0 不支援範圍

P0 明確不支援以下功能：

| 功能             | 不支援原因            | 是否保留接口 |
| -------------- | ---------------- | ------ |
| 補登過去飲食紀錄       | 會增加時間判斷與資料修改邏輯   | 是      |
| 修改 / 刪除飲食紀錄    | 會牽涉資料一致性與安全控管    | 是      |
| 使用者個人化 TDEE 建議 | 需要身高、體重、年齡、目標等資料 | 是      |
| 運動紀錄           | 會增加消耗熱量估算邏輯      | 是      |
| 登入 / 多使用者      | 會增加 Auth 與權限控管   | 是      |
| 餐廳菜單資料庫        | 需要額外爬蟲或資料建置      | 是      |
| 精準醫療或減重建議      | 有健康風險            | 否      |

---

## 4. 系統架構

```text
Web UI
  ↓
FastAPI / Cloud Run Backend
  ↓
ADK DietLoggerAgent
  ↓
Food Image Analysis Tool
  ↓
Nutrition MCP Server / Nutrition Lookup Tool
  ↓
Firestore
  ↓
Cloud Storage
```

### 4.1 Web UI

P0 Web UI 需要支援：

1. 上傳食物照片。
2. 選擇餐別。
3. 輸入便當店名稱。
4. 輸入食物重量。
5. 輸入已知熱量。
6. 送出紀錄。
7. 查詢今日摘要。
8. 查詢本週摘要。

---

### 4.2 ADK Agent

P0 Agent 名稱：

```text
DietLoggerAgent
```

主要職責：

1. 理解使用者新增紀錄或查詢紀錄的意圖。
2. 呼叫圖片分析工具。
3. 呼叫營養資料查詢工具。
4. 呼叫資料儲存工具。
5. 回覆使用者可追溯的結果。

---

### 4.3 MCP Server / Nutrition Tool

P0 至少需要提供以下工具：

```text
search_food(query: string)
get_nutrition(food_name: string)
estimate_nutrition(food_name: string, weight_g: number)
list_sources()
```

P0 可先使用簡化版營養資料來源，例如：

1. 自建常見便當食材表。
2. USDA FoodData Central。
3. 台灣食品營養成分資料庫。

---

## 5. P0 資料設計

### 5.1 Firestore Collection

```text
users/{userId}
users/{userId}/meal_logs/{mealLogId}
users/{userId}/daily_summaries/{yyyyMMdd}
```

P0 可以先使用固定 demo user：

```text
userId = demo_user
```

但資料結構必須保留 `userId`，以便 P2 擴充登入與多使用者。

---

### 5.2 meal_logs Schema

```json
{
  "id": "meal_20260706_123000",
  "user_id": "demo_user",
  "date": "2026-07-06",
  "created_at": "2026-07-06T12:30:00+08:00",
  "meal_type": "lunch",
  "restaurant_name": "optional",
  "image_uri": "gs://bucket/path.jpg",
  "manual_inputs": {
    "items": [
      {
        "name": "白飯",
        "weight_g": 150
      }
    ],
    "calories_kcal": null
  },
  "detected_items": [
    {
      "name": "白飯",
      "estimated_weight_g": 150,
      "weight_source": "user_input",
      "calories_kcal": 195,
      "protein_g": 3.6,
      "fat_g": 0.4,
      "carbs_g": 43.5,
      "confidence": 0.88,
      "nutrition_source": {
        "database": "Taiwan Food Nutrition Database",
        "matched_name": "白飯",
        "source_type": "database_lookup"
      }
    }
  ],
  "total": {
    "calories_kcal": 720,
    "protein_g": 32,
    "fat_g": 24,
    "carbs_g": 92
  },
  "readonly_sources": [
    {
      "type": "user_input",
      "label": "使用者輸入",
      "value": "白飯 150g"
    },
    {
      "type": "image_analysis",
      "label": "照片辨識",
      "value": "白飯、雞腿、青菜、滷蛋"
    },
    {
      "type": "nutrition_database",
      "label": "營養資料來源",
      "value": "Taiwan Food Nutrition Database"
    }
  ],
  "agent_audit": {
    "agent_name": "DietLoggerAgent",
    "used_tools": [
      "analyze_food_image",
      "estimate_nutrition",
      "save_meal_log"
    ],
    "warnings": [
      "熱量為估算值，實際數值可能因份量、醬料與烹調方式不同而變動。"
    ]
  },
  "version": "p0"
}
```

---

## 6. P0 API / Tool 規格

### 6.1 新增今日飲食紀錄

```text
POST /api/meals/today
```

Request：

```json
{
  "meal_type": "lunch",
  "restaurant_name": "某某便當",
  "manual_items": [
    {
      "name": "白飯",
      "weight_g": 150
    }
  ],
  "manual_calories_kcal": null,
  "image_file": "multipart-file"
}
```

Response：

```json
{
  "status": "success",
  "meal_log_id": "meal_20260706_123000",
  "summary": {
    "calories_kcal": 720,
    "protein_g": 32,
    "fat_g": 24,
    "carbs_g": 92
  },
  "sources": [
    "user_input",
    "image_analysis",
    "nutrition_database"
  ],
  "message": "已完成今日午餐紀錄。"
}
```

---

### 6.2 查詢今日摘要

```text
GET /api/summary/today
```

Response：

```json
{
  "date": "2026-07-06",
  "total": {
    "calories_kcal": 1800,
    "protein_g": 85,
    "fat_g": 60,
    "carbs_g": 210
  },
  "meals": [],
  "readonly_sources": [],
  "advice_level": "general"
}
```

---

### 6.3 查詢本週摘要

```text
GET /api/summary/week
```

Response：

```json
{
  "week_start": "2026-07-06",
  "week_end": "2026-07-12",
  "daily_totals": [],
  "weekly_average": {
    "calories_kcal": 1750,
    "protein_g": 78,
    "fat_g": 58,
    "carbs_g": 205
  },
  "readonly_sources": [],
  "advice_level": "general"
}
```

---

## 7. P0 對 P1 / P2 的接口保留要求

P0 雖然只支援今日飲食紀錄與今日 / 本週查詢，但必須保留以下擴充能力。

### 7.1 保留使用者 Profile 接口

即使 P0 不啟用個人化建議，資料結構仍需預留：

```text
users/{userId}/profiles/current
```

未來 P1 可加入：

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

P0 Agent 查詢摘要時，需先檢查 profile 是否存在：

```text
if profile exists:
    可交給 P1 personal_advice 模組
else:
    只回覆一般營養總量
```

---

### 7.2 保留運動紀錄接口

P0 不實作運動紀錄，但資料庫路徑需預留：

```text
users/{userId}/exercise_logs/{exerciseLogId}
```

未來 P1 可擴充：

```json
{
  "activity_name": "慢跑",
  "duration_min": 30,
  "intensity": "moderate",
  "calories_burned": 250,
  "created_at": "2026-07-06T18:00:00+08:00"
}
```

---

### 7.3 保留過去日期紀錄接口

P0 API 需保留 `date` 欄位，但目前只允許今天。

```python
if request.date != today:
    return {
        "status": "blocked",
        "reason": "P0 only supports today's meal logging.",
        "future_support": "past_date_logging"
    }
```

這樣 P2 可以直接開啟補登過去紀錄，不需要重寫 API 結構。

---

### 7.4 保留紀錄修改接口

P0 不支援修改與刪除，但資料 schema 需保留：

```json
{
  "status": "active",
  "created_at": "...",
  "updated_at": null,
  "deleted_at": null,
  "revision": 1
}
```

未來 P2 可支援：

1. 修改食物重量。
2. 修改餐別。
3. 刪除錯誤紀錄。
4. 查看修改歷史。

---

### 7.5 保留圖表資料格式

P0 本週摘要需輸出 `daily_totals`，未來 P2 可直接用來畫圖。

```json
{
  "daily_totals": [
    {
      "date": "2026-07-06",
      "calories_kcal": 1800,
      "protein_g": 85,
      "fat_g": 60,
      "carbs_g": 210
    }
  ]
}
```

---

## 8. 安全與限制

P0 必須遵守：

1. 不提供醫療診斷。
2. 不宣稱熱量估算為精準數值。
3. 查詢紀錄時資料來源唯讀。
4. 不允許新增過去日期紀錄。
5. 不允許刪除紀錄。
6. 不允許 Agent 擅自修改使用者輸入。

Agent 固定提醒：

```text
此結果為一般飲食紀錄與營養估算，不取代醫師或營養師建議。
```

---

## 9. P0 驗收標準

P0 完成時，必須能展示：

1. 使用者可上傳一張餐點照片。
2. Agent 可辨識至少 2 個食物項目。
3. Agent 可估算熱量、蛋白質、脂肪、碳水。
4. 系統可儲存飲食紀錄。
5. 使用者可查詢今日飲食摘要。
6. 使用者可查詢本週飲食摘要。
7. 每次回覆都能顯示資料來源。
8. 系統禁止新增非今日紀錄。
9. 專案可部署並提供公開 Demo 或公開 GitHub repo。
10. 程式碼中保留 P1 / P2 擴充接口。

---

## 10. P0 成功定義

P0 成功不代表熱量估算完全精準，而是代表：

```text
TraceBite Agent 已完成一個可追溯、可儲存、可查詢的飲食紀錄 Agent MVP。
```

P0 的核心價值是：

1. 快速紀錄。
2. 來源透明。
3. 可回顧。
4. 可擴充。
5. 可展示 Agent 工作流。
