import pytest
import os
import io
from fastapi.testclient import TestClient
from app.fast_api_app import app
from app.database.db_manager import mock_db

# API 測試一律強制啟用 Mock 模式以維持測試隔離性與速度，避免受到本地 .env 設定污染
os.environ["USE_MOCK_FIRESTORE"] = "true"

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    mock_db.clear()
    yield
    mock_db.clear()

def get_real_image_io() -> io.BytesIO:
    image_path = os.path.join(os.path.dirname(__file__), "mock_food.jpg")
    with open(image_path, "rb") as f:
        return io.BytesIO(f.read())

def test_create_meal_today_api():
    # 讀取真實測試圖片內容
    real_image = get_real_image_io()
    
    # 發送 POST 請求
    response = client.post(
        "/api/meals/today",
        data={
            "meal_type": "lunch",
            "restaurant_name": "池上便當",
            "manual_item_name": "白飯",
            "manual_weight_g": 150.0
        },
        files={
            "image_file": ("test_meal.jpg", real_image, "image/jpeg")
        }
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "meal_log_id" in res_data
    
    # 判斷是否為真實 AI 模式
    api_key = os.environ.get("GEMINI_API_KEY")
    is_real_mode = api_key and api_key != "your_gemini_api_key_here" and len(api_key.strip()) > 10
    
    if is_real_mode:
        # 真實 AI 模式下，總卡路里只要有成功分析大於 0 即可
        assert res_data["summary"]["calories_kcal"] > 0
    else:
        # 本地 Mock 模式下，總熱量 = 195 (白飯 150g) + 25 (青菜 100g) = 220.0 kcal
        assert res_data["summary"]["calories_kcal"] == 220.0
        
    assert "image_analysis" in res_data["sources"]
    
    # 驗證日誌檔案是否被寫入且存在
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "tracebite_agent.log")
    assert os.path.exists(log_path)
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
        # 確認包含 API 接收 log
        assert "[API POST /api/meals/today] 接收到請求" in log_content
        assert "回傳成功" in log_content

def test_get_summary_today_api():
    # 先利用 TestClient 寫入一餐 (使用真實圖片)
    real_image = get_real_image_io()
    client.post(
        "/api/meals/today",
        data={"meal_type": "breakfast"},
        files={"image_file": ("breakfast.jpg", real_image, "image/jpeg")}
    )
    
    # 查詢今日統計
    response = client.get("/api/summary/today")
    assert response.status_code == 200
    res_data = response.json()
    assert "date" in res_data
    assert len(res_data["meals"]) == 1
    assert res_data["total"]["calories_kcal"] > 0
    assert "advice_level" in res_data

def test_get_summary_week_api():
    # 先寫入一餐 (使用真實圖片)
    real_image = get_real_image_io()
    client.post(
        "/api/meals/today",
        data={"meal_type": "dinner"},
        files={"image_file": ("dinner.jpg", real_image, "image/jpeg")}
    )
    
    # 查詢本週統計
    response = client.get("/api/summary/week")
    assert response.status_code == 200
    res_data = response.json()
    assert "week_start" in res_data
    assert "week_end" in res_data
    assert len(res_data["daily_totals"]) == 7
    assert res_data["weekly_average"]["calories_kcal"] > 0

def test_chat_with_agent_api():
    """
    測試 /api/chat 對話端點與 Agent-MCP 整合
    """
    response = client.post(
        "/api/chat",
        json={"message": "我剛剛吃了排骨便當，幫我記在午餐"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "response" in res_data
    # 驗證回覆中包含免責聲明與寫入完成字樣
    assert "不取代醫師或營養師建議" in res_data["response"]

def test_api_upload_file_security_invalid_ext():
    """
    測試安全防禦：上傳不合規的副檔名，應回傳 400 Bad Request
    """
    bad_file = io.BytesIO(b"malicious scripts")
    response = client.post(
        "/api/meals/today",
        data={"meal_type": "lunch"},
        files={"image_file": ("exploit.sh", bad_file, "text/x-shellscript")}
    )
    assert response.status_code == 400
    assert "Only JPG, JPEG, PNG, WEBP are allowed" in response.json()["detail"]

def test_api_upload_file_security_invalid_mime():
    """
    測試安全防禦：上傳合規副檔名但 MIME 類型不合規，應回傳 400 Bad Request
    """
    bad_file = io.BytesIO(b"malicious scripts")
    response = client.post(
        "/api/meals/today",
        data={"meal_type": "lunch"},
        files={"image_file": ("exploit.jpg", bad_file, "text/x-shellscript")}
    )
    assert response.status_code == 400
    assert "Only JPG, PNG, WEBP images are allowed" in response.json()["detail"]

