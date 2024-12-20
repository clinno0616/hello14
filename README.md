# Elasticsearch 資料瀏覽器

一個基於 Streamlit 的 Elasticsearch 資料瀏覽工具，支援索引瀏覽、資料查看和統計資訊顯示。專門針對 Elasticsearch 6.8.2 版本開發。

## 功能特點

- 索引列表瀏覽（倒序排列）
- 文檔內容查看（支援分頁）
- 索引統計資訊
- 資料下載（JSON 格式）
- 支援調試模式

## 系統需求

- Python 3.7+
- Elasticsearch 6.8.2
- 相關 Python 套件（見安裝說明）

## 安裝步驟

1. 安裝必要的 Python 套件：
```bash
pip install streamlit elasticsearch==6.8.2 pandas
```

2. 下載專案檔案：
```bash
git clone [你的專案 URL]
cd [專案目錄]
```

## 使用方法

1. 啟動應用程式：
```bash
streamlit run app.py
```

2. 在瀏覽器中訪問顯示的 URL（預設為 http://localhost:8501）

3. 在介面中設定：
   - 主機名稱（預設: localhost）
   - 端口（預設: 9200）
   - 協議（http/https）

## 主要功能說明

### 索引列表
- 位於左側欄
- 倒序排列顯示所有索引
- 支援直接選擇查看

### 文檔內容
- 顯示選定索引的文檔內容
- 支援分頁瀏覽（每頁 20/50/100 筆）
- 支援資料下載

### 索引統計
- 顯示文檔數量
- 顯示已刪除文檔數
- 顯示存儲大小
- 顯示索引和搜尋操作次數

## 配置說明

可在程式碼中調整的主要參數：

```python
# 連接超時設定
timeout=30
max_retries=3
retry_on_timeout=True

# 分頁大小選項
page_size_options=[20, 50, 100]

# 預設連接設定
default_host='localhost'
default_port=9200
default_scheme='http'
```

## 故障排除

1. 連接錯誤
   - 確認 Elasticsearch 服務是否運行
   - 檢查主機名稱和端口設定
   - 確認網路連接

2. 資料顯示問題
   - 確認索引是否存在
   - 檢查文檔權限設定
   - 開啟調試模式查看詳細信息

## 開發說明

主要文件結構：

```
├── app.py             # 主程式
└── README.md          # 說明文件
```

### 代碼結構

- `ElasticsearchClient` 類：處理與 ES 的所有互動
- `main()` 函數：處理 UI 邏輯和使用者互動

## 注意事項

1. 此工具專為 Elasticsearch 6.8.2 版本開發，其他版本可能需要調整
2. 建議在正式使用前先在測試環境驗證
3. 大型索引的查詢可能需要較長時間
4. 請注意記憶體使用量，特別是處理大量資料時
