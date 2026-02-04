"""Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    name: str
    series_name: Optional[str] = None
    book_title: Optional[str] = None
    subtitle: Optional[str] = None
    author_voice_preset: str = "default"
    target_audience: Optional[str] = None
    stance: Optional[str] = None
    taboo_list: List[str] = Field(default_factory=list)
    draft_target_words: int = 25000
    final_target_words: int = 30000
    rrp_usd: float = 9.99
    expected_units: int = 500
    max_cost_usd: float = 15.0


class TopicSummary(BaseModel):
    id: int
    slug: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TopicDetail(TopicSummary):
    series_name: Optional[str] = None
    book_title: Optional[str] = None
    subtitle: Optional[str] = None
    author_voice_preset: str
    target_audience: Optional[str] = None
    stance: Optional[str] = None
    taboo_list: List[str]
    draft_target_words: int
    final_target_words: int
    rrp_usd: float
    expected_units: int
    max_cost_usd: float


class SiloSummary(BaseModel):
    id: int
    silo_number: int
    name_template: str
    custom_title: Optional[str] = None
    status: str
    draft_word_count: int
    final_word_count: int

    class Config:
        from_attributes = True


class TrendCandidateOut(BaseModel):
    id: int
    source: str
    topic_name: str
    description: Optional[str] = None
    trend_score: Optional[float] = None
    discovered_at: datetime
    status: str

    class Config:
        from_attributes = True


class ReviewPack(BaseModel):
    summary: str
    prompt_questions: List[str]
    word_count: int
    source_count: int


class SourceCreate(BaseModel):
    urls: List[str]
    source: str = "manual"


class SourceOut(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    domain: Optional[str] = None
    doc_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorNoteCreate(BaseModel):
    text: str
    source: str = "telegram"


class AuthorNoteOut(BaseModel):
    id: int
    text: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class WriteResponse(BaseModel):
    message: str
    final_path: Optional[str] = None


class RewriteResponse(BaseModel):
    message: str
    final_path: Optional[str] = None


class CompileResponse(BaseModel):
    message: str
    manuscript_path: str
    manifest_path: str


class ApplyImagesRequest(BaseModel):
    replacements: dict[str, str]


class ApplyImagesResponse(BaseModel):
    message: str
    manuscript_path: str


class SiloSettingOut(BaseModel):
    id: int
    silo_number: int
    target_words: int
    min_sources: int
    min_nuggets: int
    template_json: dict

    class Config:
        from_attributes = True


class SiloSettingUpdate(BaseModel):
    target_words: int | None = None
    min_sources: int | None = None
    min_nuggets: int | None = None
    template_json: dict | None = None


class AutopilotRequest(BaseModel):
    max_cycles: int = 6
    cooldown_seconds: int = 30
    stop_wordcount: int | None = None
    stop_on_no_new: bool = True


class AutopilotResponse(BaseModel):
    message: str
    log_path: str
