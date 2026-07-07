import uvicorn
from app.fast_api_app import app

if __name__ == "__main__":
    # 使用 reload=True 方便開發，綁定 port 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
