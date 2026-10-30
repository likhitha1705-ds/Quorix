"""Configuration settings for Phase 6: Answer Generation & Citation Engine."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    """Runtime configuration for LLM invocation, cost tracking, and citations."""

    model_name: str = Field(default="gemini-2.0-flash", description="Gemini model name")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Sampling temperature")
    max_output_tokens: int = Field(default=1024, gt=0, description="Maximum token generation limit")
    cost_per_million_input_tokens: float = Field(default=0.10, ge=0.0, description="Cost per 1M prompt tokens in USD")
    cost_per_million_output_tokens: float = Field(default=0.40, ge=0.0, description="Cost per 1M completion tokens in USD")
    api_key: str | None = Field(default=None, description="Gemini API Key")

