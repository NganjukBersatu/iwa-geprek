package id.kongstudio.cafe.feature.admin

import id.kongstudio.cafe.core.format.rupiahOf
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObjectBuilder
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull

/** Rupiah dari angka atau teks desimal kiriman server lewat [rupiahOf], tanpa melewati Double. */
internal fun JsonElement?.toMoney(): Long = toMoneyOrNull() ?: 0L

/** Seperti [toMoney] tetapi null tetap null, untuk angka yang belum ada (misalnya selisih shift yang belum ditutup). */
internal fun JsonElement?.toMoneyOrNull(): Long? =
    (this as? JsonPrimitive)?.contentOrNull?.let(::rupiahOf)

/** Mengisi bidang teks; kosong dikirim sebagai null supaya server menghapus nilainya. */
internal fun JsonObjectBuilder.putText(key: String, value: String?) {
    val text = value?.trim()
    put(key, if (text.isNullOrEmpty()) JsonNull else JsonPrimitive(text))
}
