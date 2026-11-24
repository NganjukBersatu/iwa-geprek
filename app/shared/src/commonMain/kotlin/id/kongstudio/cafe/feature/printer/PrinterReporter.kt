package id.kongstudio.cafe.feature.printer

import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlin.time.TimeMark
import kotlin.time.TimeSource
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

internal const val PrinterReportPath = "/v2/operational/printer-report"

// Menunggu sambungan tenang dulu supaya putus-sambung sesaat tidak terkirim sebagai dua laporan.
private val SettleDelay = 3.seconds
private val MinReportGap = 60.seconds
private val RetryDelay = 15_000.milliseconds
private const val MaxAttempts = 3

/** Satu printer yang terpasang di tablet ini seperti dilaporkan ke server; [stationId] terisi untuk printer stasiun. */
internal data class ReportedPrinter(val slot: String, val stationId: String?, val name: String, val address: String, val connected: Boolean)

private const val ReceiptCode = "receipt"
private const val StationCode = "station"
private const val BarCode = "bar"
private const val KitchenCode = "kitchen"

/** Kode slot di server; peran lama yang belum dipindah tetap dilaporkan dengan kodenya supaya web masih bisa memetakannya. */
private fun PrinterSlot.reported(): Pair<String, String?> = when {
    this == PrinterSlot.Receipt -> ReceiptCode to null
    stationId != null -> StationCode to stationId
    this == PrinterSlot.LegacyBar -> BarCode to null
    this == PrinterSlot.LegacyKitchen -> KitchenCode to null
    else -> StationCode to null
}

internal class PrinterReportRepository(private val api: AdminApi) {
    suspend fun report(printers: List<ReportedPrinter>): DeviceResult<Unit> =
        api.sendUnit(
            method = HttpMethod.Put,
            path = PrinterReportPath,
            body = buildJsonObject {
                putJsonArray("printers") {
                    printers.forEach { printer ->
                        add(
                            buildJsonObject {
                                put("printer_slot", printer.slot)
                                printer.stationId?.let { put("station_id", it) }
                                put("printer_name", printer.name.ifBlank { printer.address })
                                put("printer_address", printer.address)
                                put("connection", JsonPrimitive(if (printer.connected) "connected" else "disconnected"))
                            },
                        )
                    }
                }
            },
        )
}

/** Melaporkan printer tablet ke server saat dipasang, diganti, dilepas, atau sambungannya berubah, paling sering sekali per menit. */
internal class PrinterReporter(
    private val repository: PrinterReportRepository,
    private val printers: ThermalPrinters,
) {
    suspend fun run() {
        var sent: List<ReportedPrinter>? = null
        var sentAt: TimeMark? = null
        snapshots().collectLatest { snapshot ->
            if (snapshot == sent) return@collectLatest
            sentAt?.let { mark -> wait(MinReportGap - mark.elapsedNow()) }
            repeat(MaxAttempts) { attempt ->
                when (val result = repository.report(snapshot)) {
                    is DeviceResult.Ok -> {
                        sent = snapshot
                        sentAt = TimeSource.Monotonic.markNow()
                        return@collectLatest
                    }
                    is DeviceResult.Failed -> {
                        // Token ditolak diurus layar lain; laporan berikutnya dikirim saat karyawan masuk lagi.
                        if (result.failure == AppFailure.Unauthorized) return@collectLatest
                        if (attempt < MaxAttempts - 1) delay(RetryDelay * (attempt + 1))
                    }
                }
            }
        }
    }

    // Selama ada printer yang sedang menyambung, keadaannya belum pasti, jadi tidak dilaporkan.
    @OptIn(kotlinx.coroutines.FlowPreview::class)
    private fun snapshots(): Flow<List<ReportedPrinter>> =
        combine(printers.paired, printers.links) { paired, links ->
            if (paired.keys.any { links[it] == PrinterLink.Connecting }) {
                null
            } else {
                paired.entries.sortedBy { it.key.key }.map { (slot, printer) ->
                    val (code, stationId) = slot.reported()
                    ReportedPrinter(code, stationId, printer.name, printer.address, links[slot] == PrinterLink.Ready)
                }
            }
        }.filterNotNull().distinctUntilChanged().debounce(SettleDelay)

    private suspend fun wait(duration: Duration) {
        if (duration.isPositive()) delay(duration)
    }
}
