# Scheduler Configuration Guide

## 自訂收集時間

每個 chokepoint 的 `state_variables.json` 都支援自訂收集時間，避免所有資料源同時收集造成負擔。

### 設定參數

```json
{
  "vessel_arrivals": {
    "description": "船隻抵達數量 (最近期數據)",
    "source": "https://portwatch.imf.org/pages/chokepoint2",
    "update_freq": "daily",
    "schedule_hour": 0,        // 設定小時 (0-23, UTC)
    "schedule_minute": 10,     // 設定分鐘 (0-59)
    "data_type": "integer"
  }
}
```

### 參數說明

| 參數 | 說明 | 預設值 | 範例 |
|------|------|--------|------|
| `update_freq` | 更新頻率 | `daily` | `daily`, `hourly`, `weekly`, `monthly` |
| `schedule_hour` | 執行小時 (UTC) | `0` | `0` (午夜), `12` (中午) |
| `schedule_minute` | 執行分鐘 | `0` | `0`, `15`, `30`, `45` |

### 支援的更新頻率

- `realtime` - 每分鐘執行
- `15min` - 每 15 分鐘執行
- `hourly` - 每小時執行（可用 `schedule_minute` 設定執行分鐘）
- `daily` - 每天執行（可用 `schedule_hour` 和 `schedule_minute` 設定時間）
- `weekly` - 每週一執行
- `monthly` - 每月 1 日執行
- `test` - 每分鐘執行（測試用）

### 目前設定

目前各 chokepoint 已設定為**錯開 10 分鐘**收集：

| Chokepoint | 執行時間 (UTC) | 說明 |
|------------|---------------|------|
| bab-el-mandeb | 00:00 | 曼德海峽 |
| panama-canal | 00:10 | 巴拿馬運河 |
| strait-of-hormuz | 00:20 | 荷姆茲海峽 |
| strait-of-malacca | 00:30 | 麻六甲海峽 |
| bosporus-strait | 00:40 | 博斯普魯斯海峽 |

### 修改建議

1. **同一資料源的不同 chokepoint** - 錯開 5-10 分鐘，避免同時請求
2. **不同資料源** - 可以使用相同時間
3. **高頻率資料** - 使用 `hourly` 或 `15min`，並在 `schedule_minute` 錯開

### 範例

**每天凌晨 2:30 收集：**
```json
{
  "update_freq": "daily",
  "schedule_hour": 2,
  "schedule_minute": 30
}
```

**每小時的第 15 分鐘收集：**
```json
{
  "update_freq": "hourly",
  "schedule_minute": 15
}
```

**每週一早上 8:00 收集：**
```json
{
  "update_freq": "weekly",
  "schedule_hour": 8,
  "schedule_minute": 0
}
```
