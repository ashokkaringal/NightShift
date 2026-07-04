"""Gmail-style subject lines and snippets from inbound message text."""

from __future__ import annotations

# (required keywords in body, subject line)
_SUBJECT_RULES: list[tuple[tuple[str, ...], str]] = [
    (("water stain",), "Bathroom ceiling water stain"),
    (("no heat",), "No heat in unit 4B"),
    (("gas", "odor"), "Possible gas odor near stove"),
    (("gas", "smell"), "Possible gas odor near stove"),
    (("code violation",), "City code violation notice"),
    (("stop-work",), "Stop-work order notice"),
    (("lightbulb",), "Hallway lightbulb out"),
    (("faucet",), "Drippy faucet follow-up"),
    (("maintenance request",), "Maintenance request follow-up"),
    (("pool hours",), "Pool hours update"),
    (("package room",), "Package room code issue"),
    (("parking",), "Parking violation notice"),
    (("fire alarm",), "Fire alarm inspection scheduled"),
    (("assesment",), "HOA quarterly assessment"),
    (("assessment",), "HOA quarterly assessment"),
    (("invoice",), "Vendor invoice review"),
    (("noise",), "Noise complaint follow-up"),
]


def derive_message_subject(raw_text: str | None, *, source: str = "email") -> str:
    """Short Gmail-style subject — never the full message body."""
    if not raw_text:
        return "Overnight message"

    text = raw_text.lower()
    for keys, subject in _SUBJECT_RULES:
        if all(key in text for key in keys):
            return subject

    if source == "hoa_portal":
        return "HOA portal notice"
    if source == "invoice":
        return "Vendor invoice"

    line = raw_text.splitlines()[0].strip()
    for sep in (". ", "? ", "! "):
        if sep in line:
            line = line.split(sep, 1)[0]
            break

    if len(line) > 58:
        line = f"{line[:55].rsplit(' ', 1)[0]}..."

    return line or "Overnight message"


def message_snippet(raw_text: str | None, *, max_len: int = 100) -> str:
    """One-line preview for the list pane."""
    if not raw_text:
        return ""
    line = " ".join(raw_text.split())
    if len(line) <= max_len:
        return line
    return f"{line[: max_len - 3].rsplit(' ', 1)[0]}..."
