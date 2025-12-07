```
nju_crawler/
├─ main.py                # 主应用入口
├─ requirements.txt       # 依赖列表
├─ .env                   # 环境变量配置
├─ crawler/               # 学院官网爬虫模块
│    ├─ __init__.py
│    ├─ config.py
│    ├─ models.py
│    ├─ services.py
│    ├─ router.py
│    └─ lifecycle.py
├─ wechat/                # 微信公众号爬虫模块
│    ├─ __init__.py
│    ├─ config.py
│    ├─ models.py
│    ├─ services.py
│    └─ router.py
├─ storage/               # 公共数据库与API模块
│    ├─ __init__.py
│    ├─ config.py
│    ├─ database.py
│    └─ router.py         # 统一查询API
└─ ...
```

# 南京大学教育资讯爬虫平台（nju_crawler）

本项目为南京大学教育资讯聚合与爬取平台，支持自动采集各学院官网及微信公众号的新闻、通知等内容，并通过统一 API 提供查询与导出。

---

## 一、环境准备

- Python 3.8 及以上（推荐 3.10+）
- Windows/Linux/macOS 均可运行
- 推荐使用虚拟环境（venv）
- 浏览器驱动（如 geckodriver for Firefox，需配合 Selenium 使用）
- 微信公众号采集需有相关权限

### 依赖安装

1. 创建并激活虚拟环境：
   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows
   .\venv\Scripts\activate
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 安装浏览器与驱动（以 Firefox/geckodriver 为例）：
   - [下载 Firefox 浏览器](https://www.mozilla.org/zh-CN/firefox/new/)
   - [下载 geckodriver](https://github.com/mozilla/geckodriver/releases)
   - 将 geckodriver 放入项目目录或系统 PATH

4. 配置环境变量（可选，推荐 .env 文件）：
   在项目根目录新建 `.env`，如：
   ```env
   CRAWL_INTERVAL=3600
   REQUEST_TIMEOUT=30
   MAX_RETRIES=3
   AUTO_CRAWL_ENABLED=true
   CRAWLER_DB_PATH=./data/crawler.db
   ```

---

## 二、项目启动

1. 启动主服务：
   ```bash
   python main.py
   # 或开发模式
   uvicorn main:app --reload
   ```
2. 访问 API 文档：
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

---

## 三、目录结构说明

```
nju_crawler/
├─ main.py                # 主应用入口
├─ requirements.txt       # 依赖列表
├─ .env                   # 环境变量配置
├─ crawler/               # 官网爬虫模块
├─ wechat/                # 公众号爬虫模块
├─ storage/               # 数据库与API
├─ config/sources/        # 官网与公众号源配置
└─ ...
```

---

## 四、自定义与添加数据源

### 1. 添加/自定义官网源

所有官网源配置均位于 `config/sources/` 目录下，每个学院/部门一个 JSON 文件（如 `arch.json`）。

**步骤：**
1. 复制或新建一个 JSON 文件（如 `mycollege.json`）。
2. 按如下结构填写：
   ```json
   {
     "sources": [
       {
         "id": "mycollege_news",
         "name": "我的学院-新闻",
         "type": "api",  // 或 html
         "base_url": "https://mycollege.nju.edu.cn",
         "list_url": "https://mycollege.nju.edu.cn/news/index.html",
         "pagination_mode": "api",  // 或 html
         "api_url": "https://mycollege.nju.edu.cn/api/news",
         "max_pages": 3,
         "headers": { ... },
         "payload": { ... },
         "selectors": {
           "item_container": "infolist",
           "title": "title",
           "date": "releasetime",
           "url": "url"
         }
       }
     ]
   }
   ```
3. 主要字段说明：
   - `id`：唯一标识，建议格式为“学院缩写_栏目名”
   - `type`：数据获取方式，支持 `api` 或 `html`（页面解析）
   - `selectors`：用于定位新闻列表、标题、时间、链接等字段的 CSS 选择器或 JSON 路径
   - 其他字段可参考现有配置
4. 配置完成后，可用如下命令测试：
   ```bash
   python test_config.py config/sources/mycollege.json mycollege_news
   ```

### 2. 添加/自定义公众号源

所有公众号源配置在 `config/sources/wechat.json` 文件中，为一个数组，每个对象代表一个公众号。

**步骤：**
1. 打开 `config/sources/wechat.json`，按如下格式添加：
   ```json
   {
     "id": "wechat_xxxxxxxx",
     "name": "我的公众号",
     "biz": "xxxxxxxx",
     "count": 5,
     "created_at": 1234567890
   }
   ```
   - `id`：格式为 `wechat_` + 公众号 biz 字段
   - `name`：公众号名称
   - `biz`：公众号唯一标识，可通过抓包或第三方工具获取
   - `count`：每次采集的推文数量
   - `created_at`：添加时间戳
2. 保存后，重启服务即可生效。

---

## 五、常见问题与建议

- **依赖安装慢？** 可使用阿里云源：
  ```bash
  pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
  ```
- **Selenium 报错？** 检查浏览器与驱动版本匹配，驱动需在 PATH。
- **公众号采集失败？** 需有对应权限，biz 可通过抓包获取。
- **API 无数据？** 检查 config/sources/ 下的配置文件与源站点结构是否一致。

---

## 六、协作与开发规范

- 推荐每位开发者使用虚拟环境，避免依赖冲突
- 新增依赖请写入 `requirements.txt` 并同步
- 敏感信息（如数据库路径、API 密钥）请用 `.env` 管理，勿提交到 Git
- 统一通过 `main.py` 启动或集成到其他 FastAPI 项目

---

如有问题请联系项目维护者。