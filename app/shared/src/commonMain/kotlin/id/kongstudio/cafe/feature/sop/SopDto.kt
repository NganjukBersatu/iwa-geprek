package id.kongstudio.cafe.feature.sop

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class SopSummaryDto(
    val id: String,
    val title: String,
    val version: Int = 1,
    @SerialName("slide_count") val slideCount: Int = 0,
    @SerialName("outlet_name") val outletName: String? = null,
) {
    fun toModel() = SopSummary(id = id, title = title, version = version, slideCount = slideCount, outletName = outletName)
}

@Serializable
internal class SopSlideDto(
    val title: String,
    val body: String = "",
)

@Serializable
internal class SopDetailDto(
    val id: String,
    val title: String,
    val version: Int = 1,
    val slides: List<SopSlideDto> = emptyList(),
) {
    fun toModel() = SopDocument(
        id = id,
        title = title,
        version = version,
        slides = slides.map { SopSlide(title = it.title, body = it.body) },
    )
}

@Serializable
internal class SopReadDto(
    @SerialName("sop_id") val sopId: String,
    val version: Int,
)

@Serializable
internal class SopReadInDto(val version: Int)
