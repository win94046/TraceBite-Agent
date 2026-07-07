[繁體中文版](README_zh.md)

# TraceBite-Agent

TraceBite-Agent is an eating logger and nutrition estimation Agent (P0 MVP) developed based on the Google Agent Development Kit (ADK). Users can upload meal photos, input meal types and weights, and the Agent will identify the food, estimate calories and macro-nutrients, and store the meal logs in the database.

This guide will walk you through setting up your environment, configuring API keys, database settings, and starting the services.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step 1: Environment Variables Setup (.env)](#step-1-environment-variables-setup-env)
3. [Step 2: Database and Service Mode Selection](#step-2-database-and-service-mode-selection)
   - [Mode A: Physical GCP Firebase/Firestore Mode](#mode-a-physical-gcp-firebasefirestore-mode)
4. [Step 3: Install & Authorize Agent CLI](#step-3-install--authorize-agent-cli)
5. [Step 4: Start Project & Run Tests](#step-4-start-project--run-tests)
6. [Step 5: Deploy to Google Cloud Run](#step-5-deploy-to-google-cloud-run)

---

## 🛠 Prerequisites

Before starting, ensure that the following tools are installed in your environment:

- **Python**: Recommended version `>= 3.11` and `< 3.14`.
- **Git**: For version control.
- **uv (Highly Recommended)**: Modern Python package and environment manager. If you haven't installed `uv` yet, you can install it using the following commands:
  ```bash
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## Step 1: Environment Variables Setup (.env)

A template `.env.example` is provided in the project root. Please copy and rename it to `.env`:

```bash
cp .env.example .env
```

Next, edit the `.env` file to configure the necessary keys:

1. **Apply for Google Gemini API Key**:
   - Go to [Google AI Studio](https://aistudio.google.com/) to apply for an API Key (billing account binding required).
   - Fill in your obtained API key under `GEMINI_API_KEY` in the `.env` file:
     ```env
     GEMINI_API_KEY=your_actual_gemini_api_key_here
     ```
   - Fill in your corresponding Google Cloud project ID under `GCP_PROJECT_ID` in the `.env` file:
     ```env
     GCP_PROJECT_ID=your_gcp_project_id_here
     ```
   - Go to the Firebase official console (https://console.firebase.google.com/) and after logging in:
     1. Choose `Create a project` -> Select `Add Firebase to a Google Cloud project` -> Select the project named `GCP_PROJECT_ID` -> Choose `Continue` -> Choose `Create project`.
     2. Choose Database -> Choose `Create Database` for Firestore -> Choose `Start in test mode` -> Choose `Standard edition` -> Choose `default` as the Database ID and `nam5` as the location.
   - > ⚠️ **Important Security Note**: Never push your `.env` file containing real API keys to the Git repository. This file is already excluded in `.gitignore`.

---

## Step 2: Database and Service Mode Selection

TraceBite-Agent supports three databases and running modes. Select one based on your development needs:

### Mode A: Physical GCP Firebase/Firestore Mode
This mode is suitable for the final development phase, production deployment, or scenarios requiring real Firestore / Cloud Storage on Google Cloud.

1. **Prepare GCP Project and Services**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
   - Enable the **Firestore** service (use Test Mode) and **Cloud Storage**.
2. **Install Google Cloud SDK (gcloud CLI)**:
   - Follow the [Google Cloud SDK Installation Guide](https://cloud.google.com/sdk/docs/install) to install the `gcloud` command-line tool.
3. **Execute Login and Get Credentials**:
   - Run the following commands in your local terminal to log in and obtain Application Default Credentials (ADC):
     ```bash
     # Log in to gcloud
     gcloud auth login
     
     # Obtain Application Default Credentials to allow local Python code to call GCP permissions
     gcloud auth application-default login
     
     # Set the default working project ID
     gcloud config set project YOUR_GCP_PROJECT_ID
     ```
4. **Configure Environment Variables**:
   - Edit the `.env` file, turn off Mock mode, turn off (comment out) emulator environment variables, and fill in your GCP project information:
     ```env
     USE_MOCK_FIRESTORE=false
     GCP_PROJECT_ID=YOUR_GCP_PROJECT_ID
     GCP_LOCATION=global
     ```

---

## Step 3: Install & Authorize Agent CLI

This project uses `google-agents-cli` for local development, playground testing, and cloud deployment.

1. **Install Agent CLI**:
   - It is recommended to install it globally using `uv`:
     ```bash
     uv tool install google-agents-cli
     ```
2. **Execute Authorization and Login**:
   - Agent CLI needs to read your Google Cloud credentials to access Vertex AI / Agent Engine services or to deploy to Cloud Run.
   - Ensure that you have completed the ADC credential login in Step 2. If not, run in your project root:
     ```bash
     gcloud auth application-default login
     ```
   - You can run the following command to check your CLI installation and authentication status:
     ```bash
     agents-cli info
     ```
3. **Enable Vertex AI API**:
     ```bash
     gcloud services enable aiplatform.googleapis.com
     ```

---

## Step 4: Start Project & Run Tests

After completing the setup above, synchronize and install Python project dependencies and start the services:

1. **Synchronize and Install Dependencies**:
   - Run in the project root:
     ```bash
     uv sync
     ```
     *(This will automatically create a virtual environment `.venv` and install all dependencies defined in `pyproject.toml`)*

2. **Start the Development Server**:
   - Run the following command to start the FastAPI backend and web frontend:
     ```bash
     uv run python app/main.py
     ```
   - Open your browser and navigate to `http://localhost:8000` to interact with TraceBite-Agent through its Web UI.

3. **Run Unit and Integration Tests**:
   - You can verify whether your local environment is correctly configured by running:
     ```bash
     uv run pytest
     ```

---

## Step 5: Deploy to Google Cloud Run

This section provides the complete steps to containerize and deploy **TraceBite-Agent** to **Google Cloud Run**, establishing a publicly accessible URL for your serverless application.

### 5.1 Local Environment and gcloud CLI Preparation

Your local development machine must have the `gcloud` CLI installed.

#### A. Specify a Compatible Python Runtime
The macOS default Python version may not be supported by some GCP CLI tools. It is recommended to point the environment variable `CLOUDSDK_PYTHON` to a supported Python 3.10+ version installed on your machine, or directly point it to the virtual environment of this project:
```bash
export CLOUDSDK_PYTHON="<your-project-path>/.venv/bin/python"
```
> 💡 **Your actual local command**:
> ```bash
> export CLOUDSDK_PYTHON="/Users/yukai.chen/Desktop/TraceBite-Agent/.venv/bin/python"
> ```

#### B. Log in to your Google Cloud Account
Log in with your Google account that has permission to access the target GCP project:
```bash
# Generic command format (If gcloud is in your PATH, you can run gcloud directly)
$CLOUDSDK_PYTHON <your-gcloud-path>/gcloud auth login
```
> 💡 **Your actual local command**:
> ```bash
> $CLOUDSDK_PYTHON /Users/yukai.chen/google-cloud-sdk/bin/gcloud auth login
> ```

#### C. Set the Project ID
Set the active project to your Google Cloud project ID:
```bash
# List all available GCP projects
$CLOUDSDK_PYTHON <your-gcloud-path>/gcloud projects list

# Set the active project
$CLOUDSDK_PYTHON <your-gcloud-path>/gcloud config set project [YOUR_GCP_PROJECT_ID]
```
> 💡 **Your actual local command example**:
> ```bash
> $CLOUDSDK_PYTHON /Users/yukai.chen/google-cloud-sdk/bin/gcloud config set project [YOUR_GCP_PROJECT_ID]
> ```

---

### 5.2 Enable Required Google Cloud APIs

Deployment and execution require enabling GCP services for building, hosting, and AI. Enable them by running:
```bash
$CLOUDSDK_PYTHON <your-gcloud-path>/gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  aiplatform.googleapis.com
```
* **Artifact Registry**: Stores the compiled Docker container images.
* **Cloud Build**: Securely builds the source code into a container on Google Cloud.
* **Cloud Run**: Runs and hosts the serverless container.
* **Vertex AI (aiplatform)**: Allows the Agent to call Gemini securely using default Service Account permissions without exposing API keys.

---

### 5.3 Execute Cloud Run Deployment

We will use `gcloud run deploy` to upload the project to Cloud Build and deploy it.

#### Keyless Secure Deployment Command
To prevent API key leakage (such as exposing it in commands or showing it in the GCP console), **we do not pass `GEMINI_API_KEY`**. Instead, Cloud Run will automatically authenticate requests to Gemini through Vertex AI using the default service account:

```bash
$CLOUDSDK_PYTHON <your-gcloud-path>/gcloud run deploy tracebite-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="USE_MOCK_FIRESTORE=true,GCP_LOCATION=global"
```
> 💡 **Your actual local command**:
> ```bash
> $CLOUDSDK_PYTHON /Users/yukai.chen/google-cloud-sdk/bin/gcloud run deploy tracebite-agent \
>   --source . \
>   --region us-central1 \
>   --allow-unauthenticated \
>   --set-env-vars="USE_MOCK_FIRESTORE=true,GCP_LOCATION=global"
> ```
* `--source .`：Uploads the local source code to Cloud Build for containerization (we've updated the `Dockerfile` to include `COPY ./static ./static` to package the frontend assets).
* `--region us-central1`：Deploys the service in the US Central region.
* `--allow-unauthenticated`：Enables public access without login (required for Kaggle evaluation submission).
* `--set-env-vars`：
  * `USE_MOCK_FIRESTORE=true`：Enables the in-memory mock database to ensure smooth demonstration without DB setup bottlenecks.
  * `GCP_LOCATION=global`：Specifies the default Region for Vertex AI models.

#### ⚠️ Artifact Registry Prompt for First-time Deployments
If this is the first time you are deploying source code in this project and region, the terminal will display:
```text
Deploying from source requires an Artifact Registry Docker repository to store built containers. 
A repository named [cloud-run-source-deploy] in region [us-central1] will be created.

Do you want to continue (Y/n)?  
```
Type **`Y`** (and press Enter) to create the repository and continue the build process.

---

### 5.4 Verification and Access

Once the deployment completes, the terminal will display the Service URL:
```text
Service [tracebite-agent] revision [tracebite-agent-xxxx] has been deployed and is active.
Service URL: https://tracebite-agent-xxxxxx.us-central1.run.app
```

Open the `Service URL` in your browser to perform the following checks:
1. **Web UI**: Check if the webpage loads correctly (no blank pages).
2. **Multimodal Recognition**: Try uploading an image to verify food recognition.
3. **Dialogue**: Converse with the Agent and confirm the Markdown tables render correctly.