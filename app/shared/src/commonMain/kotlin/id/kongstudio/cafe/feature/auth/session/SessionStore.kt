package id.kongstudio.cafe.feature.auth.session

interface SessionStore {
    /** Null bila belum pernah masuk, sudah kedaluwarsa, atau data tidak terbaca. */
    suspend fun load(): LoginSession?

    suspend fun save(session: LoginSession)

    suspend fun clear()

    /** Token yang sudah keluar di perangkat tapi belum berhasil dicabut di server. */
    suspend fun pendingRevocations(): List<String>

    suspend fun addPendingRevocation(token: String)

    suspend fun removePendingRevocation(token: String)
}
