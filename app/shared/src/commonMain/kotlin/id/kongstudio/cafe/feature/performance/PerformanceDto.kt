package id.kongstudio.cafe.feature.performance

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class PerformanceDto(
    val start: String,
    val end: String,
    @SerialName("counted_days") val countedDays: Int = 0,
    val buckets: List<BucketDto> = emptyList(),
    val composition: CompositionDto = CompositionDto(),
    @SerialName("tasks_assigned") val tasksAssigned: Int = 0,
    @SerialName("tasks_done") val tasksDone: Int = 0,
    val rating: RatingDto = RatingDto(),
) {
    fun toModel() = Performance(
        start = start,
        end = end,
        countedDays = countedDays,
        buckets = buckets.map { it.toModel() },
        composition = composition.toModel(),
        workMinutes = buckets.sumOf { it.workMinutes },
        overtimeMinutes = buckets.sumOf { it.overtimeMinutes },
        tasksAssigned = tasksAssigned,
        tasksDone = tasksDone,
        rating = rating.toModel(),
    )
}

@Serializable
internal class BucketDto(
    val start: String,
    @SerialName("on_time_percent") val onTimePercent: Int? = null,
    @SerialName("work_minutes") val workMinutes: Int = 0,
    @SerialName("overtime_minutes") val overtimeMinutes: Int = 0,
    @SerialName("tasks_done") val tasksDone: Int = 0,
) {
    fun toModel() = PerformanceBucket(
        start = start,
        onTimePercent = onTimePercent,
        workMinutes = workMinutes,
        tasksDone = tasksDone,
    )
}

@Serializable
internal class CompositionDto(
    @SerialName("on_time") val onTime: Int = 0,
    val late: Int = 0,
    val leave: Int = 0,
    val absent: Int = 0,
) {
    fun toModel() = PerformanceComposition(onTime = onTime, late = late, leave = leave, absent = absent)
}

@Serializable
internal class RatingComponentDto(val key: String, val percent: Double? = null) {
    fun toModel() = RatingComponent(key = key, percent = percent)
}

@Serializable
internal class RatingGroupDto(val key: String, val components: List<RatingComponentDto> = emptyList()) {
    fun toModel() = RatingGroup(key = key, components = components.map { it.toModel() })
}

@Serializable
internal class RatingDto(val stars: Double? = null, val groups: List<RatingGroupDto> = emptyList()) {
    fun toModel() = Rating(stars = stars, groups = groups.map { it.toModel() })
}
