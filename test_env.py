import sys
import os

def main():
    print("=== Python 專案環境測試 ===")
    print(f"Python 執行路徑: {sys.executable}")
    print(f"Python 版本: {sys.version}")
    print(f"目前工作目錄: {os.getcwd()}")
    print("==========================")
    print("環境確認成功，您已可以開始在此專案中開發 Python 程式！")

if __name__ == "__main__":
    main()
