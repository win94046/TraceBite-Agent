## ADDED Requirements

### Requirement: 飲食紀錄與每日摘要儲存
系統 SHALL 將飲食紀錄與每日摘要儲存至 Cloud Firestore。對於每筆飲食紀錄，必須包含餐別、時間、偵測食物明細、總營養素與資料來源。當有新飲食紀錄儲存時，系統 SHALL 同步更新當日的總營養素摘要。

#### Scenario: 成功儲存飲食紀錄並更新今日摘要
- **WHEN** 儲存一筆午餐飲食紀錄（含有白飯 150g）
- **THEN** Firestore 成功建立該紀錄，且當日的 `daily_summaries` 中對應的總熱量與三大營養素會累加此餐的數值

---

### Requirement: 限登今日紀錄與欄位保留
系統 SHALL 拒絕新增非今日日期的飲食紀錄，且資料結構中 MUST 保留 `userId`、`status` (active)、`created_at`、`updated_at`、`deleted_at` 與 `revision` 欄位以供未來擴充。

#### Scenario: 嘗試新增過去日期的飲食紀錄
- **WHEN** 發送飲食紀錄的日期為昨天的日期
- **THEN** 系統拒絕新增並回傳錯誤訊息，提示 "P0 only supports today's meal logging."
