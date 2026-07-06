import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.utils.logger import logger

# 導入我們的資料庫與 Agent 函數
from app.database.db_manager import get_today_summary, get_weekly_summary, get_today_date_str
from app.agent import log_meal

app = FastAPI(
    title="TraceBite Agent P0 API",
    description="飲食紀錄 Agent 系統 MVP API"
)

# CORS 中間件設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 確保照片暫存的 uploads 目錄存在
UPLOAD_DIR = "/Users/yukai.chen/Desktop/TraceBite-Agent/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    
    # 驗證檔案名稱
    if not image_file.filename:
        logger.warning("[API POST /api/meals/today] 上傳的檔案名稱為空，拋出錯誤")
        raise HTTPException(status_code=400, detail="Missing image file.")
        
    # 將圖片寫入本地 uploads 目錄下，保留原始檔名以防碰撞且支援模擬辨識
    saved_filename = f"{uuid.uuid4().hex}_{image_file.filename}"
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
        "message": f"已完成今日{meal_type}紀錄。"
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
            {"type": "nutrition_database", "label": "台灣食品營養庫"}
        ],
        "advice_level": "general"
    }
    
    # Log: 寄送 Response
    logger.info(f"[API GET /api/summary/today] 回傳成功. 總熱量={result['total']['calories_kcal']} kcal, 餐數={len(result['meals'])}")
    return response_data

@app.get("/api/summary/week")
async def get_summary_week():
    # Log: 接收到 Request
    logger.info("[API GET /api/summary/week] 接收到本週摘要查詢請求")
    
    result = get_weekly_summary("demo_user")
    
    # Log: 寄送 Response
    logger.info(f"[API GET /api/summary/week] 回傳成功. 週平均熱量={result['weekly_average']['calories_kcal']} kcal")
    return result

# 掛載 static 靜態網頁目錄以提供前端網頁 (掛載在 '/' 位址)
STATIC_DIR = "/Users/yukai.chen/Desktop/TraceBite-Agent/static"
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
