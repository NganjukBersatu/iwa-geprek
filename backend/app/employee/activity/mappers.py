from app.employee.activity.domain import Event, Page
from app.employee.activity.schemas import ActivityPageOut, EventOut


def event_out(event: Event) -> EventOut:
    return EventOut(
        id=event.id,
        group=event.group,
        action=event.action,
        at=event.at,
        subject=event.subject,
        status=event.status,
        minutes=event.minutes,
    )


def page_out(page: Page) -> ActivityPageOut:
    return ActivityPageOut(events=[event_out(event) for event in page.events], next_before=page.next_before)
