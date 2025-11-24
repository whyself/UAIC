"""
主应用入口：独立 FastAPI 爬虫服务

本文件将 crawler 作为主应用运行，支持直接启动。
"""
from fastapi import FastAPI
from crawler.router import router as crawler_router
from crawler.lifecycle import crawler_lifespan

app = FastAPI(lifespan=crawler_lifespan)
app.include_router(crawler_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
