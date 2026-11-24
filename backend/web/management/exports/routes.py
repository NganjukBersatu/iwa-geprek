"""Download of a table as CSV, Excel or PDF; the screen sends what it shows and any signed-in person may ask, since nothing is looked up."""
from fastapi import APIRouter, Depends, Response

from app.core import clock, table_export
from app.core.auth import current_user
from app.models.user import User
from web.management.exports.schemas import ExportIn

router = APIRouter(prefix="/exports", tags=["web-exports"])


@router.post("/table")
def export_table(body: ExportIn, _: User = Depends(current_user)):
    exported = table_export.render(
        body.format,
        body.title,
        [table_export.ExportColumn(column.label, column.align) for column in body.columns],
        body.rows,
        clock.now(),
    )
    name = table_export.filename(body.title, exported.extension, clock.today())
    return Response(content=exported.content, media_type=exported.media_type, headers={"Content-Disposition": f'attachment; filename="{name}"'})
