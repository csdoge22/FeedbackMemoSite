from pydantic import BaseModel, ConfigDict
import uuid

class FeedbackBase(BaseModel):
    title: str
    content: str

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackRead(FeedbackBase):
    id: uuid.UUID

    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)
