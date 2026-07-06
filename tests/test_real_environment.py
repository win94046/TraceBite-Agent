import pytest
import os
from fastapi.testclient import TestClient

from app.fast_api_app import app
from app.tools.image_analyzer import analyze_food_image

client = TestClient(app)

def test_strict_mode_image_analyzer_error(monkeypatch, tmp_path):
    """
    驗證：在強制真實模式下 (USE_MOCK_FIRESTORE=false)，
    若缺乏 GEMINI_API_KEY (或 API 呼叫失敗)，圖片辨識必須直接拋出 RuntimeError，不得降級。
    """
    # 使用 monkeypatch 安全隔離環境變數，防止污染其他測試檔案的執行
    monkeypatch.setenv("USE_MOCK_FIRESTORE", "false")
    
    # 建立一個真實存在的空檔案以防止觸發檔案不存在的錯誤
    test_img = tmp_path / "temp_food.jpg"
    test_img.write_bytes(b"dummy image content")
    
    # 暫時移走環境變數中的 API 金鑰以模擬金鑰失效
    old_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
    try:
        # 執行辨識，預期要直接拋出 RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            analyze_food_image(str(test_img))
        
        # 斷言錯誤訊息中指明了「USE_MOCK_FIRESTORE 為 false，但未設定有效的 GEMINI_API_KEY」
        assert "USE_MOCK_FIRESTORE 為 false" in str(exc_info.value)
        
    finally:
        # 還原環境變數以防污染其他測試
        if old_key:
            os.environ["GEMINI_API_KEY"] = old_key


def test_strict_mode_firestore_connection_error(monkeypatch):
    """
    驗證：在強制真實模式下 (USE_MOCK_FIRESTORE=false)，
    若 Firebase 初始化失敗（模擬環境不可用且無合法憑證），save_meal_log 必須直接拋出 RuntimeError，不得降級。
    """
    # 確保強制真實模式
    monkeypatch.setenv("USE_MOCK_FIRESTORE", "false")
    
    import firebase_admin
    from app.database.db_manager import save_meal_log, get_today_date_str
    
    # 我們重置 db_manager 中的 _firebase_initialized，強制其在本次呼叫中執行 init_firebase() 的 try 區塊
    import app.database.db_manager as db_module
    monkeypatch.setattr(db_module, "_firebase_initialized", False)
    monkeypatch.setattr(db_module, "db_client", None)
    
    # 模擬 firebase_admin.initialize_app 拋出 Exception
    def mock_initialize_app(*args, **kwargs):
        raise RuntimeError("模擬 Firebase 連線建置失敗")
        
    monkeypatch.setattr(firebase_admin, "initialize_app", mock_initialize_app)
    
    # 準備一筆今日的飲食紀錄以利觸發 save_meal_log 中的 init_firebase()
    dummy_meal = {
        "date": get_today_date_str(),
        "meal_type": "lunch",
        "total": {
            "calories_kcal": 500.0,
            "protein_g": 20.0,
            "fat_g": 10.0,
            "carbs_g": 70.0
        }
    }
    
    # 預期在真實環境下且連線建置失敗時，會直接拋出 RuntimeError 且包含「禁止降級」等特徵字眼
    with pytest.raises(RuntimeError) as exc_info:
        save_meal_log("test_user_strict", dummy_meal)
        
    assert "真實" in str(exc_info.value) or "禁止降級" in str(exc_info.value)
