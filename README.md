# TraceBite-Agent# TraceBite-Agent

TraceBite-Agent 是一個基於 Google Agent Development Kit (ADK) 開發的飲食紀錄與營養估算 Agent (P0 MVP)。使用者可以透過上傳餐點照片、輸入餐別與重量，由 Agent 進行食物辨識並估算熱量與三大營養素，並將飲食紀錄儲存至資料庫中。

本指南將引導您從剛 Clone 下來專案開始，一步步完成所有環境準備、API 金鑰配置、資料庫設定與服務啟動。

---

## 📋 目錄
1. [事前準備](#-事前準備)
2. [步驟 1：環境變數設定 (.env)](#步驟-1環境變數設定-env)
3. [步驟 2：資料庫與服務運行模式選擇](#步驟-2資料庫與服務運行模式選擇)
   - [模式 A：實體 GCP Firebase/Firestore 模式](#模式-a實體-gcp-firebasefirestore-模式)
4. [步驟 3：安裝與授權 Agent CLI](#步驟-3安裝與授權-agent-cli)
5. [步驟 4：啟動專案與執行測試](#步驟-4啟動專案與執行測試)

---

## 🛠 事前準備

在開始前，請確保您的開發環境已安裝以下工具：

- **Python**: 建議版本為 `>= 3.11` 且 `< 3.14`。
- **Git**: 用於版本管理。
- **uv (強烈推薦)**: 現代化 Python 套件與環境管理器。如果您尚未安裝 `uv`，可以使用以下指令快速安裝：
  ```bash
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## 步驟 1：環境變數設定 (.env)

專案根目錄下附帶了環境變數範本 `.env.example`。請將其複製並重新命名為 `.env`：

```bash
cp .env.example .env
```

接著，編輯 `.env` 檔案以配置必要金鑰：

1. **申請 Google Gemini API 金鑰**：
   - 請前往 [Google AI Studio](https://aistudio.google.com/) 申請`綁定帳單帳戶`的 API Key。
   - 將取得的 API 金鑰填入 `.env` 中的 `GEMINI_API_KEY` 欄位：
     ```env
     GEMINI_API_KEY=your_actual_gemini_api_key_here
     ```
   - 將對應的Project ID 填入 `.env` 中的 `GCP_PROJECT_ID` 欄位：
     ```env
     GCP_PROJECT_ID=your_gcp_project_id_here
     ```
   - 到firebase 官方網站 https://console.firebase.google.com/，登入後:
   1. 選擇`建立新的專案`->選擇`將 Firebase 新增到 Google Cloud 專案` ->選擇`GCP_PROJECT_ID`名稱的專案->選擇`繼續`->選擇`建立專案`
   2. 選擇database->選擇`建立firestore`->選擇`standard edition`-> `Database id` 選擇 `default` , `location` 選擇 `nam5` -> 選擇`test mode`
   
   - > ⚠️ **重要安全提示**：請勿將含有真實 API Key 的 `.env` 檔案推送至 Git 儲存庫。本專案已在 `.gitignore` 中將 `.env` 排除。

---

## 步驟 2：資料庫與服務運行模式選擇

TraceBite-Agent 支援三種資料庫與運行模式。請根據您的開發需求選擇其中一種進行設定：

### 模式 A：實體 GCP Firebase/Firestore 模式
此模式適用於開發尾聲、產品部署或需要使用真實雲端 Firestore / Cloud Storage 的情境。

1. **準備 GCP 專案與服務**：
   - 請前往 [Google Cloud Console](https://console.cloud.google.com/) 建立一個專案。
   - 啟用 **Firestore** 服務（請選用 TEST 模式）與 **Cloud Storage**。
2. **安裝 Google Cloud SDK (gcloud CLI)**：
   - 請依照 [Google Cloud SDK 安裝指南](https://cloud.google.com/sdk/docs/install) 在本機安裝 `gcloud` 命令行工具。
3. **執行授權登入取得憑證**：
   - 在您的本機終端機中執行以下指令進行帳號登入與 Application Default Credentials (ADC) 授權取得：
     ```bash
     # 登入 gcloud
     gcloud auth login
     
     # 取得應用程式預設憑證，讓本地 Python 程式碼能自動調用您的 GCP 權限
     gcloud auth application-default login
     
     # 設定預設工作專案
     gcloud config set project YOUR_GCP_PROJECT_ID
     ```
4. **設定環境變數**：
   - 編輯 `.env` 檔案，關閉 Mock 模式，關閉（註解掉）模擬器環境變數，並填入您的 GCP 專案資訊：
     ```env
     USE_MOCK_FIRESTORE=false
     GCP_PROJECT_ID=YOUR_GCP_PROJECT_ID
     GCP_LOCATION=global
     

---

## 步驟 3：安裝與授權 Agent CLI

本專案使用 `google-agents-cli` 來進行本地開發、Playground 測試與雲端部署。

1. **安裝 Agent CLI**：
   - 推薦使用 `uv` 進行全域安裝：
     ```bash
     uv tool install google-agents-cli
     ```
2. **在專案中執行授權登入**：
   - Agent CLI 需要讀取您的 Google Cloud 憑證以便存取 Vertex AI / Agent Engine 服務或進行 Cloud Run 部署。
   - 請確保您已在步驟 2（模式 C）中完成了 ADC 憑證登入。如果尚未執行，請在專案目錄下執行：
     ```bash
     gcloud auth application-default login
     ```
   - 您可以執行以下指令來確認 CLI 安裝與認證狀態：
     ```bash
     agents-cli info
     ```
3. Enable Vertex AI API
     ```bash
     gcloud services enable aiplatform.googleapis.com
     ```
---

## 步驟 4：啟動專案與執行測試

完成上述設定後，即可同步安裝 Python 專案依賴並啟動服務：

1. **同步安裝專案相依套件**：
   - 在專案根目錄下執行：
     ```bash
     uv sync
     ```
     *(這會自動建立一個虛擬環境 `.venv` 並安裝 `pyproject.toml` 中的所有相依套件)*

2. **啟動開發伺服器**：
   - 執行以下指令啟動 FastAPI 後端與網頁前端：
     ```bash
     uv run python app/main.py
     ```
   - 伺服器啟動後，開啟瀏覽器瀏覽 `http://localhost:8000`，即可使用 TraceBite-Agent 的 Web UI 介面進行操作與對話。

3. **執行單元與整合測試**：
   - 您可以透過以下指令來驗證本機環境是否已設定正確，所有測試是否皆能通過：
     ```bash
     uv run pytest
     ```