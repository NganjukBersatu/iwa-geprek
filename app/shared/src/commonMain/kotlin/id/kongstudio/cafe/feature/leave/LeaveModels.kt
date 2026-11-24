package id.kongstudio.cafe.feature.leave

internal enum class LeaveType(val apiValue: String) {
    Permit("izin"),
    Sick("sakit"),
}

internal enum class LeaveStatus { Pending, Approved, Rejected }

internal class LeaveRequest(
    val id: String,
    val type: LeaveType,
    /** Tanggal "YYYY-MM-DD". */
    val startDate: String,
    val endDate: String,
    val reason: String,
    val status: LeaveStatus,
    val decidedBy: String?,
    val managerNote: String?,
    val attachmentUrl: String?,
    val attachmentLink: String?,
)

/** Lampiran pengajuan, foto JPEG atau PDF, beserta jenis dan nama berkas yang dikirim ke server. */
internal class LeaveAttachment(val bytes: ByteArray, val contentType: String, val fileName: String) {
    companion object {
        fun photo(bytes: ByteArray) = LeaveAttachment(bytes, "image/jpeg", "lampiran.jpg")

        fun pdf(bytes: ByteArray) = LeaveAttachment(bytes, "application/pdf", "lampiran.pdf")
    }
}

/** Isian pengajuan; [link] boleh kosong bila ada lampiran. */
internal class LeaveForm(
    val type: LeaveType,
    val startDate: String,
    val endDate: String,
    val reason: String,
    val link: String,
)
