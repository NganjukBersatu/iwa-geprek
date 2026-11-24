"""The one standalone error page: no sidebar, no script, always a way to try again."""
from html import escape

from app.core import brand

_TEMPLATE = """<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title} - {brand}</title>
<style>
:root {{ --ink: {ink}; --muted: {muted}; --brand: {primary}; --brand-deep: {primary_deep}; --page: {page}; --white: #FFFFFF; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; background: var(--page); color: var(--ink); font-family: Poppins, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ width: 100%; max-width: 480px; }}
h1 {{ margin: 0 0 16px; font-size: 1.5rem; line-height: 2rem; font-weight: 600; }}
p {{ margin: 0 0 24px; font-size: 1rem; line-height: 1.5rem; overflow-wrap: anywhere; }}
a.action {{ display: inline-flex; align-items: center; min-height: 44px; padding: 0 24px; border-radius: 6px; background: var(--brand); color: var(--white); font-size: 0.875rem; line-height: 1.25rem; font-weight: 500; text-decoration: none; }}
a.action:hover {{ background: var(--brand-deep); }}
a.action:focus-visible {{ outline: 2px solid var(--brand); outline-offset: 2px; }}
small {{ display: block; margin-top: 32px; font-size: 0.75rem; line-height: 1rem; color: var(--muted); overflow-wrap: anywhere; }}
</style>
</head>
<body>
<main>
<h1>{title}</h1>
<p>{body}</p>
<a class="action" href="">{action}</a>
{reference}
</main>
</body>
</html>
"""


def render(title: str, body: str, action: str, reference_label: str, request_id: str) -> str:
    """The page as text; every value is escaped, so nothing a request carried can become markup."""
    reference = f"<small>{escape(reference_label)}: {escape(request_id)}</small>" if request_id else ""
    return _TEMPLATE.format(title=escape(title), body=escape(body), action=escape(action), reference=reference, brand=escape(brand.NAME), **brand.PAGE_COLORS)
