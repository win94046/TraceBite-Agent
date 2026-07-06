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
    tool_names = []
    for tool in root_agent.tools:
        if hasattr(tool, "__name__"):
            tool_names.append(tool.__name__)
        elif hasattr(tool, "name"):
            tool_names.append(tool.name)
        else:
            tool_names.append(str(tool))
            
    assert "log_meal" in tool_names
    assert "log_meal_by_text" in tool_names
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


# ==============================================================================
# 鴨子型別 Mock 類別，供 ToolContext 圖片提取單元測試使用
# ==============================================================================
class DummyBlob:
    def __init__(self, data, mime_type):
        self.data = data
        self.mime_type = mime_type

class DummyPart:
    def __init__(self, inline_data):
        self.inline_data = inline_data

class DummyContent:
    def __init__(self, parts):
        self.parts = parts

class DummyEvent:
    def __init__(self, author, content):
        self.author = author
        self.content = content

class DummySession:
    def __init__(self, events):
        self.events = events

class DummyToolContext:
    def __init__(self, session):
        self.session = session

def test_log_meal_with_virtual_image_path(monkeypatch):
    """
    驗證：當傳入不存在的 input_file_0.png 虛擬圖片路徑，
    且 Session 歷史中有使用者上傳的圖片時，log_meal 能成功從 ToolContext 中提取並寫入實體圖片。
    """
    mock_bytes = b"fake jpeg image data"
    blob = DummyBlob(data=mock_bytes, mime_type="image/jpeg")
    part = DummyPart(inline_data=blob)
    content = DummyContent(parts=[part])
    event = DummyEvent(author="user", content=content)
    session = DummySession(events=[event])
    tool_context = DummyToolContext(session=session)
    
    # 驗證被還原後的 image_path 是否真的存在，且寫入的內容是我們 mock 的 mock_bytes！
    restored_path_ref = []
    
    def mock_analyze(image_path):
        restored_path_ref.append(image_path)
        assert os.path.exists(image_path)
        with open(image_path, "rb") as f:
            assert f.read() == mock_bytes
        return [{"name": "白飯", "estimated_weight_g": 150.0, "confidence": 0.95}]
        
    import app.agent as agent_module
    monkeypatch.setattr(agent_module, "analyze_food_image", mock_analyze)
    monkeypatch.setenv("USE_MOCK_FIRESTORE", "true")
    
    # 執行
    result = agent_module.log_meal(
        image_path="input_file_0.png",
        meal_type="lunch",
        tool_context=tool_context
    )
    
    # 清理建立的臨時還原檔案
    if restored_path_ref and os.path.exists(restored_path_ref[0]):
        try:
            os.remove(restored_path_ref[0])
        except Exception:
            pass
            
    assert result["version"] == "p0"
    assert len(result["detected_items"]) == 1
    assert result["detected_items"][0]["name"] == "白飯"
