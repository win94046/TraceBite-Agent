import pytest
import os
from dotenv import load_dotenv
from app.agent import root_agent

# 載入 .env
load_dotenv()

def test_agent_configuration():
    """
    驗證 Agent 是否正確配置，以及是否正確綁定了我們開發的 3 個飲食工具
    """
    assert root_agent.name == "DietLoggerAgent"
    # 驗證綁定的工具名稱
    tool_names = [tool.__name__ for tool in root_agent.tools]
    assert "log_meal" in tool_names
    assert "query_today_summary" in tool_names
    assert "query_weekly_summary" in tool_names

def test_agent_api_key_and_run():
    """
    驗證 API Key 設定。若缺少 GEMINI_API_KEY，將主動拋出 Fail 並提供詳細的引導說明。
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        pytest.fail(
            "\n"
            "======================================================================\n"
            "【金鑰設定提示】測試執行失敗！\n"
            "此測試需要有效的 GEMINI_API_KEY 才能呼叫大語言模型。\n"
            "請依照以下步驟設定：\n"
            "  1. 前往 Google AI Studio 申請金鑰: https://aistudio.google.com/\n"
            "  2. 在專案根目錄的 `.env` 檔案中，填入：\n"
            "     GEMINI_API_KEY=您的真實金鑰\n"
            "======================================================================\n"
        )
    
    # 若有金鑰，進行簡單的測試呼叫，驗證 Agent 的基本回答與免責聲明
    try:
        response = root_agent.run("今天吃了什麼？")
        assert response is not None
        # 應包含我們設定的免責聲明
        assert "此結果為一般飲食紀錄與營養估算，不取代醫師或營養師建議。" in response.text
    except Exception as e:
        pytest.fail(f"呼叫 Agent 發生錯誤: {e}")
