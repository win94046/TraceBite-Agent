# TraceBite-Agent: 5-Minute YouTube Video Script (Capstone Project Video)

This document provides a complete bilingual video script and visual guideline for your 5-minute capstone project presentation video. It is designed to be spoken in English (VO) with Traditional Chinese visual descriptions to help you record easily.

---

## 🎬 Video Overview
- **Target Duration**: 4:30 - 5:00 Minutes (Max 5:00)
- **Voiceover Language**: English
- **Visual & Slide Language**: English (Subtitles can be added in both Chinese and English)

---

## ⏱️ Section 1: Pain Point & Project Vision (0:00 - 0:45)

| Time | Visual (畫面與操作) | Voiceover / Audio (英文口白與旁白) | Chinese Reference (中文對照口白) |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:15** | **Slide 1**: Title slide showing "TraceBite-Agent: Your Personal Eating & Health Concierge." A brief screen recording showing a user struggling to type meal weights into a traditional diet app. | Diet tracking is vital for personal health, yet traditional applications make it incredibly exhausting. Typing every single food item, guessing weights, and logging calories manually often leads to frustration. | 飲食記錄對健康至關重要，但傳統的 App 記錄起來卻非常繁瑣。手動輸入每樣食物、猜測重量和熱量，往往讓人中途放棄。 |
| **0:15 - 0:45** | **Slide 2**: Bullet points showing "P0: Eating Logger MVP" ➔ "P1: Personalized Context (BMR/TDEE & Exercise)" ➔ "P2: Multi-user Auth & Charts." | That's why we built **TraceBite-Agent**, a personal health concierge designed to make eating logging frictionless, transparent, and secure. Our roadmap expands from a P0 MVP photo-logger, to P1 personalized BMR/TDEE tracking, and ultimately to a P2 secure multi-user product. | 這就是我們開發 TraceBite-Agent 的原因。它是一個個人健康禮賓助理，旨在讓飲食記錄變得無感、透明且安全。我們的藍圖包含 P0 相片記錄 MVP、P1 個人化 BMR/TDEE 追蹤，以及 P2 的多使用者安全隔離。 |

---

## ⏱️ Section 2: Live Product Demonstration (0:45 - 2:00)

| Time | Visual (畫面與操作) | Voiceover / Audio (英文口白與旁白) | Chinese Reference (中文對照口白) |
| :--- | :--- | :--- | :--- |
| **0:45 - 1:20** | **Live Demo**: Open the Web UI deployed on Google Cloud Run. Drag and drop a photo of a Taiwanese bento (e.g., chicken leg, rice, vegetables). Select "Lunch" and click "Log Meal." The Agent responds with a beautiful Markdown table showing identified items, scaled macros, and the "Taiwan Food Database" source citation. | Let's see it in action. On our Web UI, simply upload a photo of your meal. The Agent automatically identifies the items, scales the macros based on weight, and logs it. Every record lists its source, such as the Taiwanese Food Database, ensuring complete traceability. | 讓我們來看看實際操作。在我們的 Web UI 上，只需上傳一張餐點照片。Agent 就會自動辨識食物項目、依重量計算營養素並予以記錄。每筆紀錄都附帶來源標示（如台灣食品資料庫），確保數據透明。 |
| **1:20 - 1:45** | **Live Demo**: Type: *"I just ate a bowl of white rice 150g for lunch"* in the Chat UI. The Agent invokes `log_meal_by_text` and appends the rice to today's lunch totals. | Don't have a photo? No problem. You can type in natural language. The Agent classifies your intent, extracts parameters like weight and meal type, and logs it instantly. | 沒有照片也沒關係，您可以直接用自然語言輸入。Agent 會識別您的意圖，提取重量與餐別，並立即為您完成記錄。 |
| **1:45 - 2:00** | **Live Demo**: Ask the Agent: *"How much did I eat today?"* or *"Show me my weekly summary."* The Agent displays today's totals and a 7-day average table. | You can easily review your history by asking the Agent for today's summary or your weekly trend. The Agent aggregates your logs and replies with a clean markdown table. | 您可以輕鬆詢問 Agent 今日的總量或本週趨勢。Agent 會彙整您的歷史日誌，並以乾淨的 markdown 表格回覆您。 |

---

## ⏱️ Section 3: Technical Architecture & Development with Antigravity (2:00 - 3:30)

| Time | Visual (畫面與操作) | Voiceover / Audio (英文口白與旁白) | Chinese Reference (中文對照口白) |
| :--- | :--- | :--- | :--- |
| **2:00 - 2:30** | **Slide 3 / Code Editor**: Show the system architecture diagram. Switch to Code Editor showing `app/agent.py` and `DietLoggerAgent` tool bindings. | Behind the scenes, TraceBite-Agent is structured on the **Google Agent Development Kit (ADK)**. We use ADK's intent classifier to route requests to specialized tools, including multimodal vision using `gemini-2.5-flash` for high-precision food recognition. | 在後台，TraceBite-Agent 是基於 Google Agent Development Kit (ADK) 建構的。我們利用 ADK 的意圖分類器將請求路由至特定工具，並呼叫最新的 `gemini-2.5-flash` 進行高精度的多模態影像辨識。 |
| **2:30 - 3:00** | **Code Editor / Dev Console**: Show the **Antigravity** interface. Explain how Antigravity (the AI Pair Programming assistant) helped co-author unit tests, verify database transactions, and inspect logs. | Our development was accelerated by the **Antigravity** developer platform. It acted as an active pair programmer, helping us co-author robust unit tests and ensure Firestore transactions operate seamlessly in a keyless environment. | 我們的開發過程是透過 Antigravity 平台進行協同編寫的。它扮演了積極的 AI 配對程式設計師，幫助我們共同編寫單元測試，並確保 Firestore 事務在免金鑰的環境下順暢運行。 |
| **3:00 - 3:30** | **Code Editor**: Show how we leveraged Agent Skills (e.g., `code-trace-expert` logs) and MCP clients during local development. | In the development lifecycle, we also utilized MCP clients like `context7` for documentation retrieval, and local Agent Skills such as `code-trace-expert` to trace tool calls and debug agent logic dynamically. | 在開發生命週期中，我們還利用 MCP 客戶端（如 `context7`）來檢索開發文件，並啟用本地的 `code-trace-expert` 技能來動態追蹤工具呼叫並除錯 Agent 邏輯。 |

---

## ⏱️ Section 4: Security & Deployability (3:30 - 4:30)

| Time | Visual (畫面與操作) | Voiceover / Audio (英文口白與旁白) | Chinese Reference (中文對照口白) |
| :--- | :--- | :--- | :--- |
| **3:30 - 4:00** | **Slide 4 / Terminal**: Show the system instructions in `agent.py` containing the disclaimer warning. Highlight the `.env` configuration and the Multi-user data confusion analysis. | Security and safety are central to our design. The Agent is bounded by prompt guardrails, enforcing a strict medical disclaimer. We also documented current multi-user data confusion risks in our report, designing a future Firebase Auth and Security Rules roadmap for data isolation. | 安全與防護是我們設計的核心。Agent 受到系統指令的保護，強制執行免責聲明。我們也在報告中記錄了多使用者資料混淆的潛在隱患，並規劃了未來以 Firebase Auth 進行資料隔離的藍圖。 |
| **4:00 - 4:30** | **GCP Console / Cloud Run**: Show the Cloud Run details page. Show the console terminal executing: `gcloud run deploy`. | For deployability, the FastAPI backend and Vanilla JS assets are packaged in a single Docker image and deployed to **Google Cloud Run**. It inherits Firestore permissions securely via GCP Service Accounts and Application Default Credentials, bypassing the need for hardcoded keys. | 在部署性方面，FastAPI 後端與網頁前台被打包成單一 Docker 映像檔並部署至 Google Cloud Run。它透過 GCP 服務帳戶與 ADC 機制安全地繼承了 Firestore 權限，無需在程式碼中寫死任何金鑰。 |

---

## ⏱️ Section 5: Future Outlook & Conclusion (4:30 - 5:00)

| Time | Visual (畫面與操作) | Voiceover / Audio (英文口白與旁白) | Chinese Reference (中文對照口白) |
| :--- | :--- | :--- | :--- |
| **4:30 - 5:00** | **Slide 5 / Conclusion**: Show the P1/P2 roadmap summary. Show the project GitHub link and Kaggle Capstone Project logo. | By integrating ADK, Multimodal Vision, and Cloud Run, TraceBite-Agent is not just a prototype, but a solid foundation for a next-generation personal health concierge. Thank you for watching, and let's make diet tracking smart and secure together! | 透過整合 ADK、多模態影像辨識與 Cloud Run，TraceBite-Agent 不僅僅是一個原型，更是下一代個人健康禮賓助理的堅實基礎。謝謝您的觀看，讓我們一起讓飲食記錄變得智慧且安全！ |
