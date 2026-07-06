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
from google.adk.tools.tool_context import ToolContext

# 固定免責聲明
DISCLAIMER = "此結果為一般飲食紀錄與營養估算，不取代醫師或營養師建議。"

def log_meal(
    image_path: str,
    meal_type: str,
    tool_context: ToolContext = None,
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
        tool_context: ADK ToolContext for accessing session state and events.
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
    
    # 針對對話模式 (Chat UI) 下的虛擬檔名或不存在的圖片檔案做處理
    if image_path and (not os.path.exists(image_path) or "input_file_" in image_path):
        if tool_context:
            logger.info(f"[AgentTool: log_meal] 圖片路徑 '{image_path}' 不存在，嘗試從對話歷史中提取圖片 bytes...")
            image_bytes = None
            mime_type = "image/jpeg"
            
            # 由後往前搜尋 user 訊息中的圖片
            for event in reversed(tool_context.session.events):
                if event.author == "user" and event.content and event.content.parts:
                    for part in event.content.parts:
                        inline_data = getattr(part, "inline_data", None)
                        if inline_data:
                            data = getattr(inline_data, "data", None)
                            m_type = getattr(inline_data, "mime_type", None)
                            if data and m_type and m_type.startswith("image/"):
                                image_bytes = data
                                mime_type = m_type
                                break
                    if image_bytes:
                        break
            
            if image_bytes:
                import uuid
                ext = mime_type.split("/")[-1]
                if ext == "jpeg":
                    ext = "jpg"
                saved_filename = f"chat_upload_{uuid.uuid4().hex[:8]}.{ext}"
                saved_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads", saved_filename)
                os.makedirs(os.path.dirname(saved_path), exist_ok=True)
                with open(saved_path, "wb") as f:
                    f.write(image_bytes)
                logger.info(f"[AgentTool: log_meal] 成功將對話中的圖片還原並儲存至: '{saved_path}'")
                image_path = saved_path
            else:
                logger.warning("[AgentTool: log_meal] 無法從對話歷史中找到任何圖片 bytes。")
        else:
            logger.warning(f"[AgentTool: log_meal] 圖片路徑 '{image_path}' 不存在，但無 ToolContext 可用。")
    
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
            "weight_g": round(sum(item["estimated_weight_g"] for item in detected_items), 2),
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

def log_meal_by_text(
    food_item_name: str,
    meal_type: str,
    weight_g: float = 100.0,
    calories_kcal: float = None,
    restaurant_name: str = None
) -> dict:
    """
    Log a meal for today using text input (when no image is uploaded).
    
    Args:
        food_item_name: Name of the food item (e.g. "排骨便當", "白飯").
        meal_type: Type of the meal (breakfast, lunch, dinner, or snack).
        weight_g: Estimated weight in grams.
        calories_kcal: Optional total calories if user already knows the meal's calories.
        restaurant_name: Optional name of the restaurant.
        
    Returns:
        A dictionary containing the saved meal log details.
    """
    logger.info(
        f"[AgentTool: log_meal_by_text] 接收到文字記錄請求: item='{food_item_name}', weight={weight_g}g, "
        f"meal_type='{meal_type}', calories={calories_kcal} kcal"
    )
    
    total_calories = 0.0
    total_protein = 0.0
    total_fat = 0.0
    total_carbs = 0.0
    
    detected_items = []
    
    if calories_kcal is not None and food_item_name == "未知":
        total_calories = calories_kcal
    else:
        # 使用在地估算表
        est = estimate_nutrition(food_item_name, weight_g)
        # 文字輸入視為使用者確認，設定較高信心度
        est["confidence"] = 0.95
        detected_items.append(est)
        
        total_calories = est["calories_kcal"]
        total_protein = est["protein_g"]
        total_fat = est["fat_g"]
        total_carbs = est["carbs_g"]
        
    readonly_sources = [
        {"type": "user_input", "label": "文字輸入", "value": f"{food_item_name} {weight_g}g"},
        {"type": "nutrition_database", "label": "營養資料來源", "value": "Taiwan Food Nutrition Database"}
    ]
    
    meal_log = {
        "date": get_today_date_str(),
        "meal_type": meal_type,
        "restaurant_name": restaurant_name,
        "image_uri": "", # 文字記錄不含圖片
        "manual_inputs": {
            "items": [{"name": food_item_name, "weight_g": weight_g}],
            "calories_kcal": calories_kcal
        },
        "detected_items": detected_items,
        "total": {
            "weight_g": round(sum(item["estimated_weight_g"] for item in detected_items), 2),
            "calories_kcal": round(total_calories, 2),
            "protein_g": round(total_protein, 2),
            "fat_g": round(total_fat, 2),
            "carbs_g": round(total_carbs, 2)
        },
        "readonly_sources": readonly_sources,
        "agent_audit": {
            "agent_name": "DietLoggerAgent",
            "used_tools": ["estimate_nutrition", "save_meal_log"],
            "warnings": ["熱量為估算值，實際數值可能因份量、醬料與烹調方式不同而變動。"]
        },
        "version": "p0"
    }
    
    # 4. 寫入資料庫
    log_id = save_meal_log("demo_user", meal_log)
    meal_log["id"] = log_id
    
    logger.info(f"[AgentTool: log_meal_by_text] 新增文字紀錄完成，ID: {log_id}，總熱量: {meal_log['total']['calories_kcal']} kcal")
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
   - 當使用者提供「食物照片」或指定「照片檔案路徑」要記錄餐點時，請呼叫 `log_meal` 工具。
   - 當使用者以「純文字對話」要求記錄他吃了什麼（沒有提供圖片/路徑）時，請呼叫 `log_meal_by_text` 工具，傳入合適的參數（食物名稱、餐別、重量等）。若使用者一次描述了多個不同的食物項目，請針對每個項目個別呼叫 `log_meal_by_text` 工具，切勿合併成一個大項目呼叫。若無指定餐別，依據當前時間猜測，或呼叫工具後再說明。
   - 當使用者詢問「今天吃了什麼」、「今天熱量多少」等，呼叫 `query_today_summary` 工具。
   - 當使用者詢問「本週吃得如何」、「本週熱量統計」等，呼叫 `query_weekly_summary` 工具。

2. 格式化回覆：
   - 每次回覆統計或新增餐點紀錄結果時，請嚴格使用以下格式與 Markdown 表格（Markdown Table）語法進行輸出。請確保使用 `|` 符號與 `-` 符號構成表頭分隔線，且食物明細欄位為左對齊（`:---`），其餘數值欄位為置中對齊（`:---:`），以利於 Chat UI 自動渲染並適應屏幕寬度：
     
     您好！我已經為您將這豐富的[餐別]紀錄下來了。[對餐點的簡短特色描述，例：這份餐點包含兩種風格截然不同的菜色呢！]

     以下是您本次[餐別]的飲食紀錄與營養估算：

     | 食物明細 | 估算重量 (g) | 熱量 (大卡) | 蛋白質 (g) | 脂肪 (g) | 碳水化合物 (g) |
     | :--- | :---: | :---: | :---: | :---: | :---: |
     | [食物名稱1] (英文名稱1) | [重量1] | [熱量1] | [蛋白質1] | [脂肪1] | [碳水化合物1] |
     | [食物名稱2] (英文名稱2) | [重量2] | [熱量2] | [蛋白質2] | [脂肪2] | [碳水化合物2] |
     ...
     | **總計** | **[總重量]** | **[總熱量]** | **[總蛋白質]** | **[總脂肪]** | **[總碳水化合物]** |

     營養總結：

     總熱量： [總熱量] 大卡
     蛋白質： [總蛋白質] g
     脂肪： [總脂肪] g
     碳水化合物： [總碳水化合物] g
     資料來源：Taiwan Food Nutrition Database & Mock (通用估算)

     {DISCLAIMER}

   - 規範要求：
     - [餐別] 請依據該餐點實際類型代入（如：早餐、午餐、晚餐、點心/宵夜）。
     - [對餐點的簡短特色描述] 必須放在問候語句尾，為餐點作一句親切且契合菜色的簡短評語。
     - 表格中的「食物明細」必須呈現為「中文名稱 (英文名稱)」，如果工具只回傳中文，請自行將其翻譯成對應的英文並放於括號內。
     - 表格最後一行必須是 `**總計**`，且該行內的所有加總數值均要以粗體（`**[數值]**`）呈現。
     - 「總計」行與「營養總結」中各項營養數值（包括重量、熱量、蛋白質、脂肪、碳水化合物）請直接參考工具回傳的 `total` 字典中的對應數值（如 `weight_g`, `calories_kcal`, `protein_g`, `fat_g`, `carbs_g`），嚴禁自行心算錯誤，必須完全與 `total` 中的數據一致。
     - 結尾固定附上「資料來源：Taiwan Food Nutrition Database & Mock (通用估算)」及「{DISCLAIMER}」。
   - 保持語氣親切，且絕不做個人化減重或達標建議，僅陳述目前紀錄的數值。
""",
    tools=[log_meal, log_meal_by_text, query_today_summary, query_weekly_summary],
)

app = App(
    root_agent=root_agent,
    name="app",
)
