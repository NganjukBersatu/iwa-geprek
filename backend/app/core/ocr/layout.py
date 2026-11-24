from app.core.ocr.engine import TextBox

SAME_ROW_OVERLAP = 0.5


def _overlap(box: TextBox, top: float, bottom: float) -> float:
    shared = min(box.bottom, bottom) - max(box.top, top)
    smaller = min(box.bottom - box.top, bottom - top)
    return shared / smaller if smaller > 0 else 0.0


def lines_of(boxes: list[TextBox]) -> list[str]:
    """A receipt prints the name on the left and the price on the right as separate boxes; boxes sharing a height become one line."""
    rows: list[tuple[float, float, list[TextBox]]] = []
    for box in sorted(boxes, key=lambda item: (item.top + item.bottom) / 2):
        if rows and _overlap(box, rows[-1][0], rows[-1][1]) >= SAME_ROW_OVERLAP:
            top, bottom, members = rows[-1]
            members.append(box)
            rows[-1] = (min(top, box.top), max(bottom, box.bottom), members)
        else:
            rows.append((box.top, box.bottom, [box]))
    return [" ".join(member.text for member in sorted(members, key=lambda item: item.left)) for _top, _bottom, members in rows]
