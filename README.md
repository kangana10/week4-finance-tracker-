# Personal Finance Tracker 💰
**Week 4 Final Project — Python Course**
*By Kangana Batghare*

---

## Project Description

A fully featured command-line Personal Finance Tracker that lets you log expenses, categorise spending, set monthly budgets, and generate detailed reports — all with persistent JSON storage and automatic backups.

---

## Features

| Feature | Detail |
|---|---|
| Add / Delete Expenses | Full validation on amount, category, description, and date |
| 9 Categories | Food, Transport, Entertainment, Bills, Healthcare, Shopping, Education, Travel, Other |
| JSON Persistence | Data auto-saved on every change; atomic writes prevent corruption |
| Backup & Restore | Timestamped backups; one-click restore |
| CSV Export / Import | Share or analyse data in spreadsheets |
| Monthly Reports | Category breakdown + itemised list + ASCII bar chart |
| Budget Tracking | Set per-category limits; real-time OK / WARNING / OVER BUDGET status |
| Statistics | Totals, averages, min/max, monthly trend chart |
| Search & Filter | By keyword, category, month, or amount range |
| Modular Code | 6 focused modules + full test suite (30 tests) |

---

## Project Structure

```
week4-finance-tracker/
├── finance_tracker/
│   ├── __init__.py
│   ├── main.py              # Menu loop & UI
│   ├── expense.py           # Expense model + validation
│   ├── expense_manager.py   # In-memory store (CRUD, search, stats)
│   ├── file_handler.py      # JSON, CSV, backup I/O
│   ├── reports.py           # ASCII reports & visualisations
│   └── utils.py             # Input helpers
├── data/
│   ├── expenses.json        # Persistent data store
│   ├── backup/              # Auto-generated backups
│   └── exports/             # CSV exports
├── tests/
│   ├── test_expense.py      # 23 expense model tests
│   ├── test_file_handler.py # 14 file I/O tests
│   └── test_reports.py      # 18 report tests
├── run.py                   # Entry point
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Setup & Installation

```bash
# 1. Clone / download the project
git clone https://github.com/kangana10/week4-finance-tracker.git
cd week4-finance-tracker

# 2. (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install test dependencies
pip install -r requirements.txt

# 4. Run the application
python run.py
```

### Requirements
- Python 3.8 or higher
- No third-party runtime dependencies (standard library only)
- `pytest >= 7.0` for the test suite

---

## How to Run

```bash
python run.py
```

You will see the main menu:

```
╔══════════════════════════════════════════════════════════╗
║         PERSONAL  FINANCE  TRACKER  v1.0                 ║
╚══════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────┐
│               MAIN  MENU                 │
├──────────────────────────────────────────┤
│  1. Add New Expense                       │
│  2. View All Expenses                     │
│  ...                                      │
│  0. Save & Exit                           │
└──────────────────────────────────────────┘
```

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output: **55 passed** across all three test files.

---

## Technical Details

### Architecture
The project follows a clean layered architecture:

```
UI Layer (main.py)
      ↓
Business Logic (expense_manager.py)
      ↓
Data Model (expense.py)
      ↓
File I/O (file_handler.py)
      ↓
Reports (reports.py)   ←  Utils (utils.py)
```

### Data Format (JSON)
```json
{
  "version": "1.0",
  "last_saved": "2024-06-15T10:30:00",
  "budgets": { "Food": 3000.0 },
  "expenses": [
    {
      "expense_id": 1,
      "date": "2024-06-01",
      "amount": 150.0,
      "category": "Food",
      "description": "Grocery shopping"
    }
  ]
}
```

### Key Design Decisions
- **Atomic JSON writes**: data is written to a `.tmp` file then renamed, so a crash mid-write never corrupts the store.
- **Separation of concerns**: validation lives in `Expense`, collection logic in `ExpenseManager`, I/O in `file_handler`, and presentation in `reports`.
- **No external dependencies**: the entire runtime uses Python's standard library (`json`, `csv`, `pathlib`, `shutil`, `datetime`).

---

## Concepts Demonstrated (Week 1–4)

| Week | Concept | Where Used |
|---|---|---|
| 1 | Variables, conditionals, loops | `main.py` menu loop |
| 2 | Functions, lists, dictionaries | `expense_manager.py` |
| 3 | OOP (classes, methods), file I/O, regex-style validation | `expense.py`, `file_handler.py` |
| 4 | JSON/CSV, context managers, error handling, modules, testing | All modules + `tests/` |
