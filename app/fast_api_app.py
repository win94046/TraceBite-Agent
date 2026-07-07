import os
import shutil
import uuid
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app
from app.utils.logger import logger
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 導入我們的資料庫與 Agent 參數
from app.database.db_manager import get_today_summary, get_weekly_summary, get_today_date_str
from app.agent import log_meal, root_agent

# 取得包含 ADK 路由的 FastAPI 應用程式
app = get_fast_api_app(agents_dir=".", web=True)

# 確保照片暫存的 uploads 目錄存在
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 初始化用來持久化對話狀態的 Session 服務
session_service = InMemorySessionService()

@app.on_event("startup")
async def startup_event():
    """
    FastAPI 啟動時的初始化任務。
    """
    logger.info("[Startup] 系統啟動中...")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    """
    與 DietLoggerAgent 對話的 API 路由，內部以 ADK Runner 驅動，支援文字紀錄。
    """
    logger.info(f"[API POST /api/chat] 接收到請求. msg='{req.message}', session='{req.session_id}'")
    if not req.message or not req.message.strip():
        logger.warning("[API POST /api/chat] 傳入的訊息內容為空")
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    try:
        # 獲取或創建 Session (demo_user)
        session = await session_service.get_session(user_id="demo_user", session_id=req.session_id, app_name="app")
        if not session:
            session = await session_service.create_session(user_id="demo_user", session_id=req.session_id, app_name="app")
            logger.info(f"[API POST /api/chat] 新增 Session ID: {session.id}")

        # 使用 ADK Runner 進行 Agent 驅動
        runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
        user_message = types.Content(role="user", parts=[types.Part.from_text(text=req.message)])
        
        events = []
        async for event in runner.run_async(new_message=user_message, user_id="demo_user", session_id=session.id):
            events.append(event)

        # 彙整 Agent 的所有回覆片段
        response_parts = []
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_parts.append(part.text)

        response_text = "".join(response_parts)
        logger.info(f"[API POST /api/chat] 回傳成功. 回覆字數={len(response_text)}")
        return {
            "status": "success",
            "response": response_text
        }
    except Exception as e:
        logger.error(f"[API POST /api/chat] Agent 運作時異常: {e}")
        raise HTTPException(status_code=500, detail=f"Agent runtime error: {e}")

@app.post("/api/meals/today")
async def create_meal_today(
    meal_type: str = Form(...),
    restaurant_name: str = Form(None),
    manual_item_name: str = Form(None),
    manual_weight_g: float = Form(None),
    manual_calories_kcal: float = Form(None),
    image_file: UploadFile = File(...)
):
    # Log: 接收到 Request
    logger.info(
        f"[API POST /api/meals/today] 接收到請求. meal_type='{meal_type}', "
        f"restaurant='{restaurant_name}', manual_item='{manual_item_name}', filename='{image_file.filename}'"
    )
    
    # 檔案名稱與防路徑穿越過濾
    if not image_file.filename:
        logger.warning("[API POST /api/meals/today] 上傳的檔案名稱為空，拋出錯誤")
        raise HTTPException(status_code=400, detail="Missing image file.")
        
    safe_filename = os.path.basename(image_file.filename)
    
    # 防禦安全檢查：限制副檔名
    ext = safe_filename.split(".")[-1].lower() if "." in safe_filename else ""
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"[API POST /api/meals/today] 不符合的副檔名上傳: '{ext}'")
        raise HTTPException(status_code=400, detail="Invalid file format. Only JPG, JPEG, PNG, WEBP are allowed.")
        
    # 防禦安全檢查：限制 MIME 類型
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
    if image_file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"[API POST /api/meals/today] 不符合的 Content-Type 上傳: '{image_file.content_type}'")
        raise HTTPException(status_code=400, detail="Invalid MIME type. Only JPG, PNG, WEBP images are allowed.")

    # 寫入本地 uploads 目錄下，使用 UUID 檔名防碰撞且安全
    saved_filename = f"{uuid.uuid4().hex}.{ext}"
    local_image_path = os.path.join(UPLOAD_DIR, saved_filename)
    
    try:
        with open(local_image_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        logger.debug(f"[API POST /api/meals/today] 圖片已成功儲存至本地: '{local_image_path}'")
    except Exception as e:
        logger.error(f"[API POST /api/meals/today] 圖片儲存失敗: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded image.")
        
    # 呼叫 Agent 核心邏輯進行分析與儲存
    try:
        meal_log = log_meal(
            image_path=local_image_path,
            meal_type=meal_type,
            restaurant_name=restaurant_name,
            manual_item_name=manual_item_name,
            manual_weight_g=manual_weight_g,
            manual_calories_kcal=manual_calories_kcal
        )
    except ValueError as val_err:
        # 日期限制錯誤
        logger.error(f"[API POST /api/meals/today] 寫入失敗 (日期限制): {val_err}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        logger.error(f"[API POST /api/meals/today] 呼叫 Agent 工具失敗: {err}")
        raise HTTPException(status_code=500, detail=f"Agent internal processing failed: {err}")
        
    # 整理回傳結果
    response_data = {
        "status": "success",
        "meal_log_id": meal_log["id"],
        "summary": meal_log["total"],
        "sources": [src["type"] for src in meal_log["readonly_sources"]],
        "message": f"成功新增一筆今日的 {meal_type} 紀錄"
    }
    
    # Log: 寄送 Response
    logger.info(f"[API POST /api/meals/today] 回傳成功. log_id='{meal_log['id']}', 總熱量={meal_log['total']['calories_kcal']} kcal")
    return response_data

@app.get("/api/summary/today")
async def get_summary_today():
    # Log: 接收到 Request
    logger.info("[API GET /api/summary/today] 接收到今日摘要查詢請求")
    
    result = get_today_summary("demo_user")
    
    response_data = {
        "date": result["date"],
        "total": result["total"],
        "meals": result["meals"],
        "readonly_sources": [
            {"type": "user_input", "label": "使用者輸入"},
            {"type": "image_analysis", "label": "照片辨識"},
            {"type": "nutrition_database", "label": "台灣食品營養資料庫"}
        ],
        "advice_level": "general"
    }
    
    # Log: 寄送 Response
    logger.info(f"[API GET /api/summary/today] 回傳成功. 總熱量={result['total']['calories_kcal']} kcal, 餐點筆數={len(result['meals'])}")
    return response_data

@app.get("/api/summary/week")
async def get_summary_week():
    # Log: 接收到 Request
    logger.info("[API GET /api/summary/week] 接收到本週摘要查詢請求")
    
    result = get_weekly_summary("demo_user")
    
    # Log: 寄送 Response
    logger.info(f"[API GET /api/summary/week] 回傳成功. 週平均熱量={result['weekly_average']['calories_kcal']} kcal")
    return result

from app.app_utils.typing import Feedback

@app.post("/feedback")
async def collect_feedback(feedback: Feedback):
    logger.info(f"[API POST /feedback] 接收到回饋資訊: {feedback.model_dump()}")
    return {"status": "success", "message": "Feedback logged successfully."}

# 掛載 static 靜態網頁目錄以提供前端網頁 (掛載在 '/' 位址)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
