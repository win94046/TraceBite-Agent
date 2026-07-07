# TraceBite Agent P2 開發規格書

## 版本目標：正式產品化擴充版本

## 1. 版本定位

P2 是 TraceBite Agent 從 Kaggle MVP 走向較完整產品原型的版本。
P0 解決「飲食紀錄」，P1 解決「個人化建議」，P2 則補上正式產品常見需求：

1. 補登過去紀錄。
2. 修改與刪除紀錄。
3. 圖表化分析。
4. 多使用者登入。
5. 餐廳 / 菜單資料擴充。
6. 更完整的資料權限與紀錄版本控管。
7. 更成熟的報表與匯出能力。

P2 的目標是讓 TraceBite Agent 不只是 Demo，而是接近可長期使用的健康紀錄工具。

---

## 2. P2 新增核心使用情境

### 2.1 補登過去飲食紀錄

使用者可以補登過去日期的飲食紀錄，例如：

```text
幫我補登昨天晚餐，我吃了一個雞腿便當。
```

系統需要支援：

1. 指定日期。
2. 指定餐別。
3. 上傳照片或純文字輸入。
4. 標記資料為 past_entry。
5. 保留建立時間與實際餐點日期。

資料需區分：

| 欄位         | 說明                       |
| ---------- | ------------------------ |
| date       | 餐點發生日期                   |
| created_at | 使用者建立紀錄時間                |
| entry_type | today_entry / past_entry |

---

### 2.2 修改飲食紀錄

使用者可以修改：

1. 食物名稱。
2. 食物重量。
3. 餐別。
4. 熱量。
5. 營養素。
6. 備註。

修改時必須建立 revision history，不可直接覆蓋舊資料。

---

### 2.3 刪除飲食紀錄

P2 採用 soft delete，不直接刪除資料。

```json
{
  "status": "deleted",
  "deleted_at": "2026-07-06T20:00:00+08:00",
  "delete_reason": "使用者刪除錯誤紀錄"
}
```

查詢摘要時預設排除 deleted 紀錄。

---

### 2.4 圖表化分析

P2 Web UI 需要支援：

1. 每日熱量折線圖。
2. 蛋白質 / 脂肪 / 碳水堆疊圖。
3. 每週平均熱量。
4. 運動消耗趨勢。
5. 熱量攝取與 TDEE 對比。
6. 常見食物排行榜。

---

### 2.5 多使用者登入

P2 需導入登入機制，例如：

1. Google Sign-In。
2. Firebase Authentication。
3. Session token。
4. 每位使用者只能存取自己的資料。

---

### 2.6 餐廳 / 菜單資料擴充

P2 可加入餐廳資料：

```text
restaurants/{restaurantId}
restaurants/{restaurantId}/menu_items/{menuItemId}
```

支援：

1. 餐廳名稱搜尋。
2. 常見餐點對應熱量。
3. 使用者自建菜單。
4. 同一餐廳歷史紀錄參考。
5. Agent 根據店名提高辨識準確度。

---

## 3. P2 系統架構

```text
Web UI
  ↓
Auth Layer
  ↓
FastAPI / Cloud Run Backend
  ↓
ADK DietLoggerAgent
  ├── FoodImageAnalyzer
  ├── NutritionEstimator
  ├── RecordManager
  ├── ProfileManager
  ├── ExerciseLogger
  ├── AdviceGenerator
  ├── ChartDataGenerator
  └── RestaurantMenuResolver
  ↓
Nutrition MCP Server
  ↓
Restaurant / Menu Data Source
  ↓
Firestore / Cloud Storage
```

---

## 4. P2 Agent 模組

### 4.1 新增 ChartDataGenerator

職責：

1. 產生圖表用資料。
2. 整理每日 / 每週 / 每月趨勢。
3. 回傳前端可直接渲染的 chart-ready JSON。

---

### 4.2 新增 RestaurantMenuResolver

職責：

1. 根據餐廳名稱查詢已知菜單。
2. 根據歷史紀錄推測常見餐點。
3. 協助 FoodImageAnalyzer 提升判斷準確度。
4. 標記來源為 restaurant_menu 或 user_history。

---

### 4.3 RecordManager 擴充

P2 RecordManager 需支援：

1. create record。
2. read record。
3. update record。
4. soft delete record。
5. list revisions。
6. query by date range。
7. query by meal type。
8. query by restaurant。

---

## 5. P2 資料設計

### 5.1 Firestore Collection

```text
users/{userId}
users/{userId}/profiles/current
users/{userId}/meal_logs/{mealLogId}
users/{userId}/meal_logs/{mealLogId}/revisions/{revisionId}
users/{userId}/exercise_logs/{exerciseLogId}
users/{userId}/exercise_logs/{exerciseLogId}/revisions/{revisionId}
users/{userId}/daily_summaries/{yyyyMMdd}
users/{userId}/weekly_summaries/{yyyyWeek}
users/{userId}/monthly_summaries/{yyyyMM}
restaurants/{restaurantId}
restaurants/{restaurantId}/menu_items/{menuItemId}
```

---

### 5.2 Meal Log P2 Schema

```json
{
  "id": "meal_20260706_123000",
  "user_id": "user_abc",
  "date": "2026-07-05",
  "created_at": "2026-07-06T12:30:00+08:00",
  "updated_at": "2026-07-06T13:00:00+08:00",
  "meal_type": "dinner",
  "entry_type": "past_entry",
  "restaurant_name": "某某便當",
  "restaurant_id": "restaurant_001",
  "menu_item_name": "雞腿便當",
  "menu_item_id": "menu_001",
  "image_uri": "gs://bucket/path.jpg",
  "items": [],
  "total": {
    "calories_kcal": 820,
    "protein_g": 36,
    "fat_g": 28,
    "carbs_g": 98
  },
  "status": "active",
  "revision": 2,
  "readonly_sources": [],
  "agent_audit": {
    "used_tools": [],
    "warnings": []
  },
  "version": "p2"
}
```

---

### 5.3 Revision Schema

```json
{
  "revision_id": "rev_002",
  "meal_log_id": "meal_20260706_123000",
  "changed_at": "2026-07-06T13:00:00+08:00",
  "changed_by": "user_abc",
  "change_type": "update",
  "before": {
    "calories_kcal": 760
  },
  "after": {
    "calories_kcal": 820
  },
  "reason": "使用者修正雞腿便當熱量"
}
```

---

### 5.4 Restaurant Schema

```json
{
  "restaurant_id": "restaurant_001",
  "name": "某某便當",
  "location": "optional",
  "created_by": "user_abc",
  "created_at": "2026-07-06T10:00:00+08:00",
  "source": "user_created"
}
```

---

### 5.5 Menu Item Schema

```json
{
  "menu_item_id": "menu_001",
  "restaurant_id": "restaurant_001",
  "name": "雞腿便當",
  "estimated_nutrition": {
    "calories_kcal": 820,
    "protein_g": 36,
    "fat_g": 28,
    "carbs_g": 98
  },
  "source": "user_history",
  "confidence": 0.72
}
```

---

## 6. P2 API 規格

### 6.1 新增指定日期飲食紀錄

```text
POST /api/meals
```

Request：

```json
{
  "date": "2026-07-05",
  "meal_type": "dinner",
  "restaurant_name": "某某便當",
  "manual_items": [],
  "manual_calories_kcal": null
}
```

---

### 6.2 修改飲食紀錄

```text
PATCH /api/meals/{mealLogId}
```

Request：

```json
{
  "items": [
    {
      "name": "白飯",
      "weight_g": 120
    }
  ],
  "update_reason": "修正白飯重量"
}
```

Response：

```json
{
  "status": "success",
  "meal_log_id": "meal_20260706_123000",
  "revision": 2,
  "message": "已更新飲食紀錄，並保留修改歷史。"
}
```

---

### 6.3 刪除飲食紀錄

```text
DELETE /api/meals/{mealLogId}
```

Response：

```json
{
  "status": "success",
  "meal_log_id": "meal_20260706_123000",
  "deleted_at": "2026-07-06T20:00:00+08:00",
  "message": "已刪除紀錄。"
}
```

---

### 6.4 查詢圖表資料

```text
GET /api/charts/nutrition?range=week
```

Response：

```json
{
  "range": "week",
  "dates": ["2026-07-06", "2026-07-07"],
  "series": {
    "calories": [1800, 1750],
    "protein": [85, 78],
    "fat": [60, 58],
    "carbs": [210, 205],
    "exercise_calories": [250, 300]
  }
}
```

---

### 6.5 查詢修改歷史

```text
GET /api/meals/{mealLogId}/revisions
```

Response：

```json
{
  "meal_log_id": "meal_20260706_123000",
  "revisions": [
    {
      "revision": 1,
      "changed_at": "2026-07-06T12:30:00+08:00",
      "change_type": "create"
    },
    {
      "revision": 2,
      "changed_at": "2026-07-06T13:00:00+08:00",
      "change_type": "update"
    }
  ]
}
```

---

## 7. P2 權限與安全

P2 新增登入後，必須遵守：

1. 使用者只能讀取自己的飲食紀錄。
2. 使用者只能修改自己的飲食紀錄。
3. 所有修改都要建立 revision。
4. 刪除採 soft delete。
5. Agent 不可私自修改歷史資料。
6. 補登過去紀錄需標示為 past_entry。
7. 匯出資料時需由使用者主動觸發。
8. 圖片儲存位置不可公開暴露。
9. 若使用者刪除帳號，需規劃資料刪除流程。

---

## 8. P2 圖表與分析需求

### 8.1 今日 Dashboard

顯示：

1. 今日攝取熱量。
2. 今日運動消耗。
3. 今日淨熱量。
4. 今日蛋白質。
5. 今日脂肪。
6. 今日碳水。
7. 與目標的差距。

---

### 8.2 本週 Dashboard

顯示：

1. 每日熱量折線圖。
2. 每日蛋白質折線圖。
3. 運動次數統計。
4. 平均熱量。
5. 最常吃的食物。
6. 熱量最高的一餐。

---

### 8.3 本月 Dashboard

顯示：

1. 月平均熱量。
2. 月平均蛋白質。
3. 飲食穩定度。
4. 運動頻率。
5. 體重變化趨勢。
6. Agent 月總結。

---

## 9. P2 驗收標準

P2 完成時，必須能展示：

1. 使用者可登入。
2. 不同使用者資料互相隔離。
3. 使用者可補登過去飲食紀錄。
4. 使用者可修改飲食紀錄。
5. 修改後可查看 revision history。
6. 使用者可 soft delete 紀錄。
7. 今日 / 本週 / 本月摘要可產生圖表資料。
8. Agent 可根據餐廳名稱或歷史紀錄輔助判斷。
9. Agent 回覆仍保留資料來源。
10. 系統具備更完整的權限與安全限制。

---

## 10. P2 成功定義

P2 成功代表：

```text
TraceBite Agent 已從 Kaggle MVP 擴充為可長期使用的個人飲食紀錄產品原型。
```

P2 的核心價值是：

1. 可長期紀錄。
2. 可修正資料。
3. 可視覺化分析。
4. 可支援多使用者。
5. 可累積餐廳與菜單資料。
6. 可作為正式產品開發基礎。
