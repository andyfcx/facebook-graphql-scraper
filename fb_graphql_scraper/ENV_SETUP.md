# 使用 python-dotenv 配置說明

## 概述

現在您可以使用 `.env` 文件來管理敏感信息，而不需要每次運行都輸入帳號和密碼。

## 設置步驟

### 1. 安裝 python-dotenv

如果尚未安裝，請運行：

```bash
pip install python-dotenv
```

### 2. 配置 .env 文件

在項目根目錄中創建或編輯 `.env` 文件：

```dotenv
# Facebook Account Credentials
FB_EMAIL=your_email@example.com
FB_PASSWORD=your_password_here

# ChromeDriver Path
CHROMEDRIVER_PATH=/path/to/chromedriver
```

### 3. 替換為您的實際信息

- `FB_EMAIL`: 您的 Facebook 帳號（郵箱或電話號碼）
- `FB_PASSWORD`: 您的 Facebook 密碼
- `CHROMEDRIVER_PATH`: ChromeDriver 的完整路徑

**macOS 示例：**
```dotenv
FB_EMAIL=your_email@example.com
FB_PASSWORD=your_password_here
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
# 或
CHROMEDRIVER_PATH=/opt/homebrew/bin/chromedriver
```

**Linux 示例：**
```dotenv
FB_EMAIL=your_email@example.com
FB_PASSWORD=your_password_here
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
```

**Windows 示例：**
```dotenv
FB_EMAIL=your_email@example.com
FB_PASSWORD=your_password_here
CHROMEDRIVER_PATH=C:\\path\\to\\chromedriver.exe
```

## 使用方式

### 完全自動化（所有信息都在 .env 中）

直接運行腳本，無需任何交互：

```bash
python try_login.py
```

### 部分信息（若 .env 中有遺漏）

如果 .env 文件中某些字段為空，腳本會提示您輸入缺失的信息。例如，如果只在 .env 中保存了 ChromeDriver 路徑，但沒有保存帳號密碼，腳本會提示您輸入帳號和密碼。

## 安全提示

⚠️ **重要安全提示：**

1. **不要提交 .env 文件到版本控制系統（Git）**
   - 將 `.env` 添加到 `.gitignore` 文件中
   - 使用 `.env.example` 作為模板

2. **保護您的密碼**
   - 確保 .env 文件有適當的文件權限
   - 在共享計算機上要格外小心

3. **使用專用帳號**
   - 建議為爬蟲創建一個專用的 Facebook 測試帳號
   - 不要使用您的主帳號

## 文件說明

- `.env`: 實際配置文件（包含您的信息，不應提交到 Git）
- `.env.example`: 配置模板文件（可提交到 Git，供其他開發者參考）

## 文件結構

```
fb_graphql_scraper/
├── .env                    # 實際配置文件（本地使用）
├── .env.example            # 配置模板文件（參考用）
├── try_login.py            # 登錄測試腳本
└── ...
```

## 故障排除

### 問題：腳本仍然要求輸入信息

**解決方案：**
1. 確認 `.env` 文件在正確位置（與 `try_login.py` 同一目錄）
2. 檢查 `.env` 文件中是否有多餘的空格
3. 確保 `.env` 文件沒有被 `.gitignore` 忽略

### 問題：找不到 ChromeDriver

**解決方案：**
1. 驗證 CHROMEDRIVER_PATH 中的路徑是否正確
2. 確認 ChromeDriver 文件確實存在於指定位置
3. 在 macOS/Linux 上，確保 ChromeDriver 有執行權限：
   ```bash
   chmod +x /path/to/chromedriver
   ```

## 環境變量優先級

腳本按以下優先級讀取配置：

1. `.env` 文件中的值（優先級最高）
2. 用戶手動輸入的值
3. 其他環境變量（如果設置）

如果 `.env` 中有值，腳本將使用該值；如果為空，將提示用戶輸入。

## 其他使用 .env 的地方

您也可以在其他腳本中使用相同的 `.env` 文件。例如，在 `example.py` 中：

```python
from dotenv import load_dotenv
import os
from pathlib import Path

# 加載 .env 文件
load_dotenv(Path(__file__).parent / ".env")

# 讀取環境變量
fb_email = os.getenv("FB_EMAIL")
fb_password = os.getenv("FB_PASSWORD")
driver_path = os.getenv("CHROMEDRIVER_PATH")

# 使用這些變量初始化您的爬蟲
```
