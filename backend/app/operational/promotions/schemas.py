from app.core.catalog.promotion_schemas import AnnouncementOut, PromoOut


class TabletPromoOut(PromoOut):
    # Benar bila promo ini milik cabang tablet saja, jadi boleh diubah dari sini; yang berlaku di semua cabang diubah dari web admin.
    editable: bool


class TabletAnnouncementOut(AnnouncementOut):
    editable: bool
