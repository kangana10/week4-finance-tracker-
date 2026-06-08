"""
test_reports.py
Tests for report generation functions.
"""

import pytest
from finance_tracker.expense import Expense
from finance_tracker import reports


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

def _make(amount, category, description, date="2024-06-10", eid=1):
    exp = Expense(amount=amount, category=category, description=description, date=date)
    exp.expense_id = eid
    return exp


@pytest.fixture
def sample_expenses():
    return [
        _make(500,  "Food",          "Groceries",      date="2024-06-01", eid=1),
        _make(200,  "Transport",     "Bus pass",        date="2024-06-03", eid=2),
        _make(1500, "Entertainment", "Concert ticket",  date="2024-06-10", eid=3),
        _make(800,  "Bills",         "Electricity",     date="2024-06-15", eid=4),
        _make(300,  "Food",          "Restaurant",      date="2024-06-20", eid=5),
    ]


# ────────────────────────────────────────────────────────────────────────────
# 1. Monthly report
# ────────────────────────────────────────────────────────────────────────────

class TestMonthlyReport:
    def test_returns_string(self, sample_expenses):
        result = reports.monthly_report(sample_expenses, 2024, 6)
        assert isinstance(result, str)

    def test_contains_month_name(self, sample_expenses):
        result = reports.monthly_report(sample_expenses, 2024, 6)
        assert "June 2024" in result

    def test_contains_total(self, sample_expenses):
        result = reports.monthly_report(sample_expenses, 2024, 6)
        # Total is 500+200+1500+800+300 = 3300
        assert "3,300" in result

    def test_contains_all_categories(self, sample_expenses):
        result = reports.monthly_report(sample_expenses, 2024, 6)
        for cat in ["Food", "Transport", "Entertainment", "Bills"]:
            assert cat in result

    def test_empty_expenses_handled(self):
        result = reports.monthly_report([], 2024, 6)
        assert "No expenses" in result

    def test_contains_descriptions(self, sample_expenses):
        result = reports.monthly_report(sample_expenses, 2024, 6)
        assert "Groceries" in result


# ────────────────────────────────────────────────────────────────────────────
# 2. Category breakdown
# ────────────────────────────────────────────────────────────────────────────

class TestCategoryBreakdown:
    def test_returns_string(self, sample_expenses):
        result = reports.category_breakdown(sample_expenses)
        assert isinstance(result, str)

    def test_shows_all_present_categories(self, sample_expenses):
        result = reports.category_breakdown(sample_expenses)
        for cat in ["Food", "Transport", "Entertainment", "Bills"]:
            assert cat in result

    def test_does_not_show_empty_categories(self, sample_expenses):
        result = reports.category_breakdown(sample_expenses)
        # Healthcare has no expenses
        assert "Healthcare" not in result

    def test_empty_expenses_handled(self):
        result = reports.category_breakdown([])
        assert "No expenses" in result

    def test_shows_total(self, sample_expenses):
        result = reports.category_breakdown(sample_expenses)
        assert "3,300" in result


# ────────────────────────────────────────────────────────────────────────────
# 3. Statistics report
# ────────────────────────────────────────────────────────────────────────────

class TestStatisticsReport:
    def test_returns_string(self, sample_expenses):
        result = reports.statistics_report(sample_expenses)
        assert isinstance(result, str)

    def test_shows_count(self, sample_expenses):
        result = reports.statistics_report(sample_expenses)
        assert "5" in result   # 5 expenses

    def test_shows_total(self, sample_expenses):
        result = reports.statistics_report(sample_expenses)
        assert "3,300" in result

    def test_empty_expenses_handled(self):
        result = reports.statistics_report([])
        assert "No expenses" in result

    def test_shows_max_expense(self, sample_expenses):
        result = reports.statistics_report(sample_expenses)
        # Largest is 1500 Concert ticket
        assert "1,500" in result


# ────────────────────────────────────────────────────────────────────────────
# 4. Budget report
# ────────────────────────────────────────────────────────────────────────────

class TestBudgetReport:
    def test_returns_string(self):
        status = {
            "Food": {"budget": 3000, "spent": 800, "remaining": 2200},
            "Transport": {"budget": 500, "spent": 200, "remaining": 300},
        }
        result = reports.budget_report(status)
        assert isinstance(result, str)

    def test_shows_ok_status(self):
        status = {"Food": {"budget": 3000, "spent": 500, "remaining": 2500}}
        result = reports.budget_report(status)
        assert "OK" in result

    def test_shows_over_budget(self):
        status = {"Food": {"budget": 500, "spent": 800, "remaining": -300}}
        result = reports.budget_report(status)
        assert "OVER BUDGET" in result

    def test_shows_warning_near_limit(self):
        status = {"Food": {"budget": 1000, "spent": 950, "remaining": 50}}
        result = reports.budget_report(status)
        assert "WARNING" in result

    def test_empty_status_handled(self):
        result = reports.budget_report({})
        assert "No budgets" in result

    def test_shows_category_names(self):
        status = {
            "Bills": {"budget": 2000, "spent": 1800, "remaining": 200},
        }
        result = reports.budget_report(status)
        assert "Bills" in result
