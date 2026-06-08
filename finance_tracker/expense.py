"""
expense.py
Defines the Expense data model and its validation logic.
"""

from datetime import datetime
from typing import Optional


VALID_CATEGORIES = [
    "Food",
    "Transport",
    "Entertainment",
    "Bills",
    "Healthcare",
    "Shopping",
    "Education",
    "Travel",
    "Other",
]


class ValidationError(Exception):
    """Raised when expense data fails validation."""
    pass


class Expense:
    """
    Represents a single expense entry.

    Attributes:
        expense_id  : Unique integer ID
        date        : Date of the expense (YYYY-MM-DD string)
        amount      : Positive float amount in rupees
        category    : One of VALID_CATEGORIES
        description : Short description of the expense
    """

    def __init__(
        self,
        amount: float,
        category: str,
        description: str,
        date: Optional[str] = None,
        expense_id: Optional[int] = None,
    ):
        self.expense_id = expense_id
        self.date = date or datetime.today().strftime("%Y-%m-%d")
        self.amount = self._validate_amount(amount)
        self.category = self._validate_category(category)
        self.description = self._validate_description(description)

    # ------------------------------------------------------------------ #
    # Validation helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_amount(amount) -> float:
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValidationError("Amount must be a number.")
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        if amount > 10_000_000:
            raise ValidationError("Amount seems unrealistically large (> 1 crore).")
        return round(amount, 2)

    @staticmethod
    def _validate_category(category: str) -> str:
        category = str(category).strip().title()
        if category not in VALID_CATEGORIES:
            raise ValidationError(
                f"Invalid category '{category}'. "
                f"Choose from: {', '.join(VALID_CATEGORIES)}"
            )
        return category

    @staticmethod
    def _validate_description(description: str) -> str:
        description = str(description).strip()
        if not description:
            raise ValidationError("Description cannot be empty.")
        if len(description) > 200:
            raise ValidationError("Description must be 200 characters or fewer.")
        return description

    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate and return date string in YYYY-MM-DD format."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            raise ValidationError("Date must be in YYYY-MM-DD format.")

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "expense_id": self.expense_id,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        expense = cls(
            amount=data["amount"],
            category=data["category"],
            description=data["description"],
            date=data.get("date"),
            expense_id=data.get("expense_id"),
        )
        return expense

    # ------------------------------------------------------------------ #
    # Display
    # ------------------------------------------------------------------ #

    def __str__(self) -> str:
        return (
            f"[ID:{self.expense_id:>4}] {self.date}  "
            f"{self.category:<15} Rs{self.amount:>10,.2f}  "
            f"{self.description}"
        )

    def __repr__(self) -> str:
        return f"Expense(id={self.expense_id}, date={self.date}, amount={self.amount}, category={self.category})"
