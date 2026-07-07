[English Version](README.md)

# TraceBite-Agent

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
6. [步驟 5：部署至 Google Cloud Run](#步驟-5部署至-google-cloud-run)

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
     ```

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

---

## 步驟 5：部署至 Google Cloud Run

本節提供將 **TraceBite-Agent** 打包並部署至 **Google Cloud Run** 的完整流程，幫助您建立具備公開存取網址的無伺服器應用程式。

### 5.1 本機環境與 gcloud CLI 準備

您的開發本機必須已安裝 `gcloud` CLI。

#### A. 指定符合版本的 Python 執行環境
macOS 系統預設的舊版 Python 可能無法被部分 GCP CLI 工具支持。建議將環境變數 `CLOUDSDK_PYTHON` 指向您本機已安裝且支援的 Python 3.10+ 版本，或直接使用本專案虛擬環境中的 Python 執行檔：
```bash
export CLOUDSDK_PYTHON="<您的專案路徑>/.venv/bin/python"
```
> 💡 **您本機的實際指令**：
> ```bash
> export CLOUDSDK_PYTHON="/Users/yukai.chen/Desktop/TraceBite-Agent/.venv/bin/python"
> ```

#### B. 登入 Google Cloud 帳戶
使用具備您 GCP 專案權限的 Google 帳號完成登入：
```bash
# 通用指令形式 (若 gcloud 已在您的環境變數中，可直接執行 gcloud)
$CLOUDSDK_PYTHON <您的gcloud路徑>/gcloud auth login
```
> 💡 **您本機的實際指令**：
> ```bash
> $CLOUDSDK_PYTHON /Users/yukai.chen/google-cloud-sdk/bin/gcloud auth login
> ```

#### C. 設定工作專案 ID
請將工作目標設定為您的 GCP 專案 ID：
```bash
# 列出所有可用的 GCP 專案
$CLOUDSDK_PYTHON <您的gcloud路徑>/gcloud projects list

# 設定當前工作專案
$CLOUDSDK_PYTHON <您的gcloud路徑>/gcloud config set project [您的_GCP_PROJECT_ID]
```
> 💡 **您本機的實際指令範例**：
> ```bash
> $CLOUDSDK_PYTHON /Users/yukai.chen/google-cloud-sdk/bin/gcloud config set project [您的_GCP_PROJECT_ID]
> ```

---

### 5.2 啟用必要的 Google Cloud API

部署與運行需要啟用 GCP 的容器建置、託管與 AI 服務。請執行以下指令一鍵啟用：
```bash
$CLOUDSDK_PYTHON <您的gcloud路徑>/gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  aiplatform.googleapis.com
```
* **Artifact Registry**：用來儲存編譯好的 Docker 容器映像檔。
* **Cloud Build**：在雲端將原始碼安全編譯為容器。
* **Cloud Run**：執行與託管該無伺服器容器。
* **Vertex AI (aiplatform)**：讓 Agent 能夠以內建 Service Account 權限安全呼叫 Gemini 進行多模態辨識與對話，無需明文暴露 API Key。

---

### 5.3 執行 Cloud Run 部署

我們將使用 `gcloud run deploy` 將專案上傳至雲端編譯並部署。

#### 免金鑰安全部署指令
為避免金鑰洩漏風險（如在指令中明文暴露或在 GCP 主控台呈現金鑰），**我們不傳送 `GEMINI_API_KEY`**。Cloud Run 執行時會自動以預設服務帳戶的權限，透過 Vertex AI 來安全地呼叫 Gemini：

```bash
$CLOUDSDK_PYTHON <您的gcloud路徑>/gcloud run deploy tracebite-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="USE_MOCK_FIRESTORE=true,GCP_LOCATION=global"
```
> 💡 **您本機的實際指令**：
> ```bash
> $CLOUDSDK_PYTHON /Users/yukai.chen/google-cloud-sdk/bin/gcloud run deploy tracebite-agent \
>   --source . \
>   --region us-central1 \
>   --allow-unauthenticated \
>   --set-env-vars="USE_MOCK_FIRESTORE=true,GCP_LOCATION=global"
> ```
* `--source .`：將本地原始碼上傳至 Cloud Build 進行雲端編譯（我們已在 `Dockerfile` 中加入了 `COPY ./static ./static` 以確保前台資源一同被打包）。
* `--region us-central1`：部署在美中區域。
* `--allow-unauthenticated`：允許公開免登入存取（符合 Kaggle 評審提交展示要求）。
* `--set-env-vars`：
  * `USE_MOCK_FIRESTORE=true`：開啟記憶體模擬資料庫，確保 Demo 運作不受資料庫設定限制。
  * `GCP_LOCATION=global`：指定 Vertex AI 的預設模型區域。

#### ⚠️ 第一次部署時的 Artifact Registry 詢問
若這是您在該專案與區域第一次進行原始碼部署，終端機將出現以下提示：
```text
Deploying from source requires an Artifact Registry Docker repository to store built containers. 
A repository named [cloud-run-source-deploy] in region [us-central1] will be created.

Do you want to continue (Y/n)?  
```
此時請輸入 **`Y`**（按 Enter 鍵確認），系統便會自動在 GCP 上建立存放庫並繼續編譯與部署。

---

### 5.4 驗證與存取

部署成功後，終端機將顯示服務 URL：
```text
Service [tracebite-agent] revision [tracebite-agent-xxxx] has been deployed and is active.
Service URL: https://tracebite-agent-xxxxxx.us-central1.run.app
```

請使用該 `Service URL` 開啟瀏覽器進行以下功能驗證：
1. **網頁介面**：確認網頁載入正常，無空白頁面。
2. **多模態食物辨識**：嘗試上傳圖片，驗證 Gemini-Flash 食物辨識是否順暢。
3. **對話功能**：與 Agent 對話，確認 Markdown 表格在前端正常渲染。
