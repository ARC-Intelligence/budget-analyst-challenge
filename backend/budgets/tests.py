from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from budgets.models import LineItem, Scenario


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def scenario():
    return Scenario.objects.create(name="Q1 Plan", description="Test scenario")


@pytest.fixture
def line_item(scenario):
    return LineItem.objects.create(
        scenario=scenario,
        department="Engineering",
        category="Salaries",
        month=date(2026, 1, 1),
        budget_amount=Decimal("10000.00"),
        actual_amount=Decimal("9500.00"),
    )


@pytest.mark.django_db
def test_scenario_list_and_create(api_client, scenario):
    response = api_client.get("/api/scenarios/")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["name"] == "Q1 Plan"
    assert payload[0]["line_item_count"] == 0

    response = api_client.post(
        "/api/scenarios/",
        {"name": "FY2026", "description": "Operating budget"},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["name"] == "FY2026"
    assert response.json()["line_item_count"] == 0


@pytest.mark.django_db
def test_scenario_detail(api_client, scenario, line_item):
    response = api_client.get(f"/api/scenarios/{scenario.id}/")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == scenario.id
    assert body["name"] == "Q1 Plan"
    assert body["line_item_count"] == 1


@pytest.mark.django_db
def test_line_item_create(api_client, scenario):
    response = api_client.post(
        "/api/line-items/",
        {
            "scenario": scenario.id,
            "department": "Sales",
            "category": "Travel",
            "month": "2026-03-01",
            "budget_amount": "8000.00",
            "actual_amount": "8200.50",
            "notes": "",
        },
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["department"] == "Sales"
    assert body["category"] == "Travel"
    assert body["budget_amount"] == "8000.00"
    assert body["metadata"] == {}
    assert LineItem.objects.filter(scenario=scenario).count() == 1


@pytest.mark.django_db
def test_line_item_patch(api_client, line_item):
    response = api_client.patch(
        f"/api/line-items/{line_item.id}/",
        {"actual_amount": "10100.00", "notes": "Correction"},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["actual_amount"] == "10100.00"
    assert body["notes"] == "Correction"
    line_item.refresh_from_db()
    assert line_item.actual_amount == Decimal("10100.00")


@pytest.mark.django_db
def test_line_item_patch_metadata(api_client, line_item):
    response = api_client.patch(
        f"/api/line-items/{line_item.id}/",
        {"metadata": {"vendor": "Acme", "tags": ["a"]}},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metadata"] == {"vendor": "Acme", "tags": ["a"]}
    line_item.refresh_from_db()
    assert line_item.metadata == {"vendor": "Acme", "tags": ["a"]}


@pytest.mark.django_db
def test_line_item_list_filtered_and_paginated(api_client, scenario):
    other = Scenario.objects.create(name="Other")
    for index in range(3):
        LineItem.objects.create(
            scenario=scenario,
            department="Finance",
            category="Office",
            month=date(2026, index + 1, 1),
            budget_amount=Decimal("1000.00"),
        )
    LineItem.objects.create(
        scenario=other,
        department="Legal",
        category="Misc",
        month=date(2026, 1, 1),
        budget_amount=Decimal("500.00"),
    )

    response = api_client.get(f"/api/line-items/?scenario={scenario.id}")
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"count", "next", "previous", "results"}
    assert body["count"] == 3
    assert len(body["results"]) == 3
    assert all(row["scenario"] == scenario.id for row in body["results"])
