from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ExpenseBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0, description="Amount spent, must be positive")
    category: str = Field(min_length=1, max_length=50)
    spent_on: date = Field(default_factory=date.today)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    spent_on: Optional[date] = None


class ExpenseOut(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int
