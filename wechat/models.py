from __future__ import annotations

from pydantic import BaseModel, HttpUrl
from typing import Any, Dict, List, Optional, Union


class WechatRequest(BaseModel):
	"""请求体：指定要抓取的 wechat 源 id，或 "all" 表示全部"""
	source: str


class SingleRequest(BaseModel):
	"""请求体：抓取单个文章链接"""
	url: HttpUrl


class ErrorResponse(BaseModel):
	error: str
	code: str = "400"


class WechatResponse(BaseModel):
	code: str = "200"
	data: List[dict]


class SessionUpdateRequest(BaseModel):
	token: Optional[str] = None
	cookies: Optional[List[Dict[str, Any]]] = None
	cookies_str: Optional[str] = None
	user_agent: Optional[str] = None
	expiry: Optional[Union[int, str]] = None
	expiry_human: Optional[str] = None
	saved_at: Optional[str] = None

	class Config:
		extra = "allow"


class SessionUpdateResponse(BaseModel):
	message: str = "session saved"
	session: Dict[str, Any]

