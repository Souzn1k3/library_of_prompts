import enum

from pydantic import BaseModel

from app.modules.catalog.model.prompt import PromptListItem


class RecommendationContext(str, enum.Enum):
    home = "home"
    dashboard = "dashboard"
    prompt_detail = "prompt_detail"
    after_save = "after_save"
    after_lesson_complete = "after_lesson_complete"


class RecommendationStrategy(str, enum.Enum):
    personalized = "personalized"
    contextual = "contextual"
    cold_start = "cold_start"


class PromptRecommendationResponse(BaseModel):
    context: RecommendationContext
    strategy: RecommendationStrategy
    items: list[PromptListItem]
