from datetime import date
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API", version="1.0.0",
              description="A REST API for tracking expenses, built with FastAPI and SQLAlchemy.")


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@app.post("/expenses", response_model=schemas.ExpenseOut,
          status_code=status.HTTP_201_CREATED, tags=["expenses"])
def create_expense(payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    expense = models.Expense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.get("/expenses", response_model=List[schemas.ExpenseOut], tags=["expenses"])
def list_expenses(
    category: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(models.Expense)
    if category:
        query = query.filter(models.Expense.category == category)
    if start:
        query = query.filter(models.Expense.spent_on >= start)
    if end:
        query = query.filter(models.Expense.spent_on <= end)
    return query.order_by(models.Expense.spent_on.desc(), models.Expense.id.desc()).offset(skip).limit(limit).all()


@app.get("/expenses/summary", response_model=List[schemas.CategorySummary], tags=["analytics"])
def summary(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Expense.category,
                 func.sum(models.Expense.amount),
                 func.count(models.Expense.id))
        .group_by(models.Expense.category)
        .order_by(func.sum(models.Expense.amount).desc())
        .all()
    )
    return [schemas.CategorySummary(category=c, total=round(t, 2), count=n) for c, t, n in rows]


def _get_or_404(db: Session, expense_id: int) -> models.Expense:
    expense = db.get(models.Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.get("/expenses/{expense_id}", response_model=schemas.ExpenseOut, tags=["expenses"])
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, expense_id)


@app.put("/expenses/{expense_id}", response_model=schemas.ExpenseOut, tags=["expenses"])
def update_expense(expense_id: int, payload: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    expense = _get_or_404(db, expense_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenses"])
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = _get_or_404(db, expense_id)
    db.delete(expense)
    db.commit()
