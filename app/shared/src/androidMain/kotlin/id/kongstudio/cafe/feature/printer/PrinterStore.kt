package id.kongstudio.cafe.feature.printer

import android.content.Context
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

private const val PrefsName = "thermal_printers"
private const val StoreKey = "printers"
private const val KeepAliveKey = "keep_alive"
// Versi 3 menambah logoOff; printer dari versi lama tanpa logo tersimpan di memorinya dianggap tanpa logo.
private const val StoreVersion = 3
private const val LogoOffSince = 3
private const val LegacySeparator = "|"
private const val LegacyFieldCount = 3
// Format pertama hanya mengenal empat peran tetap; kuncinya sama dengan kunci slot struk dan peran lama.
private val FirstFormatSlots = listOf(PrinterSlot.Receipt) + PrinterSlot.Legacy

/** Satu printer yang dipasang pada satu slot; kolom yang belum diketahui dibiarkan kosong. */
@Serializable
internal data class StoredPrinter(
    val name: String,
    val address: String,
    val paper: String,
    val columns: Int? = null,
    val columnsSource: String? = null,
    val serviceUuid: String? = null,
    val characteristicUuid: String? = null,
    val logoVersion: Int? = null,
    val logoOff: Boolean = false,
)

@Serializable
private data class StoredPrinters(val version: Int, val roles: Map<String, StoredPrinter>)

/** Pemasangan printer di tablet, berversi supaya kolom baru tidak pernah menghapus pemasangan lama. */
internal class PrinterStore(context: Context) {
    private val prefs = context.getSharedPreferences(PrefsName, Context.MODE_PRIVATE)
    private val json = Json { ignoreUnknownKeys = true }

    fun load(): Map<PrinterSlot, StoredPrinter> {
        val raw = prefs.getString(StoreKey, null) ?: return migrateLegacy()
        val stored = runCatching { json.decodeFromString(StoredPrinters.serializer(), raw) }.getOrNull() ?: return emptyMap()
        val printers = stored.roles.mapNotNull { (key, printer) -> PrinterSlot.fromKey(key)?.let { it to printer } }.toMap()
        if (stored.version >= LogoOffSince) return printers
        // Logo yang dulu dijawab rusak atau belum pernah disimpan ke printer tidak lagi dikirim lengkap tanpa diminta.
        val migrated = printers.mapValues { (_, printer) -> printer.copy(logoOff = printer.logoVersion != ReceiptLogo.Version) }
        save(migrated)
        return migrated
    }

    fun loadKeepAlive(): Boolean = prefs.getBoolean(KeepAliveKey, false)

    fun saveKeepAlive(enabled: Boolean) {
        prefs.edit().putBoolean(KeepAliveKey, enabled).apply()
    }

    fun save(printers: Map<PrinterSlot, StoredPrinter>) {
        val stored = StoredPrinters(StoreVersion, printers.mapKeys { it.key.key })
        prefs.edit().putString(StoreKey, json.encodeToString(StoredPrinters.serializer(), stored)).apply()
    }

    /** Format pertama menyimpan "nama|alamat|kertas" per peran; dipindah sekali lalu kunci lamanya dibuang. */
    private fun migrateLegacy(): Map<PrinterSlot, StoredPrinter> {
        val migrated = buildMap {
            FirstFormatSlots.forEach { slot ->
                val parts = prefs.getString(slot.key, null)?.split(LegacySeparator) ?: return@forEach
                if (parts.size < LegacyFieldCount) return@forEach
                put(slot, StoredPrinter(name = parts[0], address = parts[1], paper = parts[2], logoOff = true))
            }
        }
        save(migrated)
        prefs.edit().apply { FirstFormatSlots.forEach { remove(it.key) } }.apply()
        return migrated
    }
}
