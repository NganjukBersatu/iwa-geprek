package id.kongstudio.cafe.feature.printer

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.map
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

internal const val PrintPlanPath = "/v2/operational/print-plan"

// Tabel yang perubahannya mengubah rencana cetak tablet ini; dimuat ulang lewat /v2/live.
internal val PrintPlanTables = setOf(
    "device_stations",
    "device_station_prints",
    "category_stations",
    "category_branch_stations",
    "stations",
    "devices",
)

/** Mode tablet: Mode Kasir mencetak struk menu dari tablet ini saat pesanan dibuat tanpa Papan Stasiun; Mode Stasiun mengerjakan stasiunnya di tablet. */
internal enum class TabletMode(val code: String) {
    Cashier("cashier"),
    Station("station");

    companion object {
        // Mode yang tidak dikenal (server lama) diperlakukan Mode Stasiun, yaitu perilaku sebelum mode ada.
        fun of(code: String) = entries.firstOrNull { it.code == code } ?: Station
    }
}

/**
 * Satu stasiun yang printernya dilayani tablet ini. [held] berarti tablet ini memegang stasiunnya (layar dan printer);
 * selain itu struknya dikirim dari tablet kasir ini saat pesanan dibuat. [categoryIds] kategori menu yang dicetak ke sana;
 * [delivers] berarti stasiun pengantar yang menerima satu struk antar berisi seluruh pesanan.
 */
internal class PlanStation(val id: String, val name: String, val held: Boolean, val categoryIds: Set<String>, val delivers: Boolean = false) {
    val slot: PrinterSlot get() = PrinterSlot.station(id)
}

/** Yang dicetak tablet ini: struk pembayaran bila memegang Kasir, dan satu printer per stasiun pada daftar. */
internal class PrintPlan(
    val receipt: Boolean,
    val stations: List<PlanStation>,
    /** Stasiun tujuan pemasangan lama Bar dan Dapur; null bila tidak pasti, sehingga pengguna memasang ulang. */
    val legacyBarStationId: String?,
    val legacyKitchenStationId: String?,
    val mode: TabletMode = TabletMode.Station,
) {
    /** Slot yang harus terpasang di tablet ini, dalam urutan tampil. */
    val slots: List<PrinterSlot> get() = (if (receipt) listOf(PrinterSlot.Receipt) else emptyList()) + stations.map { it.slot }

    fun station(stationId: String): PlanStation? = stations.firstOrNull { it.id == stationId }

    /** Stasiun tanpa tablet yang menerima struk menu berkategori [categoryId] dari kasir ini; null berarti tidak dicetak di sini. */
    fun sentFromHere(categoryId: String?): PlanStation? =
        categoryId?.let { category -> stations.firstOrNull { !it.held && category in it.categoryIds } }

    /** Tablet ini sendiri yang mencetak struk pesanan stasiun [stationId] saat menunya selesai. */
    fun printsAtStation(stationId: String): Boolean = stations.any { it.id == stationId && it.held }

    companion object {
        /** Sebelum rencana pertama terbaca: tidak ada yang dicetak dan tidak ada peringatan palsu. */
        val Empty = PrintPlan(receipt = false, stations = emptyList(), legacyBarStationId = null, legacyKitchenStationId = null)
    }
}

@Serializable
internal class PlanStationDto(
    @SerialName("station_id") val stationId: String,
    val name: String,
    val held: Boolean = false,
    @SerialName("category_ids") val categoryIds: List<String> = emptyList(),
    val kind: String = MakeKind,
)

@Serializable
internal class PrintPlanDto(
    val receipt: Boolean = false,
    val stations: List<PlanStationDto> = emptyList(),
    @SerialName("legacy_bar_station_id") val legacyBarStationId: String? = null,
    @SerialName("legacy_kitchen_station_id") val legacyKitchenStationId: String? = null,
    val mode: String = TabletMode.Station.code,
) {
    fun toModel() = PrintPlan(
        receipt = receipt,
        stations = stations.map { PlanStation(it.stationId, it.name, it.held, it.categoryIds.toSet(), delivers = it.kind == DeliverKind) },
        legacyBarStationId = legacyBarStationId,
        legacyKitchenStationId = legacyKitchenStationId,
        mode = TabletMode.of(mode),
    )
}

private const val MakeKind = "make"
private const val DeliverKind = "deliver"

internal class PrintPlanRepository(private val api: AdminApi) {
    suspend fun plan(): DeviceResult<PrintPlan> = api.get(PrintPlanPath, PrintPlanDto.serializer()).map { it.toModel() }
}

/**
 * Memindah sekali pemasangan peran lama ke slot stasiunnya: Bar dan Dapur ke stasiun yang ditunjuk server, Printer Stasiun
 * ke satu-satunya stasiun yang dipegang tablet ini. Yang tujuannya tidak pasti dibiarkan supaya pengguna memasang ulang.
 */
internal fun adoptLegacyPrinters(printers: ThermalPrinters, plan: PrintPlan) {
    plan.legacyBarStationId?.let { printers.move(PrinterSlot.LegacyBar, PrinterSlot.station(it)) }
    plan.legacyKitchenStationId?.let { printers.move(PrinterSlot.LegacyKitchen, PrinterSlot.station(it)) }
    plan.stations.singleOrNull { it.held }?.let { printers.move(PrinterSlot.LegacyStation, it.slot) }
}
