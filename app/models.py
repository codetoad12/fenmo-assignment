from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field


class ExpenseIn(BaseModel):
    amount: Annotated[float, Field(gt=0)]
    category: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    date: date


class ExpenseOut(BaseModel):
    id: str
    amount: float
    category: str
    description: str
    date: date
    created_at: datetime
