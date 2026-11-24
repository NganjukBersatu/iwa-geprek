package id.kongstudio.cafe.feature.attendance.selfschedule

import id.kongstudio.cafe.core.format.WibStamp

internal class SelfScheduleChoice(val id: String, val name: String)

/** Kode shift cabang yang jam mulainya dekat dengan sekarang, beserta jam nyata penugasannya. */
internal class ShiftSuggestion(
    val shiftCodeId: String,
    val code: String,
    val startsAt: WibStamp?,
    val endsAt: WibStamp?,
)

internal class SelfScheduleOptions(
    val outlets: List<SelfScheduleChoice>,
    val roles: List<SelfScheduleChoice>,
    val suggestions: List<ShiftSuggestion>,
)

internal class SelfScheduleRequest(
    val outletId: String,
    val roleId: String,
    val shiftCodeId: String,
    val reason: String?,
)
