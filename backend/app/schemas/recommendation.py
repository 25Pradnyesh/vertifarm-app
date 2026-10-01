from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class RecommendationItem(SchemaBase):
    id: str
    category: Literal['irrigation', 'ph', 'nutrition', 'environment', 'disease']
    title: str
    description: str
    priority: Literal['high', 'medium', 'low']
    tab: Literal['forYou', 'general']
    actionableLink: Optional[str] = None
