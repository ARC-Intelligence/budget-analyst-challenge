import random
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from budgets.models import LineItem, Scenario

SCENARIO_NAME = "FY2026 Operating Budget"
SCENARIO_DESCRIPTION = (
    "Departmental operating budget for fiscal year 2026, with monthly "
    "budgeted and actual amounts."
)
RNG_SEED = 20260101
TWOPLACES = Decimal("0.01")

DEPARTMENTS = [
    "Engineering",
    "Sales",
    "Marketing",
    "Customer Success",
    "Finance",
    "People",
    "Operations",
    "Legal",
]

CATEGORIES = [
    "Salaries",
    "Contractors",
    "Software & Tools",
    "Travel",
    "Events",
    "Paid Ads",
    "Training",
    "Recruiting",
    "Office",
    "Equipment",
    "Cloud Infrastructure",
    "Professional Services",
    "Entertainment",
    "Misc",
]

GUARANTEED = {
    "Marketing": ["Paid Ads", "Events"],
    "Sales": ["Travel"],
    "Engineering": ["Cloud Infrastructure"],
    "Legal": ["Entertainment"],
    "Operations": ["Equipment"],
    "People": ["Recruiting"],
}

EXCLUSIVE_TO = {
    "Paid Ads": "Marketing",
    "Cloud Infrastructure": "Engineering",
}

CATEGORY_RANGES = {
    "Salaries": (120_000, 220_000),
    "Contractors": (20_000, 80_000),
    "Software & Tools": (8_000, 40_000),
    "Travel": (95_000, 125_000),
    "Events": (5_000, 20_000),
    "Paid Ads": (65_000, 90_000),
    "Training": (5_000, 25_000),
    "Recruiting": (8_000, 30_000),
    "Office": (5_000, 20_000),
    "Equipment": (5_000, 25_000),
    "Cloud Infrastructure": (60_000, 85_000),
    "Professional Services": (8_000, 40_000),
    "Entertainment": (3_000, 15_000),
    "Misc": (3_000, 12_000),
}

MONTHS = [date(2026, month, 1) for month in range(1, 13)]
BOOKED_THROUGH = date(2026, 8, 1)

OUTLIERS = {
    ("Marketing", "Events", date(2026, 6, 1)): (
        Decimal("2.5"),
        "Annual customer conference",
    ),
    ("Operations", "Equipment", date(2026, 4, 1)): (
        Decimal("1.8"),
        "Office buildout — new floor",
    ),
    ("People", "Recruiting", date(2026, 2, 1)): (
        Decimal("1.6"),
        "Executive search fees",
    ),
}


def money(value):
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def round_to(value, nearest):
    return int(round(value / nearest) * nearest)


def pick_categories(rng, department):
    guaranteed = list(GUARANTEED.get(department, []))
    pool = [
        category
        for category in CATEGORIES
        if category not in guaranteed
        and EXCLUSIVE_TO.get(category) in (None, department)
    ]
    target = min(rng.randint(12, 14), len(guaranteed) + len(pool))
    extra = rng.sample(pool, target - len(guaranteed))
    return sorted(guaranteed + extra)


def pair_variances(items):
    totals = defaultdict(lambda: [Decimal("0.00"), Decimal("0.00")])
    for item in items:
        if item.actual_amount is None:
            continue
        key = (item.department, item.category)
        totals[key][0] += item.budget_amount
        totals[key][1] += item.actual_amount
    return {key: actual - budget for key, (budget, actual) in totals.items()}


def verify_stories(items):
    variances = pair_variances(items)
    paid_key = ("Marketing", "Paid Ads")
    travel_key = ("Sales", "Travel")
    cloud_key = ("Engineering", "Cloud Infrastructure")
    by_abs = sorted(variances, key=lambda key: abs(variances[key]), reverse=True)
    overspends = sorted(
        (key for key in variances if variances[key] > 0),
        key=lambda key: variances[key],
        reverse=True,
    )
    if by_abs[0] != paid_key:
        raise CommandError(
            f"Marketing/Paid Ads should be the largest |variance|, got {by_abs[0]}"
        )
    if len(overspends) < 2 or overspends[1] != travel_key:
        raise CommandError(
            f"Sales/Travel should be the second-largest overspend, got {overspends[:3]}"
        )
    if variances[cloud_key] >= 0 or cloud_key not in by_abs[:3]:
        raise CommandError(
            "Engineering/Cloud Infrastructure should be a top-3 underspend"
        )


class Command(BaseCommand):
    help = "Load a deterministic FY2026 operating budget scenario."

    def add_arguments(self, parser):
        parser.add_argument(
            "--answer-key",
            action="store_true",
            help="Print a reviewer answer key to stdout after seeding.",
        )

    def handle(self, *args, **options):
        scenario = self.seed()
        self.stdout.write(f"{scenario.name}: {scenario.line_items.count()} line items")
        if options["answer_key"]:
            self.print_answer_key(scenario)

    def seed(self):
        Scenario.objects.filter(name=SCENARIO_NAME).delete()
        scenario = Scenario.objects.create(
            name=SCENARIO_NAME,
            description=SCENARIO_DESCRIPTION,
        )
        rng = random.Random(RNG_SEED)
        items = []

        for department in DEPARTMENTS:
            for category in pick_categories(rng, department):
                if department == "Legal" and category == "Entertainment":
                    baseline = 0
                else:
                    low, high = CATEGORY_RANGES[category]
                    baseline = round_to(rng.uniform(low, high), 500)

                for month in MONTHS:
                    if baseline == 0:
                        budget = Decimal("0.00")
                    else:
                        budget = Decimal(
                            round_to(baseline * (1 + rng.uniform(-0.03, 0.03)), 100)
                        )

                    actual = None
                    if month <= BOOKED_THROUGH:
                        # actuals booked through August
                        actual = money(float(budget) * rng.uniform(0.90, 1.10))
                        if budget == 0:
                            actual = money(rng.uniform(300, 900))

                    items.append(
                        LineItem(
                            scenario=scenario,
                            department=department,
                            category=category,
                            month=month,
                            budget_amount=budget,
                            actual_amount=actual,
                            notes="",
                        )
                    )

        for item in items:
            if item.actual_amount is None:
                continue
            month_index = item.month.month - 1
            if item.department == "Marketing" and item.category == "Paid Ads":
                if item.month.month >= 3:
                    item.actual_amount = money(
                        float(item.budget_amount) * rng.uniform(1.28, 1.34)
                    )
            elif item.department == "Sales" and item.category == "Travel":
                factor = 1 + 0.02 + (month_index / 7) * 0.13
                item.actual_amount = money(float(item.budget_amount) * factor)
            elif (
                item.department == "Engineering"
                and item.category == "Cloud Infrastructure"
            ):
                item.actual_amount = money(
                    float(item.budget_amount) * rng.uniform(0.72, 0.78)
                )

            outlier = OUTLIERS.get((item.department, item.category, item.month))
            if outlier:
                factor, note = outlier
                item.actual_amount = money(item.budget_amount * factor)
                item.notes = note

        verify_stories(items)
        LineItem.objects.bulk_create(items)
        return scenario

    def print_answer_key(self, scenario):
        booked = scenario.line_items.filter(
            month__lte=BOOKED_THROUGH, actual_amount__isnull=False
        )
        self.stdout.write("REVIEWER ANSWER KEY — do not distribute")
        self.stdout.write("")
        self.stdout.write("(a) Budget vs actual by department (Jan–Aug)")
        self.stdout.write(
            f"{'Department':<22}{'Budget':>16}{'Actual':>16}{'Variance':>16}{'Var %':>10}"
        )

        dept_rows = list(
            booked.values("department")
            .annotate(budget=Sum("budget_amount"), actual=Sum("actual_amount"))
            .order_by("department")
        )
        dept_rows.sort(
            key=lambda row: row["actual"] - row["budget"], reverse=True
        )
        for row in dept_rows:
            variance = row["actual"] - row["budget"]
            pct = (
                f"{float(variance / row['budget'] * 100):.2f}%"
                if row["budget"]
                else "n/a"
            )
            self.stdout.write(
                f"{row['department']:<22}{row['budget']:>16,.2f}"
                f"{row['actual']:>16,.2f}{variance:>16,.2f}{pct:>10}"
            )

        self.stdout.write("")
        self.stdout.write("(b) Top 10 |variance| by department + category")
        self.stdout.write(
            f"{'Department':<22}{'Category':<24}{'Budget':>14}{'Variance':>16}{'|Var|':>16}"
        )
        pair_rows = list(
            booked.values("department", "category")
            .annotate(budget=Sum("budget_amount"), actual=Sum("actual_amount"))
        )
        pair_rows.sort(
            key=lambda row: abs(row["actual"] - row["budget"]), reverse=True
        )
        for row in pair_rows[:10]:
            variance = row["actual"] - row["budget"]
            self.stdout.write(
                f"{row['department']:<22}{row['category']:<24}"
                f"{row['budget']:>14,.2f}{variance:>16,.2f}{abs(variance):>16,.2f}"
            )
        self.stdout.write("")
        self.stdout.write("Zero-budget pairs with booked actuals")
        for row in pair_rows:
            if row["budget"] == 0:
                variance = row["actual"] - row["budget"]
                self.stdout.write(
                    f"{row['department']:<22}{row['category']:<24}"
                    f"{row['budget']:>14,.2f}{variance:>16,.2f}{abs(variance):>16,.2f}"
                )

        self.stdout.write("")
        self.stdout.write("(c) Outlier rows with notes")
        for item in scenario.line_items.exclude(notes=""):
            self.stdout.write(
                f"{item.department} / {item.category} / {item.month:%Y-%m}  "
                f"budget={item.budget_amount:,.2f}  "
                f"actual={item.actual_amount:,.2f}  "
                f"notes={item.notes}"
            )
