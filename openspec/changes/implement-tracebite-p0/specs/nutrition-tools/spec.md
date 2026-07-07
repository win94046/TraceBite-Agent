## ADDED Requirements

### Requirement: 營養資料查詢與估算
系統 SHALL 提供營養查詢工具，支援搜尋食物、獲取特定食物的營養成分（熱量、蛋白質、脂肪、碳水化合物），並能根據給定的重量估算總營養素。

#### Scenario: 成功依重量估算食物營養
- **WHEN** 呼叫 `estimate_nutrition` 傳入食物名稱 "白飯" 與重量 150 克
- **THEN** 系統回傳熱量為 195 kcal，蛋白質 3.6g，脂肪 0.4g，碳水 43.5g，並註明資料來源為 "Taiwan Food Nutrition Database"

#### Scenario: 食物未包含於資料庫時的估算
- **WHEN** 呼叫 `estimate_nutrition` 查詢未包含的食物
- **THEN** 系統回傳預估值，但將信心度（confidence）標記為較低數值，且在資料來源中註記為預估值
