package id.kongstudio.cafe.feature.dayplan

/** Rentang yang sedang berlaku: lembur menyala saat jamnya tiba, jam kerja menyala selama sudah absen datang, belum absen pulang, dan belum lewat jam selesai. */
internal fun activeSegment(segments: List<DaySegment>, nowEpoch: Long, clockedIn: Boolean): DaySegment? =
    segments.firstOrNull { it.isOvertime && nowEpoch >= it.startEpoch && nowEpoch < it.endEpoch }
        ?: segments.firstOrNull { !it.isOvertime && clockedIn && nowEpoch < it.endEpoch }
