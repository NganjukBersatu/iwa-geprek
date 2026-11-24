package id.kongstudio.cafe.feature.leave

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class LeaveResponseDto(
    val id: String,
    val type: String,
    @SerialName("start_date") val startDate: String,
    @SerialName("end_date") val endDate: String,
    val reason: String,
    val status: String,
    @SerialName("decided_by") val decidedBy: String? = null,
    @SerialName("manager_note") val managerNote: String? = null,
    @SerialName("attachment_url") val attachmentUrl: String? = null,
    @SerialName("attachment_link") val attachmentLink: String? = null,
) {
    fun toModel() = LeaveRequest(
        id = id,
        type = if (type == LeaveType.Sick.apiValue) LeaveType.Sick else LeaveType.Permit,
        startDate = startDate,
        endDate = endDate,
        reason = reason,
        status = when (status) {
            "disetujui" -> LeaveStatus.Approved
            "ditolak" -> LeaveStatus.Rejected
            else -> LeaveStatus.Pending
        },
        decidedBy = decidedBy,
        managerNote = managerNote?.takeIf { it.isNotBlank() },
        attachmentUrl = attachmentUrl,
        attachmentLink = attachmentLink?.takeIf { it.isNotBlank() },
    )
}
