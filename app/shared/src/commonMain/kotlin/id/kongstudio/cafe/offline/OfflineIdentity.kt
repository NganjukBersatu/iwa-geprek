package id.kongstudio.cafe.offline

import kotlin.io.encoding.Base64
import kotlin.io.encoding.ExperimentalEncodingApi
import kotlin.random.Random
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject

private const val UuidBytes = 16
private const val VersionByte = 6
private const val VariantByte = 8
private const val VersionMask = 0x0F
private const val VersionFour = 0x40
private const val VariantMask = 0x3F
private const val VariantRfc = 0x80
private const val ByteMask = 0xFF
private const val JwtPayloadIndex = 1

/** UUID v4 sebagai kunci idempoten pesanan; dibuat di tablet sebelum pesanan dikirim. */
internal fun newClientId(): String {
    val bytes = Random.nextBytes(UuidBytes)
    bytes[VersionByte] = ((bytes[VersionByte].toInt() and VersionMask) or VersionFour).toByte()
    bytes[VariantByte] = ((bytes[VariantByte].toInt() and VariantMask) or VariantRfc).toByte()
    val hex = bytes.joinToString("") { (it.toInt() and ByteMask).toString(16).padStart(2, '0') }
    return "${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}"
}

/** Id karyawan dari klaim `sub` token, dibaca tanpa jaringan dan tanpa memeriksa tanda tangan (server yang memeriksa saat pesanan dikirim). */
@OptIn(ExperimentalEncodingApi::class)
internal fun userIdOf(token: String): String? = runCatching {
    val part = token.split('.').getOrNull(JwtPayloadIndex) ?: return null
    val json = Base64.UrlSafe.withPadding(Base64.PaddingOption.PRESENT_OPTIONAL).decode(part).decodeToString()
    val root: JsonObject = Json.parseToJsonElement(json).jsonObject
    (root["sub"] as? JsonPrimitive)?.takeIf { it.isString }?.content
}.getOrNull()
