"""
test_expense.py
Unit tests for the Expense model and its validation logic.
"""

import pytest
from finance_tracker.expense import Expense, ValidationError, VALID_CATEGORIES


# ────────────────────────────────────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────────────────────────────────────

def make_expense(**kwargs) -> Expense:
    defaults = dict(amount=100.0, category="Food", description="Lunch")
    defaults.update(kwargs)
    return Expense(**defaults)


# ────────────────────────────────────────────────────────────────────────────
# 1. Basic creation
# ────────────────────────────────────────────────────────────────────────────

class TestExpenseCreation:
    def test_valid_expense_created(self):
        exp = make_expense()
        assert exp.amount == 100.0
        assert exp.category == "Food"
        assert exp.description == "Lunch"

    def test_default_date_is_today(self):
        from datetime import datetime
        exp = make_expense()
        today = datetime.today().strftime("%Y-%m-%d")
        assert exp.date == today

    def test_custom_date_accepted(self):
        exp = make_expense(date="2024-03-15")
        assert exp.date == "2024-03-15"

    def test_expense_id_defaults_to_none(self):
        exp = make_expense()
        assert exp.expense_id is None

    def test_expense_id_can_be_set(self):
        exp = make_expense(expense_id=42)
        assert exp.expense_id == 42


# ────────────────────────────────────────────────────────────────────────────
# 2. Amount validation
# ────────────────────────────────────────────────────────────────────────────

class TestAmountValidation:
    def test_positive_int_accepted(self):
        exp = make_expense(amount=500)
        assert exp.amount == 500.0

    def test_float_rounded_to_two_places(self):
        exp = make_expense(amount=19.999)
        assert exp.amount == 20.0

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            make_expense(amount=0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            make_expense(amount=-50)

    def test_string_number_accepted(self):
        exp = make_expense(amount="250.5")
        assert exp.amount == 250.5

    def test_non_numeric_string_raises(self):
        with pytest.raises(ValidationError, match="must be a number"):
            make_expense(amount="abc")

    def test_none_raises(self):
        with pytest.raises(ValidationError):
            make_expense(amount=None)

    def test_very_large_amount_raises(self):
        with pytest.raises(ValidationError, match="unrealistically large"):
            make_expense(amount=10_000_001)


# ────────────────────────────────────────────────────────────────────────────
# 3. Category validation
# ────────────────────────────────────────────────────────────────────────────

class TestCategoryValidation:
    def test_all_valid_categories_accepted(self):
        for cat in VALID_CATEGORIES:
            exp = make_expense(category=cat)
            assert exp.category == cat

    def test_case_insensitive(self):
        exp = make_expense(category="food")
        assert exp.category == "Food"

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError, match="Invalid category"):
            make_expense(category="Gambling")

    def test_empty_category_raises(self):
        with pytest.raises(ValidationError):
            make_expense(category="")


# ────────────────────────────────────────────────────────────────────────────
# 4. Description validation
# ────────────────────────────────────────────────────────────────────────────

class TestDescriptionValidation:
    def test_normal_description_accepted(self):
        exp = make_expense(description="Dinner at restaurant")
        assert exp.description == "Dinner at restaurant"

    def test_whitespace_stripped(self):
        exp = make_expense(description="  Coffee  ")
        assert exp.description == "Coffee"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            make_expense(description="")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            make_expense(description="   ")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError, match="200 characters"):
            make_expense(description="x" * 201)

    def test_exactly_200_chars_accepted(self):
        exp = make_expense(description="x" * 200)
        assert len(exp.description) == 200


# ────────────────────────────────────────────────────────────────────────────
# 5. Date validation
# ────────────────────────────────────────────────────────────────────────────

class TestDateValidation:
    def test_valid_date_string(self):
        assert Expense.validate_date("2024-06-15") == "2024-06-15"

    def test_wrong_format_raises(self):
        with pytest.raises(ValidationError, match="YYYY-MM-DD"):
            Expense.validate_date("15-06-2024")

    def test_invalid_date_raises(self):
        with pytest.raises(ValidationError):
            Expense.validate_date("2024-13-01")   # month 13


# ────────────────────────────────────────────────────────────────────────────
# 6. Serialisation round-trip
# ────────────────────────────────────────────────────────────────────────────

class TestSerialisation:
    def test_to_dict_has_required_keys(self):
        exp = make_expense(expense_id=1)
        d = exp.to_dict()
        assert set(d.keys()) == {"expense_id", "date", "amount", "category", "description"}

    def test_from_dict_roundtrip(self):
        exp = make_expense(expense_id=7, amount=350.0, category="Transport",
                           description="Auto", date="2024-05-10")
        d = exp.to_dict()
        exp2 = Expense.from_dict(d)
        assert exp2.expense_id == 7
        assert exp2.amount == 350.0
        assert exp2.category == "Transport"
        assert exp2.description == "Auto"
        assert exp2.date == "2024-05-10"

    def test_str_representation(self):
        exp = make_expense(expense_id=1, amount=250, category="Food", description="Pizza")
        s = str(exp)
        assert "Food" in s
        assert "Pizza" in s
        assert "250" in s

