# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth
from google.auth.exceptions import DefaultCredentialsError
from dotenv import load_dotenv

# 優先載入本地環境變數 (.env)
load_dotenv()

project_id = os.environ.get("GCP_PROJECT_ID", "mock-project-id")
try:
    _, google_project = google.auth.default()
    if google_project:
        project_id = google_project
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ.get("GCP_LOCATION", "global")
except DefaultCredentialsError:
    # 拋出憑證錯誤時，若有 GEMINI_API_KEY 則回退至 Gemini AI Studio 模式
    if os.environ.get("GEMINI_API_KEY"):
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    else:
        # 測試或匯入時先保持 False，避免在載入模組時崩潰
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"



# ==============================================================================
# 飲食紀錄 Agent 核心工具與定義
# ==============================================================================
from app.utils.logger import logger
from app.tools.image_analyzer import analyze_food_image
from app.database.nutrition_db import estimate_nutrition
from app.database.db_manager import save_meal_log, get_today_summary, get_weekly_summary, get_today_date_str

# 固定免責聲明
DISCLAIMER = "此結果為一般飲食紀錄與營養估算，不取代醫師或營養師建議。"

def log_meal(
    image_path: str,
    meal_type: str,
    restaurant_name: str = None,
    manual_item_name: str = None,
    manual_weight_g: float = None,
    manual_calories_kcal: float = None
) -> dict:
    """
    Log a meal for today by analyzing an image, estimating its nutrition, and saving the log.
    
    Args:
        image_path: Absolute or relative path to the meal image file.
        meal_type: Type of the meal (breakfast, lunch, dinner, or snack).
        restaurant_name: Optional name of the restaurant.
        manual_item_name: Optional food item name provided manually by user (e.g. "白飯").
        manual_weight_g: Optional weight in grams for the manual item.
        manual_calories_kcal: Optional total calories if user already knows the meal's calories.
        
    Returns:
        A dictionary containing the saved meal log details.
    """
    logger.info(
        f"[AgentTool: log_meal] 接收到新增紀錄請求: path='{image_path}', meal_type='{meal_type}', "
        f"restaurant='{restaurant_name}', manual_item='{manual_item_name}', manual_weight={manual_weight_g}g"
    )
    
    # 1. 圖片分析辨識
    detected_items_raw = analyze_food_image(image_path)
    
    # 2. 整合手動輸入
    detected_items = []
    # 若有手動輸入已知卡路里，我們會記錄但不影響偵測項目
    manual_inputs = {
        "items": [],
        "calories_kcal": manual_calories_kcal
    }
    
    if manual_item_name and manual_weight_g:
        manual_inputs["items"].append({
            "name": manual_item_name,
            "weight_g": manual_weight_g
        })
        
    # 3. 營養庫查詢與加總
    total_calories = 0.0
    total_protein = 0.0
    total_fat = 0.0
    total_carbs = 0.0
    
    # 若使用者有手動輸入已知總卡路里且無明細，則以手動卡路里優先
    if manual_calories_kcal is not None and not detected_items_raw and not manual_item_name:
        total_calories = manual_calories_kcal
        logger.info(f"[AgentTool: log_meal] 使用手動卡路里: {manual_calories_kcal} kcal")
    else:
        # A. 處理圖片辨識到的項目
        for item in detected_items_raw:
            name = item["name"]
            weight = item["estimated_weight_g"]
            
            # 若手動輸入的名字與辨識到的一致，以手動輸入的重量優先
            if manual_item_name == name and manual_weight_g is not None:
                weight = manual_weight_g
                logger.info(f"[AgentTool: log_meal] 食物 '{name}' 採用手動重量: {weight}g")
                
            est = estimate_nutrition(name, weight)
            detected_items.append(est)
            
            total_calories += est["calories_kcal"]
            total_protein += est["protein_g"]
            total_fat += est["fat_g"]
            total_carbs += est["carbs_g"]
            
        # B. 處理手動輸入但未在圖片中辨識到的項目
        if manual_item_name and not any(item["name"] == manual_item_name for item in detected_items_raw):
            est = estimate_nutrition(manual_item_name, manual_weight_g)
            # 信心度標為 1.0 (因是使用者手動確認輸入)
            est["confidence"] = 1.0
            est["nutrition_source"]["source_type"] = "user_input"
            
            detected_items.append(est)
            total_calories += est["calories_kcal"]
            total_protein += est["protein_g"]
            total_fat += est["fat_g"]
            total_carbs += est["carbs_g"]

    # 整合來源資訊
    readonly_sources = [
        {"type": "user_input", "label": "使用者輸入", "value": f"{manual_item_name or '無'} {f'{manual_weight_g}g' if manual_weight_g else ''}"},
        {"type": "image_analysis", "label": "照片辨識", "value": "、".join([item["name"] for item in detected_items_raw]) or "無"},
        {"type": "nutrition_database", "label": "營養資料來源", "value": "Taiwan Food Nutrition Database & Mock"}
    ]
    
    meal_log = {
        "date": get_today_date_str(),
        "meal_type": meal_type,
        "restaurant_name": restaurant_name,
        "image_uri": image_path,
        "manual_inputs": manual_inputs,
        "detected_items": detected_items,
        "total": {
            "calories_kcal": round(total_calories, 2),
            "protein_g": round(total_protein, 2),
            "fat_g": round(total_fat, 2),
            "carbs_g": round(total_carbs, 2)
        },
        "readonly_sources": readonly_sources,
        "agent_audit": {
            "agent_name": "DietLoggerAgent",
            "used_tools": ["analyze_food_image", "estimate_nutrition", "save_meal_log"],
            "warnings": ["熱量為估算值，實際數值可能因份量、醬料與烹調方式不同而變動。"]
        },
        "version": "p0"
    }
    
    # 4. 寫入資料庫
    log_id = save_meal_log("demo_user", meal_log)
    meal_log["id"] = log_id
    
    logger.info(f"[AgentTool: log_meal] 新增紀錄完成，ID: {log_id}，總熱量: {meal_log['total']['calories_kcal']} kcal")
    return meal_log

def query_today_summary() -> dict:
    """
    Query today's total nutrition and meal list.
    """
    logger.info("[AgentTool: query_today_summary] 執行今日摘要查詢")
    result = get_today_summary("demo_user")
    return result

def query_weekly_summary() -> dict:
    """
    Query weekly nutrition overview.
    """
    logger.info("[AgentTool: query_weekly_summary] 執行本週摘要查詢")
    result = get_weekly_summary("demo_user")
    return result


# ==============================================================================
# DietLoggerAgent 宣告
# ==============================================================================
root_agent = Agent(
    name="DietLoggerAgent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=f"""你是一個親切的飲食紀錄助理 DietLoggerAgent。
你的職責是協助使用者記錄今日飲食，或是查詢今日/本週的飲食統計摘要。

請遵守以下規則：
1. 識別使用者意圖：
   - 當使用者想要「記錄餐點」或上傳食物照片時，請呼叫 `log_meal` 工具，傳入合適的參數（例如餐別：breakfast, lunch, dinner, 或 snack，若無指定則依據當前時間猜測，或呼叫工具後再補充說明）。
   - 當使用者詢問「今天吃了什麼」、「今天熱量多少」等，呼叫 `query_today_summary` 工具。
   - 當使用者詢問「本週吃得如何」、「本週熱量統計」等，呼叫 `query_weekly_summary` 工具。

2. 格式化回覆：
   - 每次回覆統計或新增紀錄結果時，請條列出食物明細、熱量與三大營養素（蛋白質、脂肪、碳水化合物）。
   - 請列出資料來源 (如：Taiwan Food Nutrition Database)。
   - **必須在每次回覆的最後附上這句免責聲明**：'{DISCLAIMER}'。
   - 保持語氣親切，且絕不做個人化減重或達標建議，僅陳述目前紀錄的數值。
""",
    tools=[log_meal, query_today_summary, query_weekly_summary],
)

app = App(
    root_agent=root_agent,
    name="app",
)
