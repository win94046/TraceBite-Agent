import pytest
import os
import io
from fastapi.testclient import TestClient
from app.fast_api_app import app
from app.database.db_manager import mock_db

# 啟用 Mock 模式
os.environ["USE_MOCK_FIRESTORE"] = "true"

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    mock_db.clear()
    yield
    mock_db.clear()

def test_create_meal_today_api():
    # 建立 Dummy 圖片檔案內容
    dummy_image = io.BytesIO(b"dummy image data")
    
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
            "image_file": ("test_meal.jpg", dummy_image, "image/jpeg")
        }
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "meal_log_id" in res_data
    # 預設辨識到的應該是白飯 (因檔名不含 chicken/pork/egg 等，會走預設白飯與青菜組合)
    # 食物白飯採用了手動重量 150g -> 195 kcal
    # 食物青菜採用預估重量 100g -> 25 kcal
    # 總熱量 = 195 + 25 = 220 kcal
    assert res_data["summary"]["calories_kcal"] == 220.0
    assert "image_analysis" in res_data["sources"]
    
    # 驗證日誌檔案是否被寫入且存在
    log_path = "/Users/yukai.chen/Desktop/TraceBite-Agent/tracebite_agent.log"
    assert os.path.exists(log_path)
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
        # 確認包含 API 接收 log
        assert "[API POST /api/meals/today] 接收到請求" in log_content
        assert "回傳成功" in log_content

def test_get_summary_today_api():
    # 先利用 TestClient 寫入一餐
    dummy_image = io.BytesIO(b"dummy image data")
    client.post(
        "/api/meals/today",
        data={"meal_type": "breakfast"},
        files={"image_file": ("breakfast.jpg", dummy_image, "image/jpeg")}
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
    # 先寫入一餐
    dummy_image = io.BytesIO(b"dummy image data")
    client.post(
        "/api/meals/today",
        data={"meal_type": "dinner"},
        files={"image_file": ("dinner.jpg", dummy_image, "image/jpeg")}
    )
    
    # 查詢本週統計
    response = client.get("/api/summary/week")
    assert response.status_code == 200
    res_data = response.json()
    assert "week_start" in res_data
    assert "week_end" in res_data
    assert len(res_data["daily_totals"]) == 7
    assert res_data["weekly_average"]["calories_kcal"] > 0
