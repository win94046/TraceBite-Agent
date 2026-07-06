import pytest
import datetime
import os
from app.database.db_manager import save_meal_log, get_today_summary, get_weekly_summary, mock_db, get_today_date_str

# 在測試執行前，設定啟用 USE_MOCK_FIRESTORE 確保不連線雲端
os.environ["USE_MOCK_FIRESTORE"] = "true"

@pytest.fixture(autouse=True)
def run_around_tests():
    # 測試前清空 InMemory Mock
    mock_db.clear()
    yield
    # 測試後再次清空
    mock_db.clear()

def test_save_meal_log_success():
    user_id = "test_user"
    today_str = get_today_date_str()
    
    # 準備飲食資料
    meal_data = {
        "date": today_str,
        "meal_type": "lunch",
        "total": {
            "calories_kcal": 550.0,
            "protein_g": 25.0,
            "fat_g": 18.0,
            "carbs_g": 70.0
        }
    }
    
    # 儲存
    log_id = save_meal_log(user_id, meal_data)
    assert log_id.startswith("meal_")
    
    # 驗證是否寫入 mock 記憶體中
    assert log_id in mock_db.meal_logs[user_id]
    
    # 驗證 daily_summaries 有無自動累加
    yyyyMMdd = today_str.replace("-", "")
    summary = mock_db.daily_summaries[user_id][yyyyMMdd]
    assert summary["date"] == today_str
    assert summary["total"]["calories_kcal"] == 550.0

def test_save_meal_log_date_restriction():
    user_id = "test_user"
    
    # 準備非今日之日期 (昨天)
    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    meal_data = {
        "date": yesterday_str,
        "meal_type": "dinner",
        "total": {
            "calories_kcal": 400.0,
            "protein_g": 20.0,
            "fat_g": 15.0,
            "carbs_g": 50.0
        }
    }
    
    # 驗證會拋出 ValueError 並包含錯誤訊息
    with pytest.raises(ValueError) as excinfo:
        save_meal_log(user_id, meal_data)
    assert "P0 only supports today's meal logging." in str(excinfo.value)

def test_get_today_summary():
    user_id = "test_user"
    today_str = get_today_date_str()
    
    # 寫入兩餐
    meal_1 = {
        "date": today_str,
        "meal_type": "breakfast",
        "total": {"calories_kcal": 300.0, "protein_g": 10.0, "fat_g": 8.0, "carbs_g": 40.0}
    }
    meal_2 = {
        "date": today_str,
        "meal_type": "lunch",
        "total": {"calories_kcal": 600.0, "protein_g": 30.0, "fat_g": 20.0, "carbs_g": 80.0}
    }
    
    save_meal_log(user_id, meal_1)
    save_meal_log(user_id, meal_2)
    
    # 查詢今日摘要
    summary = get_today_summary(user_id)
    assert summary["date"] == today_str
    assert len(summary["meals"]) == 2
    assert summary["total"]["calories_kcal"] == 900.0
    assert summary["total"]["protein_g"] == 40.0

def test_get_weekly_summary():
    user_id = "test_user"
    today_str = get_today_date_str()
    
    # 寫入今日飲食
    meal = {
        "date": today_str,
        "meal_type": "lunch",
        "total": {"calories_kcal": 700.0, "protein_g": 35.0, "fat_g": 21.0, "carbs_g": 91.0}
    }
    save_meal_log(user_id, meal)
    
    # 查詢本週統計
    weekly = get_weekly_summary(user_id)
    
    # 本週包含今日的前7天
    assert len(weekly["daily_totals"]) == 7
    # 今天的數據需符合 700 kcal
    today_entry = [entry for entry in weekly["daily_totals"] if entry["date"] == today_str][0]
    assert today_entry["calories_kcal"] == 700.0
    
    # 週平均應為今日的 1/7
    assert weekly["weekly_average"]["calories_kcal"] == round(700.0 / 7.0, 2)
