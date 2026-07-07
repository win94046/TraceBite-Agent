## Context

目前專案剛初始化，尚無飲食紀錄相關功能。我們將基於「TraceBite Agent P0 開發規格書」建立一個最小可行性產品 (MVP)，整合 Google ADK 框架、FastAPI 後端、Firestore 與 Cloud Storage 儲存，並提供一個前端 Web UI 作為 Demo 展示。

## Goals / Non-Goals

**Goals:**
- **ADK Agent (DietLoggerAgent)**：能根據使用者意圖呼叫圖片分析、營養查詢與資料庫儲存工具，並回覆可追溯的資訊。
- **飲食紀錄與摘要儲存**：在 Firestore 中建立 `meal_logs` 與 `daily_summaries` 集合，並在 Cloud Storage 儲存食物照片。
- **API 提供**：新增今日飲食紀錄、查詢今日摘要、查詢本週摘要。
- **Web UI**：支援照片上傳、手動輔助欄位輸入（餐別、店家名稱、重量、熱量）以及顯示今日/本週飲食概況。
- **保留擴充接口**：在資料 Schema 與邏輯中預留 Profile、運動紀錄、過去日期限制與修改軌跡欄位。

**Non-Goals:**
- **使用者登入 (Auth)**：暫不實作，在 P0 中固定使用 `userId = "demo_user"`，但保留欄位。
- **紀錄修改與刪除**：僅限新增與查詢，唯讀資料來源。
- **補登過去紀錄**：限制僅能登錄今日紀錄。
- **個人化 TDEE 建議**：只顯示攝取量統計，不做達標與否的個人化評估。

## Decisions

### 1. 採用 Google ADK 框架實作 Agent
- **說明**：使用 Google Agent Development Kit (ADK) 實作 `DietLoggerAgent`。
- **原因**：ADK 提供了定義工具 (Tools)、管理 Agent 狀態與呼叫大語言模型的標準流程，未來若要擴充 P1/P2 的個人化建議、運動整合等功能，使用 ADK 能夠輕易地添加新 Tool 與優化 Prompt。
- **替代方案**：使用 LangChain 或純 API 呼叫。相較之下，ADK 與 Gemini 生態有更優雅的整合且程式碼更為精簡。

### 2. 使用 Firebase (Firestore & Cloud Storage) 儲存資料
- **說明**：資料庫選用 Cloud Firestore，照片儲存選用 Cloud Storage。
- **原因**：Firestore 的 NoSQL 結構非常適合儲存如 `meal_logs` 這種含有多個偵測項目 (`detected_items`) 且未來可能動態變更 schema 的資料；Cloud Storage 則方便儲存照片，且皆易於部署於 Google Cloud。
- **替代方案**：PostgreSQL 或 MongoDB。由於是 MVP，Firebase 可快速免設定起步。

### 3. 使用 FastAPI 作為後端 API 框架
- **說明**：以後端服務轉接 Web UI 請求至 ADK Agent，API 端點為 FastAPI。
- **原因**：FastAPI 提供非同步支援、快速的 Pydantic 驗證，並內建 Swagger UI，方便開發與偵測。

### 4. 營養庫使用本地自建對照表與 Mock 實作
- **說明**：自建一個包含台灣常見便當食材（如白飯、滷肉、雞腿、排骨、滷蛋等）的營養資料庫，並提供 MCP 或 Tool 介面查詢。
- **原因**：避免 MVP 階段因外部 API（如 USDA 或台灣食品成分資料庫 API）不穩定或需要密鑰而阻礙開發與測試。

### 5. 實作執行過程與 API 的日誌紀錄 (Logging)
- **說明**：使用 Python 內建的 `logging` 模組，設定日誌同時輸出至主控台 (Console) 與本地文字檔（例如專案根目錄下的 `tracebite_agent.log`
  文字檔）。
- **原因**：關鍵函數（特別是 API 的請求接收與回傳、Agent 工作流、工具執行與資料庫存取）在開發與執行時若出現問題，有詳細的 Trace Log
  將有助於 Agent 與開發者快速定位錯誤、追蹤原因，符合日誌追蹤實踐 (Logging Practice)。

### 6. 測試驅動與 API 金鑰管理
- **說明**：
  1. 每一開發階段均必須先撰寫對應的單元測試 (Unit Test)，確保單元測試通過後，才可繼續進行下一個階段的開發。
  2. 當測試或執行需要 API 金鑰（例如呼叫 Gemini API）時，系統必須自 `.env` 檔案中讀取該環境變數。若缺少金鑰，Agent 必須主動告知使用者並說明如何設置 `.env` 檔案，嚴禁主動跳過或將金鑰寫死於程式碼中。

## Risks / Trade-offs

- **[照片辨識不準確]** → 介面提供「手動輸入重量/熱量」的輔助欄位，若使用者有輸入則以使用者輸入優先；在 Agent 回覆與 UI 上警示「熱量為估算值，實際數值可能因份量、醬料與烹調方式不同而變動」。
- **[Firestore 查詢效能]** → 對於本週摘要的查詢，若逐日讀取明細會增加讀取次數，P0 會建立 `daily_summaries` 集合，在新增飲食紀錄時同時利用 Cloud Function 邏輯或 Backend 邏輯更新當日總量，減少查詢負擔。
- **[本地營養庫涵蓋不足]** → 當查無特定食材時，工具將回傳估算值並於 `detected_items` 的 `confidence` 中給予較低信心度，並在資料來源中註記。
