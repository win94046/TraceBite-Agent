import os
import json
from google import genai
from google.genai import types
from app.utils.logger import logger

def analyze_food_image(image_path: str) -> list[dict]:
    """
    分析食物圖片。
    當偵測到環境變數中有設定真實的 GEMINI_API_KEY 時，會啟用真實的 Gemini 2.5 進行多模態圖像分析；
    否則會自動降級 (Fallback) 為本地的檔名關鍵字 Mock 模擬辨識。
    """
    logger.info(f"[ImageAnalyzer] 開始分析食物圖片，路徑: '{image_path}'")
    
    if not image_path:
        logger.warning("[ImageAnalyzer] 傳入的圖片路徑為空")
        return []

    use_mock = os.environ.get("USE_MOCK_FIRESTORE", "true").lower() == "true"
    if not os.path.exists(image_path):
        if not use_mock:
            logger.error(f"[ImageAnalyzer] 圖片路徑不存在: '{image_path}'，在真實模式下拋出錯誤。")
            raise RuntimeError(f"圖片路徑不存在且禁止降級: {image_path}")
        logger.warning(f"[ImageAnalyzer] 圖片路徑不存在: '{image_path}'，自動安全降級 (Fallback) 至 Mock 模式。")
        return _mock_analyze_food_image(image_path)

    # 檢查是否具備有效的 API 金鑰 (排除範本占位符)
    api_key = os.environ.get("GEMINI_API_KEY")
    is_real_mode = api_key and api_key != "your_gemini_api_key_here" and len(api_key.strip()) > 10
    use_mock = os.environ.get("USE_MOCK_FIRESTORE", "true").lower() == "true"

    if not use_mock and not is_real_mode:
        logger.error("[ImageAnalyzer] 啟用真實環境模式但未檢測到有效的 GEMINI_API_KEY，拋出錯誤！")
        raise RuntimeError("USE_MOCK_FIRESTORE 為 false，但未設定有效的 GEMINI_API_KEY！")

    if is_real_mode:
        logger.info("[ImageAnalyzer] 檢測到真實 API Key，啟用 Gemini 視覺模型分析...")
        try:
            # 建立 genai 客戶端 (SDK 會自動讀取 GEMINI_API_KEY)
            client = genai.Client()
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            prompt = """
            請分析這張照片中的食物。
            請列出食物項目名稱，並估算它的重量（單位：公克）。
            請務必以 JSON 陣列格式回傳，且陣列內的物件必須包含 'name' (食物名稱)、'estimated_weight_g' (估算重量) 與 'confidence' (信心度) 欄位。
            例如：
            [
              {"name": "雞腿", "estimated_weight_g": 180.0, "confidence": 0.92},
              {"name": "白飯", "estimated_weight_g": 150.0, "confidence": 0.88}
            ]
            """

            # 呼叫 Gemini 2.5 Flash 模型
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json" # 指定回傳格式為 JSON
                )
            )
            
            # 解析並驗證回傳結果
            detected_items = json.loads(response.text)
            logger.info(f"[ImageAnalyzer] Real AI 辨識完成。項目數: {len(detected_items)}，明細: {[item['name'] for item in detected_items]}")
            return detected_items

        except Exception as e:
            if not use_mock:
                logger.error(f"[ImageAnalyzer] 在真實環境下，Gemini API 呼叫發生不可忽視的錯誤: {e}")
                raise RuntimeError(f"真實 AI 辨識發生錯誤且禁止降級: {e}")
            else:
                logger.error(f"[ImageAnalyzer] 真實 AI 辨識發生錯誤: {e}，自動安全降級 (Fallback) 至 Mock 模式。")
                return _mock_analyze_food_image(image_path)
    else:
        logger.info("[ImageAnalyzer] 未檢測到真實 API Key，啟用本地 Mock 檔名辨識...")
        return _mock_analyze_food_image(image_path)


def _mock_analyze_food_image(image_path: str) -> list[dict]:
    """
    模擬食物圖片辨識的本地 Fallback 方法。
    依據檔案名稱內含的關鍵字，辨識出不同的食物項目與預估重量。
    """
    filename = os.path.basename(image_path).lower()
    detected_items = []
    
    if "chicken" in filename or "雞腿" in filename:
        detected_items.append({"name": "雞腿", "estimated_weight_g": 180.0, "confidence": 0.92})
        detected_items.append({"name": "白飯", "estimated_weight_g": 150.0, "confidence": 0.88})
        detected_items.append({"name": "青菜", "estimated_weight_g": 80.0, "confidence": 0.85})
    elif "pork" in filename or "排骨" in filename:
        detected_items.append({"name": "排骨", "estimated_weight_g": 150.0, "confidence": 0.90})
        detected_items.append({"name": "白飯", "estimated_weight_g": 150.0, "confidence": 0.88})
        detected_items.append({"name": "滷蛋", "estimated_weight_g": 50.0, "confidence": 0.95})
    elif "egg" in filename or "蛋" in filename:
        detected_items.append({"name": "滷蛋", "estimated_weight_g": 50.0, "confidence": 0.95})
        detected_items.append({"name": "青菜", "estimated_weight_g": 100.0, "confidence": 0.87})
    else:
        detected_items.append({"name": "白飯", "estimated_weight_g": 150.0, "confidence": 0.80})
        detected_items.append({"name": "青菜", "estimated_weight_g": 100.0, "confidence": 0.75})
        
    logger.info(
        f"[ImageAnalyzer Mock] 圖片分析完成。辨識出的項目筆數: {len(detected_items)}，"
        f"辨識明細: {[item['name'] for item in detected_items]}"
    )
    return detected_items
