"""
expense_manager.py
Manages the in-memory collection of Expense objects.
Provides add, remove, search, and filter operations.
"""

from datetime import datetime
from typing import List, Optional

from finance_tracker.expense import Expense, ValidationError, VALID_CATEGORIES


class ExpenseManager:
    """
    Central store for all Expense objects.
    Maintains a running ID counter so each expense gets a unique ID.
    """

    def __init__(self):
        self._expenses: List[Expense] = []
        self._next_id: int = 1
        self.budgets: dict = {}          # category -> monthly budget amount

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #

    def add_expense(self, expense: Expense) -> Expense:
        """Assign an ID and store the expense. Returns the stored expense."""
        if expense.expense_id is None:
            expense.expense_id = self._next_id
            self._next_id += 1
        else:
            # Loading from file: keep track of highest ID seen
            self._next_id = max(self._next_id, expense.expense_id + 1)
        self._expenses.append(expense)
        return expense

    def remove_expense(self, expense_id: int) -> bool:
        """Remove an expense by ID. Returns True if found and removed."""
        for i, exp in enumerate(self._expenses):
            if exp.expense_id == expense_id:
                del self._expenses[i]
                return True
        return False

    def get_by_id(self, expense_id: int) -> Optional[Expense]:
        for exp in self._expenses:
            if exp.expense_id == expense_id:
                return exp
        return None

    def all_expenses(self) -> List[Expense]:
        return sorted(self._expenses, key=lambda e: (e.date, e.expense_id))

    # ------------------------------------------------------------------ #
    # Search & filter
    # ------------------------------------------------------------------ #

    def search(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        month: Optional[str] = None,   # "YYYY-MM"
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ) -> List[Expense]:
        """Return expenses matching ALL supplied filters."""
        results = self._expenses

        if keyword:
            kw = keyword.lower()
            results = [
                e for e in results
                if kw in e.description.lower() or kw in e.category.lower()
            ]
        if category:
            results = [e for e in results if e.category.lower() == category.lower()]
        if month:
            results = [e for e in results if e.date.startswith(month)]
        if min_amount is not None:
            results = [e for e in results if e.amount >= min_amount]
        if max_amount is not None:
            results = [e for e in results if e.amount <= max_amount]

        return sorted(results, key=lambda e: (e.date, e.expense_id))

    def expenses_for_month(self, year: int, month: int) -> List[Expense]:
        prefix = f"{year:04d}-{month:02d}"
        return [e for e in self._expenses if e.date.startswith(prefix)]

    # ------------------------------------------------------------------ #
    # Statistics helpers
    # ------------------------------------------------------------------ #

    def total(self, expenses: Optional[List[Expense]] = None) -> float:
        target = expenses if expenses is not None else self._expenses
        return round(sum(e.amount for e in target), 2)

    def category_totals(self, expenses: Optional[List[Expense]] = None) -> dict:
        target = expenses if expenses is not None else self._expenses
        totals: dict = {}
        for exp in target:
            totals[exp.category] = round(totals.get(exp.category, 0) + exp.amount, 2)
        return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))

    def monthly_totals(self) -> dict:
        """Return {YYYY-MM: total} for all expenses, sorted."""
        totals: dict = {}
        for exp in self._expenses:
            key = exp.date[:7]
            totals[key] = round(totals.get(key, 0) + exp.amount, 2)
        return dict(sorted(totals.items()))

    # ------------------------------------------------------------------ #
    # Budget helpers
    # ------------------------------------------------------------------ #

    def set_budget(self, category: str, amount: float):
        if category not in VALID_CATEGORIES and category != "Total":
            raise ValidationError(f"Unknown category: {category}")
        if amount < 0:
            raise ValidationError("Budget must be non-negative.")
        self.budgets[category] = round(amount, 2)

    def budget_status(self, year: int, month: int) -> dict:
        """
        Returns a dict with budget vs spent for each budgeted category.
        {category: {"budget": X, "spent": Y, "remaining": Z}}
        """
        monthly_expenses = self.expenses_for_month(year, month)
        cat_totals = self.category_totals(monthly_expenses)
        status = {}
        for cat, budget in self.budgets.items():
            spent = cat_totals.get(cat, 0)
            status[cat] = {
                "budget": budget,
                "spent": spent,
                "remaining": round(budget - spent, 2),
            }
        return status

    # ------------------------------------------------------------------ #
    # Serialisation helpers
    # ------------------------------------------------------------------ #

    def load_from_list(self, data: List[dict]):
        """Populate manager from a list of expense dicts (from JSON)."""
        self._expenses.clear()
        self._next_id = 1
        for item in data:
            exp = Expense.from_dict(item)
            self.add_expense(exp)

    def to_list(self) -> List[dict]:
        return [e.to_dict() for e in self.all_expenses()]
