package id.kongstudio.cafe.feature.admin

/** Kunci baku [PagedListViewModel.setParams] untuk penyaring yang dipakai banyak daftar; nilai kosong berarti tidak disaring. */
internal object ListParam {
    const val From = "from"
    const val To = "to"
    /** Dikirim ke server sebagai user_id. */
    const val UserId = "user_id"
    /** Hanya untuk label tag; tidak pernah dikirim ke server. */
    const val UserName = "user_name"
}
