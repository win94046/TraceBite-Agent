# TraceBite-Agent: Personal Eating and Health Concierge Agent (Capstone Project Report)

## 1. Project Vision & Problem Definition

### 1.1 Pain Points Analysis
In modern busy life, diet management and health tracking have become essential yet difficult burdens to maintain. Traditional diet recording applications face three core pain points:
1. **Tedious Input**: Users must manually enter each food item's name and estimate weights. This tedious process frequently leads to users giving up halfway.
2. **Lack of Data Traceability**: Existing tools often provide a "black-box" calorie number. Users have no way of knowing whether the data comes from an authoritative database or a random guess, which reduces trust.
3. **Lack of Contextualized Advice**: Most tools stop at "recording" and fail to combine user physical attributes (e.g., height, weight, TDEE) and exercise logs to provide tailored health feedback with safe boundaries.

### 1.2 Project Vision & Roadmap
**TraceBite-Agent** aims to become the user's **"Personal Eating and Health Concierge Agent."** We have planned its development in three phases to gradually achieve seamless, personalized, and long-term health management:

- **P0 MVP (Current Implementation)**: Establish the core closed-loop of "photo/text quick logging ➔ multimodal AI food recognition ➔ authoritative database lookup & calculation ➔ today/weekly summary query," emphasizing data traceability and transparency.
- **P1 Personalized Context Advice (Future Expansion)**: Import user physical attributes (height, weight, age, activity level) to estimate Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE). Concurrently integrate daily exercise logs, using a dedicated Advice Agent to provide contextual, safe, and encouraging dietary feedback.
- **P2 Production Grade (Future Expansion)**: Support multi-user isolation (Firebase Auth), chart-based trend analysis (Dashboard), logging modification history version control (Revisions), and expansion of custom & restaurant menu databases for long-term health tracking.

---

## 2. Solution Design & Architecture

TraceBite-Agent's architectural design follows the principle of "high cohesion, low coupling," ensuring clear responsibilities for each module and leaving clean API extension interfaces for future P1/P2 functions.

```text
+-------------------------------------------------------------+
|                      Web UI (Vanilla JS)                    |
+-------------------------------------------------------------+
                              │  (HTTP / JSON API)
                              ▼
+-------------------------------------------------------------+
|                  Backend API (FastAPI / Python)             |
+-------------------------------------------------------------+
                              │  (Invokes ADK App Thread)
                              ▼
+-------------------------------------------------------------+
|                   ADK DietLoggerAgent Core                  |
+-------------------------------------------------------------+
         ├── Intent Classifier
         └── Tools Binding
               ├── FoodImageAnalyzer  (Gemini-2.5-Flash Multimodal Analysis)
               ├── NutritionEstimator (Taiwan Food Database Lookup/Scale)
               └── RecordManager      (Firestore / InMemory Dual DB)
```

> [!NOTE]
> `FoodImageAnalyzer`, `NutritionEstimator`, and `RecordManager` in the architecture diagram are logical modules. In the actual implementation, they map to the food recognition function `analyze_food_image()` in `image_analyzer.py`, the nutrition estimation function `estimate_nutrition()` in `nutrition_db.py`, and database helper functions in `db_manager.py`, respectively.

### 2.1 Technology Selection & Decisions
1. **Google Agent Development Kit (ADK)**: Serving as the agent's backbone, we leverage its high-level `Agent` and `App` wrappers to implement intent classification and tool routing. For the model configuration, the core `DietLoggerAgent` utilizes `gemini-flash-latest` (Gemini 1.5 Flash) as the reasoning engine to balance response speed and comprehension accuracy.
2. **Multimodal Image Recognition**: The image analysis tool (`image_analyzer.py`) calls the latest `gemini-2.5-flash` model, utilizing its leading vision capabilities to accurately identify various food items (e.g., rice, chicken drumstick, vegetables) from meal photos and estimate weights.
3. **Dual-Mode Database Design**: An `InMemory` Mock database is provided locally to allow E2E tests with 100% coverage without API keys, while the production environment easily switches to cloud **Firebase Firestore** to guarantee data persistence.

---

## 3. Implementation Details & Key Concepts Demonstration

This project implements and demonstrates five key concepts covered in the Capstone course during development.

### 3.1 Concept 1: ADK-based Agent System
We declared the core `DietLoggerAgent` using ADK, which automatically routes the user's natural language inputs to the corresponding Python tools:

- **Image Logging Tool (`log_meal`)**: When a user uploads a meal photo, the Agent extracts image bytes and calls Gemini for food identification and weight estimation.
- **Text Logging Tool (`log_meal_by_text`)**: When a user inputs text (e.g., "I just ate a bowl of rice"), the Agent identifies the intent and extracts parameters.
- **Query Tools (`query_today_summary` / `query_weekly_summary`)**: Automatically queries the database to calculate nutritional aggregates for today or the past seven days, rendering the results in a structured **Markdown Table**.

#### System Function & Data Flow (Meal Logging Flow)
```text
1. Image Upload Logging Flow:
+----------------+      POST /api/meals/today      +-------------------+
|   Web UI       | ------------------------------> |  fast_api_app.py  |
+----------------+                                 +-------------------+
                                                             │
                                                             │ Invokes log_meal()
                                                             ▼
+---------------------+     Invokes analyze_food_image() +-------------------+
|  image_analyzer.py  | <------------------------- |     agent.py      |
+---------------------+                            +-------------------+
        │ (Gemini 2.5 Flash Recognition)                     │
        ▼                                                    │ Invokes estimate_nutrition()
+-------------------+                                        ▼
| Detected Items    | ──────────────────────────────────> +-------------------+
| and Weights       |                                      |   nutrition_db.py |
+-------------------+                                      +-------------------+
                                                                     │ (Taiwan DB / Mock)
                                                                     ▼
+--------------------+               Invokes                +-------------------+
|   db_manager.py    | <────────────────────────────────── | Calculated Totals |
+--------------------+         save_meal_log()             +-------------------+
        │
        ├──> (Mock Mode) Writes to InMemoryMockDB, aggregates today's summary
        └──> (Real Mode) Writes to Firestore: users/{userId}/meal_logs
                          and users/{userId}/daily_summaries
```

### 3.2 Concept 2: Security & Defense Features
Diet tracking involves highly personal health data and potential recommendation risks. This project implements defensive design at multiple levels:
1. **Prompt-Level Guardrails**: The Agent System Instruction strictly prohibits the Agent from giving extreme weight-loss programs or medical prescriptions. Every summary response is appended with a mandatory disclaimer: `"This result is a general diet record and nutrition estimate, and does not replace the advice of a physician or nutritionist."`
2. **Key Management & Environment Isolation**: All API credentials (e.g., `GEMINI_API_KEY`) and database configurations are managed via a `.env` file and never committed to public Git repositories.
3. **Database-Level Protection**: The database logic in `db_manager.py` restricts log entries to the current date only, preventing historical database contamination (preparing a defense line for future P2 past-logging).
4. **Data Confusion & Security Vulnerabilities under Multi-User Environments (Current Limitations & Future Solutions)**:
   - **Current Problem**: In the P0/P1 MVP versions, to accelerate validation of the diet logger closed-loop, the database (Firestore) uses a fixed mock account (`demo_user`). If multiple end-users access this system simultaneously using the same physical Firebase project, everyone's meal logs and statistics will be written to the same `demo_user` node, leading to severe data confusion and privacy leakage.
   - **Future Solution**: In the future P2 production phase, we will introduce **Firebase Authentication** as a strict identity verification layer, rejecting all unauthorized writes. All API requests must carry a valid JWT Bearer Token in the HTTP Header. The backend will decrypt and extract the user's real `userId` to achieve strict physical data isolation in Firestore (e.g., `users/{userId}/meal_logs`). Firebase Security Rules will be configured to restrict read/write access to the account owner only, completely eliminating data confusion and unauthorized access risks.

### 3.3 Concept 3: Deployability
To ensure system usability and scalability, we performed cloud containerization:
1. **Dockerfile Packaging**: Packaged the backend FastAPI app and frontend static folder together, ensuring consistent execution across any Docker environment.
2. **GCP Cloud Run Deployment**: Deployed via Cloud Run for serverless execution, enabling auto-scaling to zero and configuring environment variables in the console for real database connection.
3. **GCP IAM & ADC**: Utilized GCP Application Default Credentials (ADC). When running on Cloud Run, the service automatically inherits Firestore read/write permissions from its Service Account, eliminating the need to hardcode database keys in the codebase.

### 3.4 Concept 4: MCP (Model Context Protocol) Development Practice
In the system architecture, because the Taiwanese food nutrition database is relatively stable, we chose to download and embed it locally for API multiplier calculation, achieving low network latency and offline testing capabilities. Consequently, we did not package this database query into a production-level MCP server.

However, **during the developer lifecycle, we deeply practiced the MCP ecosystem**. We integrated `context7` (context retrieval service) and `google-developer-knowledge` (Google Developer Knowledge Base MCP) via an MCP Client. When writing ADK tools and understanding API best practices, these MCP services provided cross-tool context links, accelerating agent business logic research.

### 3.5 Concept 5: Agent Skills in Developer Toolchain
Since this system is directly structured using Python and native Google ADK, the production Agent Runtime does not import additional dynamic Skills runtimes.

However, **during local development and pair programming, we extensively utilized dedicated Agent Skills**. For example, we enabled `code-trace-expert` to inspect the Agent's intent classification and Tool Call lifecycle, and used `google-agents-cli-adk` and `google-agents-cli-workflow` to retrieve ADK API code templates, guide local playground testing, and optimize deployment configurations. This demonstrates the power of Agent Skills as developer digital assistants.

---

## 4. User Value & Summary

### 4.1 Core User Value
- **Frictionless Experience**: Upload a meal photo to record calories and macros in one second, greatly lowering the barrier to diet tracking.
- **Traceability & Transparency**: Every log includes `readonly_sources`, explicitly marking whether the data comes from "user manual input," "multimodal AI vision," or the "Taiwan Food Database," resolving the "black box" calorie issue.
- **Seamless Scalability**: The development roadmap has reserved database paths for `users/{userId}/profiles` and `exercise_logs`. Once P1/P2 features are activated, personalized advice and exercise logging can be added without altering the database schema.

### 4.2 Project Summary
TraceBite-Agent successfully demonstrates how to use Google ADK combined with multimodal LLMs to simplify a complex daily health tracking task into an intuitive agent dialogue. We have built not only a high-availability MVP prototype but also a production-grade architecture in terms of security, data consistency, toolchain efficiency (MCP & Skills), and cloud deployability.
