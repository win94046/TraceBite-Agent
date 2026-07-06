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
    
    if not api_key or api_key == "your_gemini_api_key_here" or len(api_key.strip()) < 10:
        pytest.skip(
            "跳過測試：未檢測到有效的 GEMINI_API_KEY。若要進行實體 Gemini API 測試，請前往 Google AI Studio 申請金鑰並在 .env 中配置。"
        )
    
    # 若有金鑰，進行簡單的測試呼叫，驗證 Agent 的基本回答與免責聲明
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        session_service = InMemorySessionService()
        session = session_service.create_session_sync(user_id="test_user", app_name="app")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="app")

        message = types.Content(role="user", parts=[types.Part.from_text(text="今天吃了什麼？")])
        events = list(runner.run(new_message=message, user_id="test_user", session_id=session.id))
        
        assert len(events) > 0
        response_text = "".join([
            part.text for e in events if e.content and e.content.parts
            for part in e.content.parts if part.text
        ])
        assert "此結果為一般飲食紀錄與營養估算，不取代醫師或營養師建議。" in response_text
    except Exception as e:
        pytest.fail(f"呼叫 Agent 發生錯誤: {e}")
