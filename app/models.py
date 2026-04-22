from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class ExpenseIn(BaseModel):
    amount: Annotated[
        Decimal,
        Field(gt=0, max_digits=12, decimal_places=2),
    ]
    category: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    date: date

    @field_validator('category', 'description')
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('Field cannot be blank')
        return stripped

    @field_validator('date')
    @classmethod
    def reject_future_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError('Expense date cannot be in the future')
        return value


class ExpenseOut(BaseModel):
    id: str
    amount: Decimal
    category: str
    description: str
    date: date
    created_at: datetime
