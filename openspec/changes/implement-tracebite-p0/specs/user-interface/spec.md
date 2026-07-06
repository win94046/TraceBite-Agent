## ADDED Requirements

### Requirement: 後端 API 提供
系統 SHALL 提供三個 FastAPI 端點，用於新增今日飲食紀錄與查詢摘要：
1. `POST /api/meals/today`：接收餐別、店家名稱、手動輸入項目、照片檔案，並回傳儲存後的估算摘要。
2. `GET /api/summary/today`：回傳今日的總熱量、三大營養素與餐點列表。
3. `GET /api/summary/week`：回傳本週的每日熱量統計、週平均值與常用食物項目。

#### Scenario: 成功呼叫今日紀錄新增端點
- **WHEN** 發送 multipart/form-data 請求至 `/api/meals/today`，帶有餐照片與餐別 "lunch"
- **THEN** API 回傳狀態 "success" 與新增的紀錄 ID 及營養估算摘要

---

### Requirement: 前端網頁介面
Web UI SHALL 提供直覺的表單讓使用者上傳食物照片、選擇餐別（breakfast / lunch / dinner / snack）、輸入便當店名稱與手動輸入食物重量或已知熱量，並設有「今日摘要」與「本週摘要」查詢按鈕。

#### Scenario: 成功提交飲食表單並顯示結果
- **WHEN** 使用者上傳照片、選擇餐別並點擊「送出紀錄」
- **THEN** 網頁顯示 Agent 估算的今日熱量與三大營養素，並顯示免責聲明與資料來源

---

### Requirement: API 接收與寄送之日誌紀錄
後端 API 在接收到任何 HTTP 請求時（如新增紀錄、查詢摘要），SHALL 紀錄傳入的關鍵參數；在發送 Response 回傳給前端時，SHALL 紀錄回傳的狀態碼與主要資料摘要。所有此類日誌 MUST 寫入至本地日誌檔案。

#### Scenario: 成功紀錄新增飲食紀錄 API 的輸入與輸出
- **WHEN** 呼叫 `POST /api/meals/today`
- **THEN** 系統於本地日誌檔寫入請求的 Form 欄位（如餐別、店家名稱）與回傳的 Response 內容（如新增紀錄 ID 與總熱量）

