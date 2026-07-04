"""Blue/Green output validation — cross-tenant leakage checks (Member D — D4)."""

from __future__ import annotations

from dataclasses import dataclass

from memory.store import PROPERTY_DISPLAY_NAMES, get_property_display_name
from models.core import ClassifiedItem


class OutputValidationError(ValueError):
    """Raised when draft output contains critical cross-tenant leakage."""


@dataclass(frozen=True)
class OutputIssue:
    severity: str  # "critical" | "warning"
    code: str
    message: str


def _other_property_labels(property_id: str | None) -> set[str]:
    if not property_id or property_id == "unknown":
        return set(PROPERTY_DISPLAY_NAMES.values())
    return {
        label
        for pid, label in PROPERTY_DISPLAY_NAMES.items()
        if pid != property_id
    }


def _tenant_emails_for_other_properties(property_id: str | None) -> set[str]:
    from memory.store import _load_json

    emails: set[str] = set()
    for row in _load_json("tenant_property_map.json"):
        if row.get("property_id") != property_id:
            email = row.get("tenant_email")
            if email:
                emails.add(email.lower())
    return emails


def validate_draft_output(draft_text: str, classified: ClassifiedItem) -> list[OutputIssue]:
    """Detect cross-tenant property names or emails in drafts."""
    if not draft_text or draft_text.startswith("(No tenant reply drafted"):
        return []

    issues: list[OutputIssue] = []
    text_lower = draft_text.lower()
    own_label = (get_property_display_name(classified.property_id) or "").lower()

    for label in _other_property_labels(classified.property_id):
        if label.lower() in text_lower and label.lower() != own_label:
            issues.append(
                OutputIssue(
                    severity="warning",
                    code="cross_property_name",
                    message=f"Draft mentions other property label: {label}",
                )
            )

    for email in _tenant_emails_for_other_properties(classified.property_id):
        if email in text_lower:
            issues.append(
                OutputIssue(
                    severity="critical",
                    code="cross_tenant_email",
                    message=f"Draft contains another tenant email: {email}",
                )
            )

    return issues


def assert_draft_output_safe(draft_text: str, classified: ClassifiedItem) -> list[OutputIssue]:
    issues = validate_draft_output(draft_text, classified)
    critical = [issue for issue in issues if issue.severity == "critical"]
    if critical:
        raise OutputValidationError("; ".join(issue.message for issue in critical))
    return issues
