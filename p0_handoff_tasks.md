# TraceBite Agent P0 - 下階段交接與部署任務清單

本文件為下一個接手的 Agent 準備，用以說明目前的 P0 MVP 開發進度，並條列接下來需要接續執行的部署、真實 AI 對接與雲端整合任務。

---

## 1. 目前專案完工狀態與架構

目前的 P0 核心業務代碼與 Web UI 已經開發完成。在 `USE_MOCK_FIRESTORE=true`（無金鑰沙盒模式）下，所有的工具、資料庫、API 以及 E2E 測試皆已 **100% 執行通過**。

### 目前系統資料流架構 (Data Flow)

```text
[ 前端 Web UI (static/) ] ──────> [ FastAPI 後端 API ] ──────> [ log_meal() 業務層 ]
                                                                      │
                                                ┌─────────────────────┴─────────────────────┐
                                                ▼ (偵測金鑰: 有)                              ▼ (偵測金鑰: 無/測試)
                                       【 真實 AI 模式 】                             【 本地 Mock 模式 】
                                         - 呼叫 gemini-2.5-flash 看圖辨識                - 根據檔名關鍵字比對食物
                                         - 取得精確 AI 估算項目與重量                    - (雞腿/白飯/青菜)
                                                │                                             │
                                                └─────────────────────┬───────────────────────┘
                                                                      v
                                                        [ nutrition_db.py 查表 & 乘算 ]
                                                                      │
                                                                      v
                                                        [ db_manager.py 資料庫寫入 ]
                                                          - 限制僅能記錄今日日期
                                                          - 寫入明細，並累加更新今日/本週統計
                                                                      │
                                                                      v
                                                       [ mock_db 或雲端 Firestore ]
```

---

## 2. 接續執行的任務清單 (TODO List)

接手的 Agent 需要執行以下任務，將專案從「本地沙盒 Mock 測試」推向「真實 AI 運行與雲端部署」：

### 任務 1：配置真實環境金鑰與憑證
*   **說明**：
    *   在專案根目錄的 [`.env`](file:///Users/yukai.chen/Desktop/TraceBite-Agent/.env) 檔案中，將 `GEMINI_API_KEY` 替換為真實的 Google AI Studio 金鑰。
    *   若是需要關閉 Mock 模式並對接真實的 Firebase，請配置 GCP Application Default Credentials (ADC) 或在本地下載 Firebase 服務帳號金鑰並設定 `GOOGLE_APPLICATION_CREDENTIALS` 變數。
*   **依賴關係**：無

### 任務 2：執行真實 AI 與多模態圖片分析測試
*   **說明**：
    *   金鑰填入後，開啟 [`tests/test_agent.py`](file:///Users/yukai.chen/Desktop/TraceBite-Agent/tests/test_agent.py)，將 `test_agent_api_key_and_run` 中原本預期因無金鑰而主動 `pytest.fail` 的防禦性代碼移除。
    *   放入一張真實的雞肉或便當圖片到測試目錄。
    *   執行 `.venv/bin/pytest tests/test_agent.py`，驗證實體 Gemini API 是否能成功連線，且辨識出的 JSON 能正確解析回傳。
*   **依賴關係**：任務 1

### 任務 3：關閉 Mock 並對接實體 Firestore 資料庫
*   **說明**：
    *   將 [`.env`](file:///Users/yukai.chen/Desktop/TraceBite-Agent/.env) 中的 `USE_MOCK_FIRESTORE` 設為 `false`。
    *   啟動本地的 Firebase Emulator（模擬器），或直接連線到實體雲端專案的 Firestore 中。
    *   執行 `.venv/bin/pytest tests/test_db.py`，驗證飲食日誌的寫入與每日統計的累加在真實的 Firestore Collections（`meal_logs` 與 `daily_summaries`）中運作完全無誤。
*   **依賴關係**：任務 1

### 任務 4：本機整合運行與手動 E2E 測試
*   **說明**：
    *   本機執行服務：`python -m app.main`
    *   開啟瀏覽器至 `http://127.0.0.1:8000`。
    *   手動上傳不同食物的真實照片，不要在檔名中加任何提示（如直接上傳 `my_dinner.jpg`），驗證 Gemini-Flash 視覺模型是否能成功辨識出盤中食物並查表精算出卡路里。
*   **依賴關係**：任務 2, 任務 3

### 任務 5：部署至雲端開發環境 (GCP / Cloud Run)
*   **說明**：
    *   確認專案根目錄的 [`Dockerfile`](file:///Users/yukai.chen/Desktop/TraceBite-Agent/Dockerfile) 已封裝了所有後端代碼與 `static/` 靜態目錄。
    *   執行 `agents-cli deploy`（如果適用）或是使用 GCP Cloud Build & Cloud Run 將容器部署上線。
    *   配置 Cloud Run 上的環境變數 `GEMINI_API_KEY` 與 Firestore 權限。
*   **依賴關係**：任務 4
