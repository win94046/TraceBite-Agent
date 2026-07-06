import pytest
import os
import io
from fastapi.testclient import TestClient
from app.fast_api_app import app
from app.database.db_manager import mock_db

# 啟用 Mock 模式 (只在環境變數未手動設定時，才預設為 true)
if "USE_MOCK_FIRESTORE" not in os.environ:
    os.environ["USE_MOCK_FIRESTORE"] = "true"
client = TestClient(app)

@pytest.fixture(autouse=True)
def init_db():
    mock_db.clear()
    yield
    mock_db.clear()

def get_real_image_io() -> io.BytesIO:
    image_path = os.path.join(os.path.dirname(__file__), "mock_food.jpg")
    with open(image_path, "rb") as f:
        return io.BytesIO(f.read())

def test_full_user_flow_e2e():
    """
    E2E 整合測試：模擬使用者整天的餐點上傳、資料庫累加與查詢今日/本週統計之完整工作流
    """
    # 判斷是否為真實 AI 模式
    api_key = os.environ.get("GEMINI_API_KEY")
    is_real_mode = api_key and api_key != "your_gemini_api_key_here" and len(api_key.strip()) > 10

    # ==========================================================================
    # 步驟 1: 新增今日早餐 (照片檔名含 chicken)
    # ==========================================================================
    breakfast_image = get_real_image_io()
    response_bf = client.post(
        "/api/meals/today",
        data={
            "meal_type": "breakfast",
            "restaurant_name": "A餐館"
        },
        files={
            "image_file": ("chicken_leg.jpg", breakfast_image, "image/jpeg")
        }
    )
    
    assert response_bf.status_code == 200
    res_bf = response_bf.json()
    assert res_bf["status"] == "success"
    
    if is_real_mode:
        assert res_bf["summary"]["calories_kcal"] > 0
    else:
        # 雞腿 180g (396kcal) + 白飯 150g (195kcal) + 青菜 80g (20kcal) = 611 kcal
        assert res_bf["summary"]["calories_kcal"] == 611.0
    
    # ==========================================================================
    # 步驟 2: 新增今日午餐 (無關鍵字檔名，但手動指定白飯重量為 200g)
    # ==========================================================================
    lunch_image = get_real_image_io()
    response_lu = client.post(
        "/api/meals/today",
        data={
            "meal_type": "lunch",
            "restaurant_name": "池上便當",
            "manual_item_name": "白飯",
            "manual_weight_g": 200.0 # 手動覆寫白飯重量為 200g
        },
        files={
            "image_file": ("unknown.jpg", lunch_image, "image/jpeg")
        }
    )
    
    assert response_lu.status_code == 200
    res_lu = response_lu.json()
    
    if is_real_mode:
        assert res_lu["summary"]["calories_kcal"] > 0
    else:
        # 預設辨識：白飯 150g 與 青菜 100g (25kcal)
        # 手動覆寫白飯為 200g (260kcal) -> 總卡路里 = 260 + 25 = 285 kcal
        assert res_lu["summary"]["calories_kcal"] == 285.0
    
    # ==========================================================================
    # 步驟 3: 查詢今日飲食摘要
    # ==========================================================================
    response_today = client.get("/api/summary/today")
    assert response_today.status_code == 200
    res_today = response_today.json()
    
    if is_real_mode:
        assert res_today["total"]["calories_kcal"] > 0
        assert res_today["total"]["protein_g"] > 0
    else:
        # 驗證總熱量累加： 611 + 285 = 896 kcal
        assert res_today["total"]["calories_kcal"] == 896.0
        assert res_today["total"]["protein_g"] == 43.5
        
    # 驗證有 2 餐明細
    assert len(res_today["meals"]) == 2
    
    # ==========================================================================
    # 步驟 4: 查詢本週飲食統計
    # ==========================================================================
    response_week = client.get("/api/summary/week")
    assert response_week.status_code == 200
    res_week = response_week.json()
    
    if is_real_mode:
        assert res_week["weekly_average"]["calories_kcal"] > 0
    else:
        # 週日均熱量應為今日總和的 1/7 = 896 / 7 = 128 kcal
        assert res_week["weekly_average"]["calories_kcal"] == round(896.0 / 7.0, 2)
        
    # 驗證日趨勢列表包含 7 天
    assert len(res_week["daily_totals"]) == 7
