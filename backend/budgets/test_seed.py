import json
from pathlib import Path

import pytest
from django.core.management import call_command

from budgets.models import LineItem, Scenario

FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "fy2026_operating_budget.json"
)


def _fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _row_tuple(item):
    return (
        item.department,
        item.category,
        item.month,
        item.budget_amount,
        item.actual_amount,
        item.notes,
        json.dumps(item.metadata, sort_keys=True),
    )


@pytest.mark.django_db
def test_seed_command_loads_snapshot():
    fixture = _fixture()
    call_command("seed")
    scenario = Scenario.objects.get(name=fixture["scenario"]["name"])
    assert scenario.line_items.count() == len(fixture["line_items"])

    count = LineItem.objects.count()
    call_command("seed")
    assert LineItem.objects.count() == count

    first = sorted(_row_tuple(item) for item in LineItem.objects.all())
    call_command("seed", "--reset")
    second = sorted(_row_tuple(item) for item in LineItem.objects.all())
    assert second == first

    items = list(LineItem.objects.all())
    assert any(item.metadata for item in items)
    assert any(item.actual_amount is None for item in items)
