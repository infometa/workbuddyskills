"""
配置管理模块 - 使用 pydantic 验证
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class APIConfig(BaseModel):
    provider: str = Field(default="openai", description="API 提供商")
    base_url: str = Field(default="", description="API 基础 URL")
    api_key: str = Field(default="", description="API 密钥")
    model: str = Field(default="gpt-3.5-turbo", description="模型名称")
    temperature: float = Field(default=0.8, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4096, ge=100, le=32000, description="最大令牌数")

    @field_validator("api_key", mode="before")
    @classmethod
    def get_api_key_from_env(cls, v: str) -> str:
        return os.environ.get("NOVEL_API_KEY", v)

    @field_validator("base_url", mode="before")
    @classmethod
    def get_base_url_from_env(cls, v: str) -> str:
        return os.environ.get("NOVEL_API_BASE_URL", v)

    @field_validator("model", mode="before")
    @classmethod
    def get_model_from_env(cls, v: str) -> str:
        return os.environ.get("NOVEL_MODEL", v)

    @field_validator("temperature", mode="before")
    @classmethod
    def get_temperature_from_env(cls, v: float) -> float:
        env_val = os.environ.get("NOVEL_TEMPERATURE")
        return float(env_val) if env_val else v

    @field_validator("max_tokens", mode="before")
    @classmethod
    def get_max_tokens_from_env(cls, v: int) -> int:
        env_val = os.environ.get("NOVEL_MAX_TOKENS")
        return int(env_val) if env_val else v


class ProjectConfig(BaseModel):
    default_style: str = Field(default="wuxia", description="默认写作风格")
    auto_save: bool = Field(default=True, description="自动保存")
    min_word_count: int = Field(default=2200, ge=1000, description="最小字数")
    max_word_count: int = Field(default=2500, le=5000, description="最大字数")
    enable_logging: bool = Field(default=True, description="启用日志")

    @field_validator("default_style", mode="before")
    @classmethod
    def get_style_from_env(cls, v: str) -> str:
        return os.environ.get("NOVEL_DEFAULT_STYLE", v)

    @field_validator("auto_save", mode="before")
    @classmethod
    def get_auto_save_from_env(cls, v: bool) -> bool:
        env_val = os.environ.get("NOVEL_AUTO_SAVE", "true")
        return env_val.lower() == "true"


class NovelWriterConfig(BaseModel):
    api: APIConfig = Field(default_factory=APIConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)

    @classmethod
    def from_env(cls) -> "NovelWriterConfig":
        """从环境变量加载配置"""
        return cls(
            api=APIConfig(),
            project=ProjectConfig()
        )

    def validate_api_key(self) -> bool:
        """验证 API 密钥是否配置"""
        return bool(self.api.api_key)


class Character(BaseModel):
    name: str
    profile: str
    status: str = "active"
    first_appear: int = 1


class OutlineNode(BaseModel):
    chapter: int
    title: str
    summary: str
    status: str = "planned"
    word_count: int = 0
    hooks: List[str] = Field(default_factory=list)


class ChapterData(BaseModel):
    chapter: int
    title: str
    content: str
    summary: str
    word_count: int
    timestamp: str
    status: str = "completed"


class NovelContext(BaseModel):
    novel_title: str
    characters: dict[str, str] = Field(default_factory=dict)
    world: str = ""
    outline: List[OutlineNode] = Field(default_factory=list)
    chapters: List[ChapterData] = Field(default_factory=list)
    style: str = "wuxia"
    word_count_total: int = 0
    created_at: str = ""
    updated_at: str = ""