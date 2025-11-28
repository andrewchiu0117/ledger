# Google Sheets 整合設定說明

## 概述

此應用程式現在可以直接從 Google Sheets 讀取資料，而不需要本地資料庫。

## 設定方式

### 方式 1: 公開分享（最簡單，推薦）

1. 將您的 Google Sheet 設為「任何有連結的人都可以檢視」
   - 在 Google Sheets 中，點擊右上角的「分享」
   - 選擇「變更為任何有連結的使用者」
   - 權限設為「檢視者」

2. 安裝必要的套件：
   ```bash
   pip install -r requirements.txt
   ```

3. 完成！應用程式會自動使用公開 CSV 方式讀取資料

### 方式 2: 使用服務帳號（需要認證）

如果您不想公開分享 Sheet，可以使用 Google 服務帳號：

1. 建立 Google Cloud 專案並啟用 Google Sheets API
2. 建立服務帳號並下載 JSON 憑證檔案
3. 將憑證檔案命名為 `credentials.json` 並放在專案根目錄
4. 在 Google Sheets 中分享 Sheet 給服務帳號的 email（格式：xxx@xxx.iam.gserviceaccount.com）

## Google Sheets 結構

請確保您的 Google Sheet 包含以下工作表（Sheet tabs）：

- **Transactions** - 交易記錄
  - 欄位：日期 (date), 類型 (type), 類別 (category), 金額 (amount), 支付方式 (payment_method), 備註 (description), 帳戶 (account_name)
  
- **Accounts** - 帳戶資訊
  - 欄位：名稱 (name), 類型 (type), 初始餘額 (initial_balance)
  
- **Stocks** - 股票資訊
  - 欄位：代號 (symbol), 購買日期 (buy_date), 買入價格 (buy_price), 數量 (quantity), 手續費 (broker_fee), 交易費 (transaction_fee), 狀態 (status)
  
- **Categories** - 類別資訊
  - 欄位：名稱 (name), 類型 (type)
  
- **Budgets** - 預算資訊
  - 欄位：月份 (month), 金額 (amount)

## 自訂工作表名稱

如果您的 Google Sheet 工作表名稱不同，可以修改 `modules/sheets.py` 中的 `SHEET_NAMES` 字典：

```python
SHEET_NAMES = {
    'transactions': '您的交易工作表名稱',
    'accounts': '您的帳戶工作表名稱',
    'stocks': '您的股票工作表名稱',
    'categories': '您的類別工作表名稱',
    'budgets': '您的預算工作表名稱'
}
```

## 目前設定的 Google Sheet

- Spreadsheet ID: `1i1hT5FTRsNTBBVvDyGY26Zz2YKOD8Z3m-UwV-ljHREA`
- Sheet GID: `893494942`

如需更改，請修改 `modules/sheets.py` 中的 `SPREADSHEET_ID` 和 `SHEET_GID`。

