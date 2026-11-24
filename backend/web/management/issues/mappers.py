"""Turns the findings into their response schema."""
from dataclasses import asdict

from web.management.issues.domain import Issue, IssueLevel
from web.management.issues.schemas import IssueOut, IssuesOut


def issues_out(items: list[Issue], outlet_names: dict[str, str]) -> IssuesOut:
    def count(level: IssueLevel) -> int:
        return sum(1 for item in items if item.level == level)

    return IssuesOut(
        problem=count(IssueLevel.PROBLEM),
        warning=count(IssueLevel.WARNING),
        notice=count(IssueLevel.NOTICE),
        suggestion=count(IssueLevel.SUGGESTION),
        items=[IssueOut(**asdict(item), outlet_name=outlet_names.get(item.outlet_id) if item.outlet_id else None) for item in items],
    )
