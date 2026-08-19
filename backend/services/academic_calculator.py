"""Generic calculator for activity-unit and direct-hour academic rulesets."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from models.academic_models import (
    AcademicLineResult,
    AcademicOccasionResult,
    AcademicPayRequest,
    AcademicPayResponse,
    AcademicWorkKind,
)
from services.academic_rules import get_academic_ruleset


def _normalized_topic(topic: str | None) -> str:
    return " ".join((topic or "").casefold().split())


def _money(value: float | Decimal) -> float:
    """Round a monetary line using conventional half-up currency rounding."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class AcademicPayCalculator:
    def __init__(self, data: AcademicPayRequest):
        self.data = data
        self.rules = get_academic_ruleset(data.scheme)
        self.activities = self.rules.ACTIVITIES
        self.courses = {course.id: course for course in data.courses}

    def _rate_schedule(self, work_date: date) -> tuple[date, dict]:
        eligible = [
            schedule
            for schedule in self.rules.RATE_SCHEDULES
            if date.fromisoformat(schedule["effective_from"]) <= work_date
        ]
        if not eligible:
            raise ValueError(f"No academic rate schedule applies on {work_date.isoformat()}.")
        selected = max(eligible, key=lambda schedule: schedule["effective_from"])
        return date.fromisoformat(selected["effective_from"]), selected["rates"]

    def _course_for(self, item, activity_rule):
        if activity_rule.get("course_required") and not item.course_id:
            raise ValueError(f"{activity_rule['label']} requires a course.")
        if item.course_id and item.course_id not in self.courses:
            raise ValueError(f"Unknown course ID {item.course_id!r} on item {item.id!r}.")
        return self.courses.get(item.course_id)

    @staticmethod
    def _eligibility_key(course) -> str:
        if course and course.eligibility.value in {"relevant_phd", "full_coordinator"}:
            return "higher"
        return "standard"

    def _classification_record(self, rule, variant, classification, eligibility):
        effective_variant = "repeat" if classification == "repeat" else variant
        if rule.get("variant_uses_default_classification"):
            effective_variant = rule["default_variant"]
        key = f"{effective_variant}:{eligibility}"
        record = rule["classifications"].get(key)
        if record is None and eligibility == "higher":
            record = rule["classifications"].get(f"{effective_variant}:standard")
        if record is None:
            raise ValueError(f"No classification is configured for {key!r}.")
        return effective_variant, record

    def calculate(self) -> AcademicPayResponse:
        combined = [
            *((item, True) for item in self.data.lookback_items),
            *((item, False) for item in self.data.work_items),
        ]
        # Stable input order distinguishes multiple deliveries on the same date.
        combined = sorted(
            enumerate(combined),
            key=lambda pair: (pair[1][0].date, pair[0]),
        )
        prior_repeatable = []
        line_items = []
        credited_by_occasion = {}
        warnings = []

        for _, (item, is_lookback) in combined:
            rule = self.activities.get(item.activity)
            if rule is None:
                raise ValueError(f"Unknown academic activity {item.activity!r}.")
            expected_kind = (
                AcademicWorkKind.ACTIVITY
                if rule["payment_basis"] == "composite_unit"
                else AcademicWorkKind.DIRECT_HOURS
            )
            if item.kind != expected_kind:
                raise ValueError(
                    f"{rule['label']} must use the {expected_kind.value!r} work-item kind."
                )
            course = self._course_for(item, rule)
            if rule.get("topic_required") and not (item.topic or "").strip():
                raise ValueError(f"{rule['label']} requires a topic or teaching week.")
            if rule.get("requires_approval") and not item.required_or_approved:
                raise ValueError(f"{rule['label']} hours must be marked required or approved.")

            variant = item.variant or rule["default_variant"]
            if variant not in rule["variants"]:
                raise ValueError(f"Unknown {rule['label']} variant {variant!r}.")

            repeat_match = None
            if rule.get("repeatable"):
                for earlier in reversed(prior_repeatable):
                    days = (item.date - earlier.date).days
                    if days > self.rules.SCHEME["repeat_window_days"]:
                        break
                    if (
                        days >= 0
                        and earlier.activity == item.activity
                        and earlier.course_id == item.course_id
                        and _normalized_topic(earlier.topic) == _normalized_topic(item.topic)
                    ):
                        repeat_match = earlier
                        break
            automatic = "repeat" if repeat_match else "original"
            final = item.classification_override or automatic
            if final == "repeat" and not rule.get("repeatable"):
                raise ValueError(f"{rule['label']} cannot be classified as repeat work.")

            eligibility = self._eligibility_key(course)
            effective_variant, classification_record = self._classification_record(
                rule, variant, final, eligibility
            )
            effective_date, rates = self._rate_schedule(item.date)
            rate_code = classification_record["rate_code"]
            if rate_code not in rates:
                raise ValueError(f"Rate code {rate_code!r} is missing for {item.date.isoformat()}.")
            rate = rates[rate_code]
            quantity = (
                item.delivered_quantity
                if expected_kind == AcademicWorkKind.ACTIVITY
                else item.actual_hours
            )
            incorporated = round(
                quantity * classification_record.get("incorporated_hours", 0), 6
            )
            paid_hours = round(quantity + incorporated, 6) if expected_kind == AcademicWorkKind.ACTIVITY else quantity
            pay = _money(Decimal(str(quantity)) * Decimal(str(rate)))
            variance = None
            item_warnings = []
            if expected_kind == AcademicWorkKind.ACTIVITY and item.actual_associated_hours is not None:
                variance = round(item.actual_associated_hours - incorporated, 6)
                if variance > 0:
                    item_warnings.append(
                        f"Actual associated work exceeds incorporated time by {variance:g} hours; review separately."
                    )

            if repeat_match:
                reason = (
                    f"Matches {repeat_match.id} for the same course, activity and topic "
                    f"within {self.rules.SCHEME['repeat_window_days']} days."
                )
            else:
                reason = "No earlier matching delivery was supplied within seven days."
            if item.classification_override:
                reason = f"User override to {final}: {item.override_reason}"

            if is_lookback:
                if rule.get("repeatable"):
                    prior_repeatable.append(item)
                continue

            course_code = course.code if course else None
            line = AcademicLineResult(
                id=item.id,
                date=item.date,
                occasion_id=item.occasion_id,
                course_id=item.course_id,
                course_code=course_code,
                topic=item.topic,
                activity=item.activity,
                activity_label=rule["label"],
                variant=variant,
                payment_basis=rule["payment_basis"],
                automatic_classification=automatic,
                final_classification=final,
                classification_label=classification_record["label"],
                repeat_match_id=repeat_match.id if repeat_match else None,
                classification_reason=reason,
                override_reason=item.override_reason,
                rate_code=rate_code,
                rate=rate,
                rate_effective_from=effective_date,
                quantity=quantity,
                quantity_label=rule["quantity_label"],
                incorporated_hours=incorporated,
                actual_associated_hours=item.actual_associated_hours,
                associated_hours_variance=variance,
                paid_hours=paid_hours,
                pay=pay,
                warnings=item_warnings,
            )
            line_items.append(line)
            occasion_key = (item.date, item.occasion_id)
            occasion = credited_by_occasion.setdefault(
                occasion_key, {"hours": 0.0, "items": []}
            )
            occasion["hours"] += paid_hours
            occasion["items"].append(item.id)
            warnings.extend(f"{item.id}: {message}" for message in item_warnings)
            if rule.get("repeatable"):
                prior_repeatable.append(item)

        minimum = self.rules.SCHEME.get("minimum_engagement_hours", 0)
        occasions = []
        for (occasion_date, occasion_id), values in credited_by_occasion.items():
            credited = round(values["hours"], 6)
            shortfall = round(max(0, minimum - credited), 6)
            occasions.append(AcademicOccasionResult(
                occasion_id=occasion_id,
                date=occasion_date,
                credited_hours=credited,
                minimum_hours=minimum,
                shortfall_hours=shortfall,
                item_ids=values["items"],
            ))
            if shortfall > 0:
                warnings.append(
                    f"{occasion_date.isoformat()} occasion {occasion_id}: review a {shortfall:g}-hour minimum-engagement shortfall."
                )

        activity_lines = [line for line in line_items if line.payment_basis == "composite_unit"]
        direct_lines = [line for line in line_items if line.payment_basis == "direct_hour"]
        activity_pay = _money(sum(Decimal(str(line.pay)) for line in activity_lines))
        direct_pay = _money(sum(Decimal(str(line.pay)) for line in direct_lines))
        period_end = date.fromordinal(self.data.period_start.toordinal() + 13)

        return AcademicPayResponse(
            scheme=self.data.scheme,
            scheme_label=self.rules.SCHEME["label"],
            period_start=self.data.period_start,
            period_end=period_end,
            line_items=line_items,
            occasions=sorted(occasions, key=lambda item: (item.date, item.occasion_id)),
            activity_pay=activity_pay,
            direct_hours_pay=direct_pay,
            total_pay=_money(Decimal(str(activity_pay)) + Decimal(str(direct_pay))),
            delivered_hours=round(sum(line.quantity for line in activity_lines), 2),
            direct_hours=round(sum(line.quantity for line in direct_lines), 2),
            incorporated_hours=round(sum(line.incorporated_hours for line in activity_lines), 2),
            actual_associated_hours=round(sum(line.actual_associated_hours or 0 for line in activity_lines), 2),
            review_warnings=warnings,
            ruleset=self.public_ruleset(),
        )

    def public_ruleset(self) -> dict:
        return {
            "scheme": self.rules.SCHEME,
            "eligibility": self.rules.ELIGIBILITY,
            "activities": self.rules.ACTIVITIES,
            "rate_schedules": self.rules.RATE_SCHEDULES,
        }


def public_academic_ruleset(scheme: str) -> dict:
    rules = get_academic_ruleset(scheme)
    return {
        "scheme": rules.SCHEME,
        "eligibility": rules.ELIGIBILITY,
        "activities": rules.ACTIVITIES,
        "rate_schedules": rules.RATE_SCHEDULES,
    }
