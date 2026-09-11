import random
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand, CommandError

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
    "Marketing": ["Paid Ads", "Events", "Software & Tools"],
    "Sales": ["Travel", "Software & Tools"],
    "Engineering": ["Cloud Infrastructure"],
    "Legal": ["Entertainment"],
    "Operations": ["Equipment"],
    "People": ["Recruiting"],
    "Finance": ["Professional Services"],
    "Customer Success": ["Software & Tools"],
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
AUGUST = date(2026, 8, 1)
SEPTEMBER = date(2026, 9, 1)
BOOKED_THROUGH = {
    "Finance": SEPTEMBER,
    "Legal": SEPTEMBER,
    "People": SEPTEMBER,
    "Engineering": AUGUST,
    "Sales": AUGUST,
    "Marketing": AUGUST,
    "Customer Success": AUGUST,
    "Operations": AUGUST,
}

OUTLIERS = {
    ("Marketing", "Events", date(2026, 6, 1)): (
        Decimal("1.95"),
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

ENGINEERING_TEAMS = ["platform", "data", "web", "mobile"]
ENGINEERING_SERVICES = [
    "api-gateway",
    "billing",
    "search",
    "auth",
    "ci",
    "metrics",
    "cdn",
    "queue",
]
SALES_INITIALS = ["AJ", "BK", "CL", "DM", "EN", "FO", "GP", "HK", "JL"]
SALES_REGIONS = ["EMEA", "NA", "APAC"]
MARKETING_CAMPAIGNS = [
    "spring-launch",
    "brand-refresh",
    "webinar-series",
    "product-hunt",
    "retention",
]
MARKETING_CHANNELS = ["paid", "organic", "events"]
CS_TIERS = ["enterprise", "mid"]
CS_TAGS = ["onboarding", "renewal", "expansion", "health", "training"]
FINANCE_VENDORS = ["Acme", "Contoso", "Globex", "Initech", "Umbrella", "Soylent"]
PEOPLE_PROGRAMS = ["onboarding", "l&d", "wellness", "offsite", "mentorship"]
OPS_SITES = ["HQ", "Berlin"]
NOTE_SNIPPETS = ["follow up", "ok", "reviewed", "pending", "see slack"]

STRICT_OVER = {"Marketing", "Sales", "Operations"}
ROW_OVER = {"Marketing", "Sales", "Operations", "Finance"}
SEPTEMBER_DEPARTMENTS = {"Finance", "Legal", "People"}


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


def pair_variances(items, months=None):
    totals = defaultdict(lambda: [Decimal("0.00"), Decimal("0.00")])
    for item in items:
        if item.actual_amount is None:
            continue
        if months is not None and item.month not in months:
            continue
        key = (item.department, item.category)
        totals[key][0] += item.budget_amount
        totals[key][1] += item.actual_amount
    return {key: actual - budget for key, (budget, actual) in totals.items()}


def fully_booked_months(items):
    by_month = defaultdict(list)
    for item in items:
        by_month[item.month].append(item.actual_amount is not None)
    return {
        month
        for month, flags in by_month.items()
        if flags and all(flags)
    }


def department_variance(items, department, months=None):
    budget = Decimal("0.00")
    actual = Decimal("0.00")
    for item in items:
        if item.department != department or item.actual_amount is None:
            continue
        if months is not None and item.month not in months:
            continue
        budget += item.budget_amount
        actual += item.actual_amount
    return actual - budget


def over_budget_departments(items, months=None):
    totals = defaultdict(lambda: Decimal("0.00"))
    for item in items:
        if item.actual_amount is None:
            continue
        if months is not None and item.month not in months:
            continue
        totals[item.department] += item.actual_amount - item.budget_amount
    return {department for department, variance in totals.items() if variance > 0}


def category_uplift(items, department, category, months):
    budget = Decimal("0.00")
    actual = Decimal("0.00")
    for item in items:
        if item.department != department or item.category != category:
            continue
        if item.month.month not in months or item.actual_amount is None:
            continue
        budget += item.budget_amount
        actual += item.actual_amount
    if budget == 0:
        return Decimal("0.00")
    return actual / budget - 1


def planted_signal(item):
    department, category, month = item.department, item.category, item.month.month
    if department == "Marketing" and category == "Paid Ads" and 3 <= month <= 8:
        return {
            "campaign": "Q2 brand push",
            "approved_by": "CMO",
            "approved_uplift_pct": 20,
            "ref": "MKT-114",
        }
    if department == "Marketing" and category == "Events" and month in (5, 6):
        return {"one_off": True, "comment": "Conference moved from May to June"}
    if (
        department == "Engineering"
        and category == "Cloud Infrastructure"
        and 6 <= month <= 8
    ):
        return {
            "comment": (
                "Vendor invoices for Q3 delayed; expect catch-up in Sep-Oct"
            ),
            "owner": "platform",
        }
    if (
        department == "Finance"
        and category == "Professional Services"
        and month == 3
    ):
        return {"comment": "Overspend approved by CFO"}
    if (
        department == "Finance"
        and category == "Professional Services"
        and month == 9
    ):
        return {"comment": "Annual audit fees", "vendor": "KPMG"}
    if category == "Software & Tools":
        if department == "Sales":
            return {"vendor": "Salesforce", "seats": 40}
        if department == "Customer Success":
            return {"supplier": "salesforce.com", "plan": "enterprise"}
        if department == "Marketing":
            return {"vendor_name": "SFDC", "tags": ["crm"]}
    if department == "People" and category == "Recruiting" and month == 2:
        return {
            "status": "placement pending",
            "comment": "Executive search; 40k refundable if placement fails",
        }
    return None


def _vary_filler(meta, rng):
    meta = dict(meta)
    if len(meta) > 1 and rng.random() < 0.25:
        omit = rng.choice(list(meta.keys()))
        meta.pop(omit)
    if rng.random() < 0.20:
        meta["note"] = rng.choice(NOTE_SNIPPETS)
    return meta


def filler_metadata(department, rng):
    if department == "Engineering":
        meta = {
            "owner": rng.choice(ENGINEERING_TEAMS),
            "service": rng.choice(ENGINEERING_SERVICES),
        }
    elif department == "Sales":
        meta = {
            "rep": rng.choice(SALES_INITIALS),
            "region": rng.choice(SALES_REGIONS),
        }
    elif department == "Marketing":
        meta = {
            "campaign": rng.choice(MARKETING_CAMPAIGNS),
            "channel": rng.choice(MARKETING_CHANNELS),
        }
    elif department == "Customer Success":
        tag_count = 1 if rng.random() < 0.6 else 2
        meta = {
            "account_tier": rng.choice(CS_TIERS),
            "tags": rng.sample(CS_TAGS, tag_count),
        }
    elif department == "Finance":
        meta = {
            "vendor": rng.choice(FINANCE_VENDORS),
            "invoice_ref": f"INV-{rng.randint(1000, 9999):04d}",
        }
    elif department == "People":
        if rng.random() < 0.5:
            meta = {"requisition": f"REQ-{rng.randint(100, 999):03d}"}
        else:
            meta = {"program": rng.choice(PEOPLE_PROGRAMS)}
    elif department == "Operations":
        meta = {
            "po": f"PO-{rng.randint(1000, 9999):04d}",
            "site": rng.choice(OPS_SITES),
        }
    elif department == "Legal":
        meta = {
            "matter": f"M-{rng.randint(100, 999):03d}",
            "external_counsel": rng.choice([True, False]),
        }
    else:
        meta = {"note": rng.choice(NOTE_SNIPPETS)}
    return _vary_filler(meta, rng)


def _is_outlier(item):
    return (item.department, item.category, item.month) in OUTLIERS


def _is_finance_ps_sep(item):
    return (
        item.department == "Finance"
        and item.category == "Professional Services"
        and item.month.month == 9
    )


def _is_finance_ps_march(item):
    return (
        item.department == "Finance"
        and item.category == "Professional Services"
        and item.month.month == 3
    )


def _scale_actuals(pairs, factor):
    for item, original in pairs:
        item.actual_amount = money(float(original) * factor)


def apply_finance_flip(items):
    jan_aug_months = {date(2026, month, 1) for month in range(1, 9)}

    for item in items:
        if _is_finance_ps_sep(item) and item.actual_amount is not None:
            item.actual_amount = money(item.budget_amount * Decimal("4.00"))
        elif _is_finance_ps_march(item) and item.actual_amount is not None:
            item.actual_amount = money(item.budget_amount * Decimal("0.90"))

    scalable = [
        item
        for item in items
        if item.department == "Finance"
        and item.actual_amount is not None
        and not _is_finance_ps_sep(item)
        and not _is_finance_ps_march(item)
    ]
    budget_jan_aug = sum(
        (
            item.budget_amount
            for item in items
            if item.department == "Finance" and item.month in jan_aug_months
        ),
        Decimal("0.00"),
    )
    ps_march_actual = next(
        item.actual_amount for item in items if _is_finance_ps_march(item)
    )
    scaled_jan_aug_actuals = sum(
        (item.actual_amount for item in scalable if item.month in jan_aug_months),
        Decimal("0.00"),
    )
    factor = (
        Decimal("0.988") * budget_jan_aug - ps_march_actual
    ) / scaled_jan_aug_actuals
    for item in scalable:
        item.actual_amount = money(item.actual_amount * factor)


def apply_department_band(items, department, rng, must_be_under=True):
    """Scale booked actuals so a department stays under (or over) budget."""
    strict_months = fully_booked_months(items)
    scalable = [
        item
        for item in items
        if item.department == department
        and item.actual_amount is not None
        and not _is_outlier(item)
        and not _is_finance_ps_sep(item)
        and not _is_finance_ps_march(item)
    ]
    if not scalable:
        return

    def ok():
        jan_aug = department_variance(items, department, strict_months)
        all_booked = department_variance(items, department)
        if must_be_under:
            return jan_aug < 0 and all_booked < 0
        return jan_aug > 0 and all_booked > 0

    if ok():
        return

    originals = [(item, item.actual_amount) for item in scalable]
    # Mildest adjustment first so a department that only just misses the
    # target lands close to budget rather than at an arbitrary offset.
    if must_be_under:
        candidates = [0.995, 0.99, 0.985, 0.98, 0.97, 0.96, 0.95, 0.93, 0.90]
    else:
        candidates = [1.005, 1.01, 1.015, 1.02, 1.03, 1.05, 1.08, 1.12]

    for factor in candidates:
        _scale_actuals(originals, factor)
        if ok():
            return


def apply_paid_ads_uplift_guard(items):
    mar_aug = category_uplift(items, "Marketing", "Paid Ads", range(3, 9))
    jan_aug = category_uplift(items, "Marketing", "Paid Ads", range(1, 9))
    if Decimal("0.28") <= mar_aug <= Decimal("0.34") and jan_aug > Decimal("0.20"):
        return

    jan_feb = [
        item
        for item in items
        if item.department == "Marketing"
        and item.category == "Paid Ads"
        and item.month.month in (1, 2)
        and item.actual_amount is not None
    ]
    originals = [(item, item.actual_amount) for item in jan_feb]
    for factor in [1.05, 1.08, 1.10, 1.12, 1.15, 1.18, 1.20]:
        _scale_actuals(originals, factor)
        jan_aug = category_uplift(items, "Marketing", "Paid Ads", range(1, 9))
        if jan_aug > Decimal("0.20"):
            return


def apply_metadata(items, rng):
    signal_keys = {
        (item.department, item.category, item.month)
        for item in items
        if planted_signal(item) is not None
    }
    eligible = [
        item
        for item in items
        if item.category != "Salaries"
        and (item.department, item.category, item.month) not in signal_keys
    ]
    for item in eligible:
        if rng.random() < 0.50:
            item.metadata = filler_metadata(item.department, rng)

    for item in items:
        signal = planted_signal(item)
        if signal is not None:
            item.metadata = dict(signal)

    total = len(items)
    filled = [item for item in items if item.metadata]
    coverage = len(filled) / total if total else 0
    if 0.45 <= coverage <= 0.55:
        return

    unused = [item for item in eligible if not item.metadata]
    extra = [item for item in eligible if item.metadata]
    if coverage < 0.45:
        needed = int(total * 0.48) - len(filled)
        for item in unused[: max(needed, 0)]:
            item.metadata = filler_metadata(item.department, rng)
    elif coverage > 0.55:
        overflow = len(filled) - int(total * 0.52)
        for item in extra[: max(overflow, 0)]:
            item.metadata = {}


def verify_stories(items):
    strict_months = fully_booked_months(items)
    variances = pair_variances(items, strict_months)
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
    strict_over = over_budget_departments(items, strict_months)
    if strict_over != STRICT_OVER:
        raise CommandError(
            "Departments over budget on fully-booked months should be "
            f"{sorted(STRICT_OVER)}, got {sorted(strict_over)}"
        )
    row_over = over_budget_departments(items)
    if row_over != ROW_OVER:
        raise CommandError(
            "Departments over budget on booked rows should be "
            f"{sorted(ROW_OVER)}, got {sorted(row_over)}"
        )

    september_departments = {
        item.department
        for item in items
        if item.month == SEPTEMBER and item.actual_amount is not None
    }
    if september_departments != SEPTEMBER_DEPARTMENTS:
        raise CommandError(
            "September actuals should exist only for Finance, Legal, and People, "
            f"got {sorted(september_departments)}"
        )
    if any(
        item.actual_amount is not None and item.month > SEPTEMBER for item in items
    ):
        raise CommandError("No actuals should be booked after September")

    events = [
        item
        for item in items
        if item.department == "Marketing"
        and item.category == "Events"
        and item.month.month in (5, 6)
    ]
    events_budget = sum((item.budget_amount for item in events), Decimal("0.00"))
    events_actual = sum((item.actual_amount for item in events), Decimal("0.00"))
    if events_budget == 0 or abs(events_actual - events_budget) / events_budget > Decimal(
        "0.05"
    ):
        raise CommandError(
            "Marketing/Events May+June actual should be within 5% of May+June budget"
        )

    mar_aug = category_uplift(items, "Marketing", "Paid Ads", range(3, 9))
    if not (Decimal("0.28") <= mar_aug <= Decimal("0.34")):
        raise CommandError(
            "Marketing/Paid Ads Mar–Aug uplift should be between 0.28 and 0.34, "
            f"got {mar_aug}"
        )
    jan_aug = category_uplift(items, "Marketing", "Paid Ads", range(1, 9))
    if jan_aug <= Decimal("0.20"):
        raise CommandError(
            "Marketing/Paid Ads Jan–Aug uplift should be greater than 0.20, "
            f"got {jan_aug}"
        )

    march_ps = next(
        item
        for item in items
        if _is_finance_ps_march(item)
    )
    if march_ps.actual_amount is None or march_ps.actual_amount >= march_ps.budget_amount:
        raise CommandError(
            "Finance/Professional Services March actual should be under budget"
        )

    finance_jan_aug_budget = Decimal("0.00")
    finance_jan_aug_actual = Decimal("0.00")
    finance_booked_budget = Decimal("0.00")
    finance_booked_actual = Decimal("0.00")
    for item in items:
        if item.department != "Finance" or item.actual_amount is None:
            continue
        finance_booked_budget += item.budget_amount
        finance_booked_actual += item.actual_amount
        if item.month in strict_months:
            finance_jan_aug_budget += item.budget_amount
            finance_jan_aug_actual += item.actual_amount
    jan_aug_ratio = (
        (finance_jan_aug_actual - finance_jan_aug_budget) / finance_jan_aug_budget
        if finance_jan_aug_budget
        else Decimal("0.00")
    )
    if not (Decimal("-0.020") <= jan_aug_ratio <= Decimal("-0.008")):
        raise CommandError(
            "Finance Jan–Aug variance should be between -2.0% and -0.8% of "
            f"Jan–Aug budget, got {jan_aug_ratio}"
        )
    jan_sep_ratio = (
        (finance_booked_actual - finance_booked_budget) / finance_booked_budget
        if finance_booked_budget
        else Decimal("0.00")
    )
    if jan_sep_ratio <= Decimal("0.005"):
        raise CommandError(
            "Finance Jan–Sep variance should be greater than +0.5% of "
            f"Jan–Sep budget, got {jan_sep_ratio}"
        )

    total = len(items)
    with_metadata = sum(1 for item in items if item.metadata)
    coverage = with_metadata / total if total else 0
    if not (0.45 <= coverage <= 0.55):
        raise CommandError(
            f"Metadata should be present on 45–55% of line items, got {coverage:.1%}"
        )
    if any(item.category == "Salaries" and item.metadata for item in items):
        raise CommandError("Salaries line items should not have metadata")

    for item in items:
        expected = planted_signal(item)
        if expected is not None and item.metadata != expected:
            raise CommandError(
                "Planted metadata on "
                f"{item.department}/{item.category}/{item.month:%Y-%m} "
                "did not match"
            )


class Command(BaseCommand):
    help = "Load a deterministic FY2026 operating budget scenario."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing scenario and regenerate it.",
        )

    def handle(self, *args, **options):
        scenario = Scenario.objects.filter(name=SCENARIO_NAME).first()
        if options["reset"] or scenario is None or not scenario.line_items.exists():
            scenario = self.seed()
            self.stdout.write(
                f"{scenario.name}: {scenario.line_items.count()} line items"
            )
        else:
            self.stdout.write(
                f"{scenario.name} already seeded "
                f"({scenario.line_items.count()} line items); use --reset to regenerate"
            )

    def seed(self):
        Scenario.objects.filter(name=SCENARIO_NAME).delete()
        scenario = Scenario.objects.create(
            name=SCENARIO_NAME,
            description=SCENARIO_DESCRIPTION,
        )
        rng = random.Random(RNG_SEED)
        items = []

        for department in DEPARTMENTS:
            booked_through = BOOKED_THROUGH[department]
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
                    if month <= booked_through:
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
                            metadata={},
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

            if (
                item.department == "Marketing"
                and item.category == "Events"
                and item.month.month == 5
            ):
                item.actual_amount = money(item.budget_amount * Decimal("0.05"))

        apply_finance_flip(items)
        apply_department_band(items, "Legal", rng, must_be_under=True)
        apply_department_band(items, "People", rng, must_be_under=True)
        apply_department_band(items, "Customer Success", rng, must_be_under=True)
        apply_department_band(items, "Engineering", rng, must_be_under=True)
        apply_department_band(items, "Operations", rng, must_be_under=False)
        apply_paid_ads_uplift_guard(items)
        apply_metadata(items, rng)
        verify_stories(items)
        LineItem.objects.bulk_create(items)
        return scenario
