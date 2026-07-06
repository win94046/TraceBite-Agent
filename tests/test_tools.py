import pytest
from app.database.nutrition_db import search_food, get_nutrition, estimate_nutrition
from app.tools.image_analyzer import analyze_food_image

def test_search_food():
    # 測試基本搜尋
    results = search_food("飯")
    assert "白飯" in results
    
    # 測試找不到的食物
    empty_results = search_food("披薩")
    assert len(empty_results) == 0

def test_get_nutrition():
    # 測試存在的食物
    nutr = get_nutrition("白飯")
    assert nutr is not None
    assert nutr["calories_kcal"] == 130.0
    assert nutr["database"] == "Taiwan Food Nutrition Database"
    
    # 測試不存在的食物
    assert get_nutrition("無此食物") is None

def test_estimate_nutrition():
    # 測試精確重量乘算 (白飯 150g -> 130 * 1.5 = 195 kcal)
    res = estimate_nutrition("白飯", 150.0)
    assert res["name"] == "白飯"
    assert res["estimated_weight_g"] == 150.0
    assert res["calories_kcal"] == 195.0
    assert res["protein_g"] == 3.6
    assert res["confidence"] == 0.95
    assert res["nutrition_source"]["source_type"] == "database_lookup"
    
    # 測試不存在食物之通用預估 (Mock Nutrition Estimator, 150 kcal/100g, 信心度 0.5)
    res_mock = estimate_nutrition("神秘便當", 200.0)
    assert res_mock["calories_kcal"] == 300.0
    assert res_mock["confidence"] == 0.50
    assert res_mock["nutrition_source"]["source_type"] == "estimated"

def test_analyze_food_image():
    # 測試內含 chicken 關鍵字
    res_chicken = analyze_food_image("/path/to/chicken_lunchbox.jpg")
    foods = [item["name"] for item in res_chicken]
    assert "雞腿" in foods
    assert "白飯" in foods
    
    # 測試預設值
    res_default = analyze_food_image("unknown.jpg")
    foods_default = [item["name"] for item in res_default]
    assert "白飯" in foods_default
    assert "青菜" in foods_default
