package id.kongstudio.cafe.feature.sop

internal class SopSummary(
    val id: String,
    val title: String,
    val version: Int,
    val slideCount: Int,
    /** Kosong untuk SOP semua cabang. */
    val outletName: String?,
)

internal class SopSlide(val title: String, val body: String)

internal class SopDocument(
    val id: String,
    val title: String,
    val version: Int,
    val slides: List<SopSlide>,
)
