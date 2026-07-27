from typing import Any, Dict, List

from pydantic import BaseModel, Field


class TextAnalysisRequest(BaseModel):
    model_config = {"extra": "forbid"}

    text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="The SMS text to analyze (1-10000 characters)",
    )


class InvestigationArtefact(BaseModel):
    model_config = {"extra": "forbid"}

    text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Artefact text content (1-10000 characters)",
    )
    type: str = Field(default="text", pattern=r"^[a-zA-Z_][a-zA-Z0-9_-]{0,31}$")


class InvestigationRequest(BaseModel):
    model_config = {"extra": "forbid"}

    artefacts: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of artefacts to investigate (1-20 items)",
    )
