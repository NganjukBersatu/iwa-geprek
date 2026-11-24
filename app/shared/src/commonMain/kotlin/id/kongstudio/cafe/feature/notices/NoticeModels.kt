package id.kongstudio.cafe.feature.notices

import id.kongstudio.cafe.core.format.WibStamp

internal enum class NoticeKind { TaskAssigned, TaskOverdue, DueChanged }

/** Satu pengumuman untuk karyawan; [showAt] saat pengumuman mulai berlaku. */
class NoticeItem internal constructor(
    val id: String,
    internal val kind: NoticeKind,
    val title: String,
    val showAt: WibStamp?,
)
