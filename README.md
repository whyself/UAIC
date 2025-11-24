# nju_crawler

## 快速开始（开发环境搭建）

1. 创建并激活虚拟环境：
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. 安装依赖：
   ```powershell
   pip install -r requirements.txt
   ```

3. 启动主应用（独立服务模式）：
   ```powershell
   python main.py
   # 或
   uvicorn main:app --reload
   ```

## 目录结构说明
- `crawler/`：爬虫模块主包，包含所有核心代码
- `main.py`：主应用入口，可直接运行
- `requirements.txt`：依赖列表
- `venv/`：虚拟环境目录（自动生成，无需提交到Git）

## 贡献开发
- 推荐每位开发者使用虚拟环境，避免依赖冲突
- 所有新依赖请写入 `requirements.txt`
- 代码风格建议遵循 PEP8
- 统一通过 `main.py` 或集成到其他 FastAPI 项目

---
如有问题请联系项目维护者。