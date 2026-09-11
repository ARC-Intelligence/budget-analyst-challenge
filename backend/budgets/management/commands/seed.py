import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from budgets.models import LineItem, Scenario

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "fixtures" / "fy2026_operating_budget.json"
)


class Command(BaseCommand):
    help = "Load the FY2026 operating budget scenario from the bundled snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing scenario and reload it.",
        )

    def handle(self, *args, **options):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        name = payload["scenario"]["name"]
        scenario = Scenario.objects.filter(name=name).first()
        if options["reset"] or scenario is None or not scenario.line_items.exists():
            scenario = self.seed(payload)
            self.stdout.write(
                f"{scenario.name}: {scenario.line_items.count()} line items"
            )
        else:
            self.stdout.write(
                f"{scenario.name} already seeded "
                f"({scenario.line_items.count()} line items); use --reset to regenerate"
            )

    def seed(self, payload):
        name = payload["scenario"]["name"]
        Scenario.objects.filter(name=name).delete()
        scenario = Scenario.objects.create(
            name=name,
            description=payload["scenario"]["description"],
        )
        LineItem.objects.bulk_create(
            [
                LineItem(
                    scenario=scenario,
                    department=row["department"],
                    category=row["category"],
                    month=date.fromisoformat(row["month"]),
                    budget_amount=Decimal(row["budget_amount"]),
                    actual_amount=(
                        None
                        if row["actual_amount"] is None
                        else Decimal(row["actual_amount"])
                    ),
                    notes=row["notes"],
                    metadata=row["metadata"],
                )
                for row in payload["line_items"]
            ]
        )
        return scenario
