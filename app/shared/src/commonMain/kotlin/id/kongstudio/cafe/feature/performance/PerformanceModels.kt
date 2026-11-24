package id.kongstudio.cafe.feature.performance

internal enum class PerformanceRange(val key: String) {
    Cycle("cycle"),
    Previous("previous"),
    All("all"),
}

/** Satu batang grafik: satu minggu dari awal siklus, atau satu siklus utuh pada rentang sejak bergabung. */
internal class PerformanceBucket(
    val start: String,
    val onTimePercent: Int?,
    val workMinutes: Int,
    val tasksDone: Int,
)

internal class PerformanceComposition(
    val onTime: Int,
    val late: Int,
    val leave: Int,
    val absent: Int,
) {
    val total: Int get() = onTime + late + leave + absent
}

internal class RatingComponent(val key: String, val percent: Double?)

internal class RatingGroup(val key: String, val components: List<RatingComponent>)

/** Bintang 0 sampai 5 kelipatan 0,5; null bila belum cukup data. */
internal class Rating(val stars: Double?, val groups: List<RatingGroup>)

internal class Performance(
    val start: String,
    val end: String,
    val countedDays: Int,
    val buckets: List<PerformanceBucket>,
    val composition: PerformanceComposition,
    val workMinutes: Int,
    val overtimeMinutes: Int,
    val tasksAssigned: Int,
    val tasksDone: Int,
    val rating: Rating,
)
