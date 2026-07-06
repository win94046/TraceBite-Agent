## Why

建立一個最小可交付的 TraceBite Agent MVP，目標是在最短時間內實現核心飲食紀錄的閉環：使用者上傳今日餐點照片，經由 Agent 辨識食物內容並估算熱量與三大營養素，最後儲存紀錄，並支援查詢今日與本週的飲食摘要，提供可追溯的資料來源與 ADK Agent 工作流展示。

## What Changes

- 新增 `DietLoggerAgent`：基於 Google ADK 框架，負責理解使用者意圖（紀錄或查詢）並呼叫相關工具。
- 新增 `Food Image Analysis Tool`：用於解析使用者上傳的食物照片並辨識食物項目。
- 新增 `Nutrition Tools`：提供食物搜尋、營養成分查詢與熱量估算工具，支援自建台灣食品營養成分資料庫、USDA 等來源。
- 新增 `Meal Database`：整合 Firestore 儲存每日飲食紀錄與摘要，並利用 Cloud Storage 儲存食物照片。
- 新增 `Web UI & FastAPI Backend`：提供前端網頁供使用者上傳照片與點擊查詢，並由 FastAPI 後端提供對應的 API 端點。
- 保留擴充接口：在資料結構與 API 設計中，保留使用者個人 Profile、運動紀錄、過去日期紀錄、紀錄修改與圖表格式的擴充空間。

## Capabilities

### New Capabilities
- `diet-logger-agent`: DietLoggerAgent 的意圖理解、工具呼叫與可追溯結果回覆。
- `nutrition-tools`: 營養資料庫查詢、食物搜尋與基於重量的熱量與三大營養素估算。
- `meal-database`: 使用 Firestore 儲存與讀取飲食紀錄 (meal_logs) 與每日摘要 (daily_summaries)。
- `user-interface`: 網頁前端介面與後端 API 端點，支援照片上傳、餐別選擇、手動重量/熱量輸入與摘要查詢。

### Modified Capabilities
<!-- 無變更的現有 Capability，因為這是初始專案 -->

## Impact

- **新增相依性**：引進 Google ADK、FastAPI、Firebase Admin SDK、Firestore、Cloud Storage。
- **資料庫**：需設定 Firebase Firestore 與 Cloud Storage 儲存桶。
- **API 變更**：新增 `/api/meals/today`、`/api/summary/today`、`/api/summary/week` 三個 API 端點。
