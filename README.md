# Expense Tracker API

A REST API for tracking personal expenses, built with **FastAPI**, **SQLAlchemy** (SQLite) and **Pydantic**.
Interactive Swagger docs are generated automatically at `/docs`.

## Features
- Full CRUD for expenses (`POST/GET/PUT/DELETE /expenses`)
- Filtering by category and date range, with pagination (`skip`, `limit`)
- Category-wise spending summary using SQL aggregation (`GET /expenses/summary`)
- Request validation with Pydantic (e.g. amount must be positive) and proper HTTP status codes (201, 204, 404, 422)
- Automated tests with pytest

## Run locally
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

## Run tests
```bash
pytest -v
```

## Example
```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title":"Lunch","amount":120.5,"category":"Food"}'
```
