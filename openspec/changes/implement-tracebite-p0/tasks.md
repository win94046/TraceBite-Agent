## 1. 專案初始化與相依性設定

- [ ] 1.1 安裝專案所需套件，包括 FastAPI, Uvicorn, Firebase Admin SDK 與 Google ADK 相關套件
- [ ] 1.2 設定 Firebase Firestore 與 Cloud Storage 的本地模擬器 (Emulator) 或開發環境
- [ ] 1.3 設計並建立共用日誌模組 (Logger)，設定同時輸出至 Console 與專案根目錄下的 `tracebite_agent.log` 文字檔

## 2. 營養庫與圖片辨識工具實作

- [ ] 2.1 實作本地台灣常見便當食材的營養庫，提供 search_food 與 estimate_nutrition 查詢 API
- [ ] 2.2 實作 Food Image Analysis Tool 模擬圖片辨識邏輯，從上傳圖片推測食物名稱與信心度

## 3. 資料庫儲存與查詢邏輯

- [ ] 3.1 實作 meal_logs 寫入邏輯，驗證日期限制（僅限今日日期），否則拒絕
- [ ] 3.2 實作 daily_summaries 更新邏輯，於寫入飲食紀錄時自動累加當日營養素
- [ ] 3.3 實作本週與今日飲食紀錄的讀取邏輯，以提供摘要查詢

## 4. ADK Agent 實作

- [ ] 4.1 建立 DietLoggerAgent，撰寫 System Prompt 與意圖分類邏輯
- [ ] 4.2 整合 Agent 工具呼叫，使其能串接圖片分析、營養查詢與資料庫寫入工具
- [ ] 4.3 確保 Agent 回覆包含資料來源 (readonly_sources) 與醫療免責聲明
- [ ] 4.4 在 Agent 意圖判斷、各工具呼叫（圖片分析、營養庫查詢、寫入資料庫）等關鍵函數中實作詳細日誌記錄

## 5. FastAPI 後端 API

- [ ] 5.1 實作 POST /api/meals/today 端點，處理 multipart/form-data 照片上傳並呼叫 Agent 處理
- [ ] 5.2 實作 GET /api/summary/today 端點，讀取今日的每日摘要與每餐明細
- [ ] 5.3 實作 GET /api/summary/week 端點，讀取本週的每日總量並計算週平均
- [ ] 5.4 於所有 API 端點實作請求接收 (Request) 與回傳結果 (Response) 的日誌記錄

## 6. 前端 Web UI 實作

- [ ] 6.1 使用 HTML & CSS 建立具有現代設計感、響應式的單頁應用程式介面
- [ ] 6.2 實作 JavaScript 串接 API，包括照片上傳、今日摘要與本週摘要之非同步更新與展示

## 7. 驗證與測試

- [ ] 7.1 撰寫端對端測試腳本，測試上傳照片、限制非今日紀錄、查詢今日與本週摘要之流程
