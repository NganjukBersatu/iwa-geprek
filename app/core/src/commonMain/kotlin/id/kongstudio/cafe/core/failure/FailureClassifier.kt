package id.kongstudio.cafe.core.failure

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject

private const val MaxCauseDepth = 6
private const val StatusUnauthorized = 401
private const val StatusNotFound = 404
private const val StatusMethodNotAllowed = 405
private const val FirstClientError = 400
private const val LastClientError = 499

private val TimeoutMarks = listOf("Timeout")
private val SecureMarks = listOf("SSL", "Certificate", "CertPath", "Handshake")
private val UnreachableMarks = listOf("UnknownHost", "ConnectException", "NoRouteToHost", "UnresolvedAddress", "SocketException", "EOF", "IOException")

/** Menggolongkan exception dari panggilan jaringan; hanya yang benar-benar soal sambungan yang dianggap tak terjangkau. */
fun failureOf(error: Throwable, where: String): AppFailure {
    val names = generateSequence(error) { it.cause }.take(MaxCauseDepth).map { it::class.simpleName.orEmpty() }.toList()
    fun has(marks: List<String>) = names.any { name -> marks.any { mark -> name.contains(mark) } }
    return when {
        has(TimeoutMarks) -> AppFailure.Timeout(where)
        has(SecureMarks) -> AppFailure.SecureConnection(where)
        has(UnreachableMarks) -> AppFailure.Unreachable(where)
        else -> AppFailure.Unexpected(names.firstOrNull().orEmpty().ifEmpty { "Exception" }, where)
    }
}

/** Menggolongkan jawaban server yang tidak sukses; [body] dipakai untuk mengambil pesan penolakan. */
fun failureOf(status: Int, where: String, body: String?): AppFailure = when {
    status == StatusUnauthorized -> AppFailure.Unauthorized
    status == StatusNotFound || status == StatusMethodNotAllowed -> AppFailure.NotFound(status, where)
    status in FirstClientError..LastClientError -> AppFailure.Rejected(status, rejectionMessage(body), rejectionCode(body))
    else -> AppFailure.Server(status, where)
}

/** Jawaban 2xx yang isinya tidak bisa dibaca dianggap gangguan di server, bukan jaringan. */
fun unreadableAnswer(status: Int, where: String): AppFailure = AppFailure.Server(status, where)

/** Kode galat stabil dari badan jawaban backend (`code`), atau null bila tidak ada. */
fun rejectionCode(body: String?): String? {
    if (body.isNullOrBlank()) return null
    return runCatching { (Json.parseToJsonElement(body).jsonObject["code"] as? JsonPrimitive)?.takeIf { it.isString }?.content }.getOrNull()
}

/** Pesan dari `detail` FastAPI: teks tunggal, atau daftar galat validasi (diambil yang pertama). */
fun rejectionMessage(body: String?): String? {
    if (body.isNullOrBlank()) return null
    return runCatching {
        val root: JsonObject = Json.parseToJsonElement(body).jsonObject
        when (val detail = root["detail"]) {
            is JsonPrimitive -> detail.takeIf { it.isString }?.content
            is JsonArray -> (detail.firstOrNull() as? JsonObject)?.get("msg")?.let { (it as? JsonPrimitive)?.content }
            else -> null
        }
    }.getOrNull()
}
