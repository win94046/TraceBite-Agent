import os
import datetime
from app.utils.logger import logger

# 嘗試初始化 Firebase Admin SDK (僅在 USE_MOCK_FIRESTORE 為 False 時才會真正執行連線)
_firebase_initialized = False
db_client = None

def init_firebase():
    global _firebase_initialized, db_client
    if _firebase_initialized:
        return db_client
    
    use_mock = os.environ.get("USE_MOCK_FIRESTORE", "true").lower() == "true"
    if use_mock:
        logger.info("[DBManager] 啟用本地 InMemory Mock 資料庫模式，不連線至 Firebase。")
        _firebase_initialized = True
        return None
        
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        if not firebase_admin._apps:
            # 如果有設定模擬器環境變數，可以使用匿名憑證
            if os.environ.get("FIRESTORE_EMULATOR_HOST"):
                logger.info(
                    f"[DBManager] 偵測到 Firestore 模擬器位址: {os.environ.get('FIRESTORE_EMULATOR_HOST')}"
                )
                cred = credentials.AnonymousCredentials()
                firebase_admin.initialize_app(cred)
            else:
                logger.info("[DBManager] 嘗試初始化 Firebase Application Default Credentials...")
                firebase_admin.initialize_app()
                
        db_client = firestore.client()
        _firebase_initialized = True
        logger.info("[DBManager] Firebase Firestore 連線初始化成功。")
    except Exception as e:
        if not use_mock:
            logger.error(f"[DBManager] 在真實環境下，Firebase Firestore 連線失敗: {e}")
            raise RuntimeError(f"真實 Firestore 初始化失敗且禁止降級: {e}") from e
        logger.error(f"[DBManager] Firebase Firestore 初始化失敗: {e}，自動降級至 Mock 模式。")
        os.environ["USE_MOCK_FIRESTORE"] = "true"
        _firebase_initialized = True
        
    return db_client


# ==============================================================================
# InMemory Mock 資料庫實作 (用以進行本地快速測試)
# ==============================================================================
class InMemoryMockDB:
    def __init__(self):
        # 結構: { userId: { mealLogId: log_data } }
        self.meal_logs = {}
        # 結構: { userId: { yyyyMMdd: summary_data } }
        self.daily_summaries = {}

    def clear(self):
        self.meal_logs.clear()
        self.daily_summaries.clear()
        logger.debug("[DBManager Mock] 已清空 InMemory 測試資料。")

mock_db = InMemoryMockDB()


# ==============================================================================
# 核心資料庫管理函數
# ==============================================================================
def get_today_date_str() -> str:
    """
    取得本機今日日期字串 YYYY-MM-DD
    """
    return datetime.date.today().strftime("%Y-%m-%d")

def save_meal_log(user_id: str, meal_data: dict) -> str:
    """
    儲存飲食紀錄至資料庫，並限制僅能新增今日日期的紀錄。
    若儲存成功，會自動同步累加並更新該日的 daily_summaries 摘要。
    """
    logger.info(f"[DBManager] 開始儲存飲食紀錄，User: '{user_id}'，餐別: '{meal_data.get('meal_type')}'")
    
    # 1. 驗證日期限制：僅限今日日期
    today_str = get_today_date_str()
    record_date = meal_data.get("date")
    
    if record_date != today_str:
        logger.warning(
            f"[DBManager] 新增紀錄失敗！限制僅能新增今日日期 ({today_str})，但傳入的日期為 ({record_date})"
        )
        raise ValueError("P0 only supports today's meal logging.")
        
    # 初始化資料庫連線
    init_firebase()
    use_mock = os.environ.get("USE_MOCK_FIRESTORE", "true").lower() == "true"
    
    # 產生唯一的 mealLogId，結合時間戳與隨機 UUID 尾綴防碰撞
    import uuid
    timestamp_suffix = datetime.datetime.now().strftime("%H%M%S_%f")[:10] # 精確到毫秒的尾數
    meal_log_id = f"meal_{record_date.replace('-', '')}_{timestamp_suffix}_{uuid.uuid4().hex[:6]}"
    
    # 準備寫入的格式
    record = meal_data.copy()
    record["id"] = meal_log_id
    record["user_id"] = user_id
    record["created_at"] = datetime.datetime.now().isoformat()
    record["status"] = record.get("status", "active")
    record["updated_at"] = record.get("updated_at", None)
    record["deleted_at"] = record.get("deleted_at", None)
    record["revision"] = record.get("revision", 1)
    
    # 計算此餐的總營養素
    meal_total = record.get("total", {
        "calories_kcal": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "carbs_g": 0.0
    })
    
    if use_mock:
        # A. Mock 模式儲存
        # 寫入 meal_logs
        if user_id not in mock_db.meal_logs:
            mock_db.meal_logs[user_id] = {}
        mock_db.meal_logs[user_id][meal_log_id] = record
        
        # 更新 daily_summaries (yyyyMMdd 格式)
        yyyyMMdd = record_date.replace("-", "")
        if user_id not in mock_db.daily_summaries:
            mock_db.daily_summaries[user_id] = {}
            
        current_summary = mock_db.daily_summaries[user_id].get(yyyyMMdd, {
            "date": record_date,
            "total": {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}
        })
        
        # 累加數值
        current_summary["total"]["calories_kcal"] = round(current_summary["total"]["calories_kcal"] + meal_total.get("calories_kcal", 0.0), 2)
        current_summary["total"]["protein_g"] = round(current_summary["total"]["protein_g"] + meal_total.get("protein_g", 0.0), 2)
        current_summary["total"]["fat_g"] = round(current_summary["total"]["fat_g"] + meal_total.get("fat_g", 0.0), 2)
        current_summary["total"]["carbs_g"] = round(current_summary["total"]["carbs_g"] + meal_total.get("carbs_g", 0.0), 2)
        
        mock_db.daily_summaries[user_id][yyyyMMdd] = current_summary
        
        logger.info(
            f"[DBManager Mock] 飲食紀錄已成功寫入，ID: '{meal_log_id}'。 "
            f"已更新當日摘要總量: {current_summary['total']}"
        )
    else:
        # B. Firestore 實體模式儲存
        db = init_firebase()
        
        # 使用 Transaction 或直接寫入
        # 1. 寫入 meal_logs
        doc_ref = db.collection("users").document(user_id).collection("meal_logs").document(meal_log_id)
        doc_ref.set(record)
        
        # 2. 累加更新 daily_summaries
        yyyyMMdd = record_date.replace("-", "")
        summary_ref = db.collection("users").document(user_id).collection("daily_summaries").document(yyyyMMdd)
        
        # 讀取並合併
        summary_doc = summary_ref.get()
        if summary_doc.exists:
            current_summary = summary_doc.to_dict()
            current_total = current_summary.get("total", {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0})
            new_total = {
                "calories_kcal": round(current_total.get("calories_kcal", 0.0) + meal_total.get("calories_kcal", 0.0), 2),
                "protein_g": round(current_total.get("protein_g", 0.0) + meal_total.get("protein_g", 0.0), 2),
                "fat_g": round(current_total.get("fat_g", 0.0) + meal_total.get("fat_g", 0.0), 2),
                "carbs_g": round(current_total.get("carbs_g", 0.0) + meal_total.get("carbs_g", 0.0), 2)
            }
            summary_ref.update({"total": new_total})
        else:
            new_total = {
                "calories_kcal": round(meal_total.get("calories_kcal", 0.0), 2),
                "protein_g": round(meal_total.get("protein_g", 0.0), 2),
                "fat_g": round(meal_total.get("fat_g", 0.0), 2),
                "carbs_g": round(meal_total.get("carbs_g", 0.0), 2)
            }
            summary_ref.set({
                "date": record_date,
                "total": new_total
            })
            
        logger.info(f"[DBManager Firestore] 飲食紀錄與摘要已成功寫入，ID: '{meal_log_id}'。")
        
    return meal_log_id

def get_today_summary(user_id: str) -> dict:
    """
    讀取今日的總計與今日所有飲食紀錄列表
    """
    today_str = get_today_date_str()
    logger.debug(f"[DBManager] 讀取今日飲食摘要，User: '{user_id}'，今日日期: '{today_str}'")
    
    init_firebase()
    use_mock = os.environ.get("USE_MOCK_FIRESTORE", "true").lower() == "true"
    
    meals_list = []
    total_nutrients = {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}
    
    if use_mock:
        # A. Mock 模式讀取
        user_logs = mock_db.meal_logs.get(user_id, {})
        # 篩選今日且狀態為 active 的明細
        meals_list = [
            log for log in user_logs.values()
            if log.get("date") == today_str and log.get("status") == "active"
        ]
        
        # 讀取當日摘要總量
        yyyyMMdd = today_str.replace("-", "")
        summary = mock_db.daily_summaries.get(user_id, {}).get(yyyyMMdd, {})
        total_nutrients = summary.get("total", total_nutrients)
    else:
        # B. Firestore 模式讀取
        db = init_firebase()
        
        # 1. 讀取今日明細
        logs_ref = db.collection("users").document(user_id).collection("meal_logs")
        query = logs_ref.where("date", "==", today_str).where("status", "==", "active").stream()
        for doc in query:
            meals_list.append(doc.to_dict())
            
        # 2. 讀取當日摘要
        yyyyMMdd = today_str.replace("-", "")
        summary_ref = db.collection("users").document(user_id).collection("daily_summaries").document(yyyyMMdd)
        summary_doc = summary_ref.get()
        if summary_doc.exists:
            total_nutrients = summary_doc.to_dict().get("total", total_nutrients)
            
    logger.info(
        f"[DBManager] 今日摘要讀取完畢，明細筆數: {len(meals_list)}，"
        f"總熱量: {total_nutrients.get('calories_kcal')} kcal"
    )
    return {
        "date": today_str,
        "total": total_nutrients,
        "meals": meals_list
    }

def get_weekly_summary(user_id: str) -> dict:
    """
    讀取本週統計 (定義為：包含今日的前 7 天)
    回傳：每日總和列表、週平均與本週統計指標。
    """
    today_dt = datetime.date.today()
    logger.debug(f"[DBManager] 讀取本週飲食摘要 (前 7 天)，User: '{user_id}'，今日日期: '{today_dt}'")
    
    # 取得前 7 天的日期字串清單
    past_7_days = [
        (today_dt - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(7)
    ]
    # 由舊到新排序
    past_7_days.reverse()
    
    init_firebase()
    use_mock = os.environ.get("USE_MOCK_FIRESTORE", "true").lower() == "true"
    
    daily_totals = []
    total_nutrients = {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}
    
    if use_mock:
        # A. Mock 模式讀取本週
        for date_str in past_7_days:
            yyyyMMdd = date_str.replace("-", "")
            summary = mock_db.daily_summaries.get(user_id, {}).get(yyyyMMdd, {
                "date": date_str,
                "total": {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}
            })
            day_total = summary["total"]
            
            daily_totals.append({
                "date": date_str,
                **day_total
            })
            
            # 累加總計以利計算平均
            for key in total_nutrients:
                total_nutrients[key] += day_total.get(key, 0.0)
    else:
        # B. Firestore 模式讀取本週
        db = init_firebase()
        
        # 逐日讀取 (7 次讀取在 P0 規模是可接受的，且速度快)
        for date_str in past_7_days:
            yyyyMMdd = date_str.replace("-", "")
            summary_ref = db.collection("users").document(user_id).collection("daily_summaries").document(yyyyMMdd)
            summary_doc = summary_ref.get()
            
            if summary_doc.exists:
                day_total = summary_doc.to_dict().get("total", {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0})
            else:
                day_total = {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}
                
            daily_totals.append({
                "date": date_str,
                **day_total
            })
            
            for key in total_nutrients:
                total_nutrients[key] += day_total.get(key, 0.0)
                
    # 計算本週平均值 (除以 7)
    weekly_average = {
        key: round(total_nutrients[key] / 7.0, 2)
        for key in total_nutrients
    }
    
    logger.info(
        f"[DBManager] 本週統計讀取完畢。週開始: '{past_7_days[0]}'，"
        f"週結束: '{past_7_days[-1]}'，每日統計筆數: {len(daily_totals)}"
    )
    return {
        "week_start": past_7_days[0],
        "week_end": past_7_days[-1],
        "daily_totals": daily_totals,
        "weekly_average": weekly_average
    }
