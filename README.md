# SeeSeaIntelligence

SeeSea 資料收集與處理系統 - 全球航運情報自動化爬蟲

## 📊 系統概覽

這是 SeeSea 專案的資料收集和處理核心，負責從 IMF PortWatch API 自動收集全球主要航道的船隻流量資料，並進行清洗、處理和存儲。

## 🎯 主要功能

- **自動資料收集**: 定時從 IMF PortWatch API 抓取最新的船隻流量資料
- **資料處理**: 清洗、驗證和標準化原始資料
- **資料回填**: 自動補齊歷史缺失資料
- **排程執行**: 可配置的自動排程系統
- **資料導出**: 支援 CSV、Pickle 等多種格式

## 📁 目錄結構

```
SeeSeaIntelligence/
├── src/                          # 原始碼
│   ├── collectors/              # 資料收集器
│   │   ├── __init__.py
│   │   └── imf_portwatch.py    # IMF PortWatch API 爬蟲
│   ├── core/                    # 核心功能
│   │   ├── collector.py        # 收集器基礎類別
│   │   ├── processor.py        # 資料處理器
│   │   ├── backfill.py         # 歷史資料回填
│   │   └── logger.py           # 日誌系統
│   ├── logistics/              # 航道配置
│   │   └── chokepoints/        # 各航道資料夾
│   ├── main.py                 # 主程式入口
│   ├── scheduler.py            # 排程系統
│   └── process_data.py         # 資料處理腳本
│
├── data/                        # 原始資料（Pickle 格式）
├── processed/                   # 處理後的資料（CSV 格式）
├── scripts/                     # 工具腳本
├── config/                      # 配置文件
├── requirements.txt            # Python 依賴
└── .env.example               # 環境變數範例
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. 配置環境

```bash
cp .env.example .env
# 編輯 .env 填入必要的 API Keys
```

### 3. 運行

```bash
# 單次收集所有航道（推薦）
python src/scheduler.py --once

# 單次收集特定航道
python src/main.py --chokepoint suez-canal --variable vessel_arrivals

# 啟動排程器（自動定時收集）
python src/scheduler.py --start

# 檢查缺失的資料
python src/scheduler.py --check
```

## 📊 支援的航道

- 蘇伊士運河 (suez-canal)
- 霍爾木茲海峽 (strait-of-hormuz)
- 麻六甲海峽 (strait-of-malacca)
- 巴拿馬運河 (panama-canal)
- 博斯普魯斯海峽 (bosporus-strait)
- 曼德海峽 (bab-el-mandeb)

## 🔄 資料流程

```
IMF API → 原始資料(Pickle) → 處理器 → CSV → 資料庫
```

## 📄 授權

Proprietary
