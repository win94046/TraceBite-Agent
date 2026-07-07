import sys
from app.utils.logger import logger

# 台灣常見便當食材營養資料庫 (數值以每 100g 為單位)
# 格式: {食物名稱: (熱量 kcal, 蛋白質 g, 脂肪 g, 碳水 g)}
TAIWAN_FOOD_DATABASE = {
    "白飯": (130.0, 2.4, 0.3, 29.0),
    "雞腿": (220.0, 18.0, 15.0, 1.0),
    "排骨": (280.0, 16.0, 22.0, 2.0),
    "滷蛋": (140.0, 13.0, 9.0, 1.0),
    "青菜": (25.0, 1.5, 0.2, 4.0),
    "滷肉": (350.0, 12.0, 32.0, 2.0),
    "滷油豆腐": (130.0, 8.0, 9.0, 3.0),
    "煎香腸": (350.0, 15.0, 30.0, 5.0),
}

def search_food(query: str) -> list[str]:
    """
    搜尋名稱相似的食物
    """
    logger.debug(f"[NutritionDB] 開始搜尋食物，關鍵字: '{query}'")
    if not query:
        return []
    
    results = [name for name in TAIWAN_FOOD_DATABASE.keys() if query in name]
    logger.info(f"[NutritionDB] 食物搜尋完畢，關鍵字: '{query}'，結果筆數: {len(results)}")
    return results

def get_nutrition(food_name: str) -> dict | None:
    """
    取得食物每 100g 的營養成分
    """
    logger.debug(f"[NutritionDB] 查詢每 100g 營養素，食物名稱: '{food_name}'")
    if food_name in TAIWAN_FOOD_DATABASE:
        val = TAIWAN_FOOD_DATABASE[food_name]
        return {
            "calories_kcal": val[0],
            "protein_g": val[1],
            "fat_g": val[2],
            "carbs_g": val[3],
            "database": "Taiwan Food Nutrition Database"
        }
    logger.debug(f"[NutritionDB] 查詢不到該食物的營養資料: '{food_name}'")
    return None

def estimate_nutrition(food_name: str, weight_g: float) -> dict:
    """
    根據食物名稱與重量估算總營養素。
    若資料庫查無此項目，會進行合理估算並給予較低信心度。
    """
    logger.info(f"[NutritionDB] 開始估算營養素: 食物名稱='{food_name}', 重量={weight_g}g")
    
    # 預設極低值以防萬一
    weight_g = max(0.0, weight_g)
    ratio = weight_g / 100.0
    
    # 嘗試查詢
    nutr = get_nutrition(food_name)
    
    if nutr:
        # 資料庫查有此項目
        calories = round(nutr["calories_kcal"] * ratio, 2)
        protein = round(nutr["protein_g"] * ratio, 2)
        fat = round(nutr["fat_g"] * ratio, 2)
        carbs = round(nutr["carbs_g"] * ratio, 2)
        confidence = 0.95
        matched_name = food_name
        source_type = "database_lookup"
        database_name = nutr["database"]
        logger.info(f"[NutritionDB] 資料庫匹配成功: '{food_name}' -> 估算熱量: {calories} kcal, 信心度: {confidence}")
    else:
        # 資料庫查無此項目，給予通用平均便當食材的預估 (約 150 kcal/100g)
        # 並降低信心度
        calories = round(150.0 * ratio, 2)
        protein = round(6.0 * ratio, 2)
        fat = round(8.0 * ratio, 2)
        carbs = round(12.0 * ratio, 2)
        confidence = 0.50
        matched_name = "未匹配 (通用估算)"
        source_type = "estimated"
        database_name = "Mock Nutrition Estimator"
        logger.warning(
            f"[NutritionDB] 資料庫查無此項目: '{food_name}'，使用通用預估值，"
            f"估算熱量: {calories} kcal, 信心度: {confidence}"
        )
        
    result = {
        "name": food_name,
        "estimated_weight_g": weight_g,
        "calories_kcal": calories,
        "protein_g": protein,
        "fat_g": fat,
        "carbs_g": carbs,
        "confidence": confidence,
        "nutrition_source": {
            "database": database_name,
            "matched_name": matched_name,
            "source_type": source_type
        }
    }
    
    logger.debug(f"[NutritionDB] 營養素估算完成，輸出內容: {result}")
    return result
