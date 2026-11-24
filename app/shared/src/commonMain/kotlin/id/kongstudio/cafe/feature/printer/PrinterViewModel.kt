package id.kongstudio.cafe.feature.printer

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Hasil tindakan terakhir untuk satu slot, ditampilkan di kartunya sampai tindakan berikutnya. */
internal sealed interface PrinterNotice {
    data object TestPrinted : PrinterNotice

    data class Failed(val outcome: PrintOutcome) : PrinterNotice

    data object NothingFound : PrinterNotice

    data object ScanNoPermission : PrinterNotice

    data object ScanBluetoothOff : PrinterNotice

    /** Kertas uji berlogo sudah keluar; menunggu orang memastikan struk dan logonya utuh. */
    data object LogoCheck : PrinterNotice

    /** Struk dan logo tercetak utuh: struk berikutnya memanggil logo dari memori printer. */
    data object LogoStored : PrinterNotice

    /** Logo tidak tercetak benar: struk dicetak tanpa logo. */
    data object LogoOff : PrinterNotice
}

internal data class PrinterUiState(
    /** Slot yang sedang mencari, menyambung, atau mencetak uji; kartu lain tetap bisa dipakai. */
    val busy: PrinterSlot? = null,
    /** Hasil pencarian untuk slot yang sedang dipasang; null bila lembar pilihan tidak tampil. */
    val picking: PrinterSlot? = null,
    val found: List<DiscoveredPrinter> = emptyList(),
    val notices: Map<PrinterSlot, PrinterNotice> = emptyMap(),
)

private const val LogoWriteMillis = 1_500L

/**
 * Layar Printer: memasang printer per slot dari rencana cetak, lalu satu kertas uji yang sekaligus menyimpan logo struk,
 * dan menyalakan Jaga sambungan begitu ada printer terpasang. [testPage] menyusun kertas uji dari nama slot, kertas, dan logo.
 */
internal class PrinterViewModel(
    private val printers: ThermalPrinters,
    val plan: StateFlow<PrintPlan?>,
    val planFailure: StateFlow<id.kongstudio.cafe.core.failure.AppFailure?>,
    val onRetryPlan: () -> Unit,
    private val testPage: (slotName: String, paper: PaperSize, logo: ByteArray?) -> ByteArray,
) : ViewModel() {
    val paired: StateFlow<Map<PrinterSlot, PairedPrinter>> = printers.paired
    val links: StateFlow<Map<PrinterSlot, PrinterLink>> = printers.links
    val keepAlive: StateFlow<Boolean> = printers.keepAlive

    private val _state = MutableStateFlow(PrinterUiState())
    val state: StateFlow<PrinterUiState> = _state.asStateFlow()

    init {
        // Layar dibuka: sambungkan ulang semua printer tersimpan agar statusnya jujur dan siap cetak.
        viewModelScope.launch {
            printers.paired.value.keys.forEach { printers.reconnect(it) }
        }
    }

    fun search(slot: PrinterSlot) {
        if (_state.value.busy != null) return
        _state.update { it.copy(busy = slot, notices = it.notices - slot) }
        viewModelScope.launch {
            when (val result = printers.scan()) {
                is ScanOutcome.Found -> {
                    if (result.printers.isEmpty()) {
                        finish(slot, PrinterNotice.NothingFound)
                    } else {
                        _state.update { it.copy(busy = null, picking = slot, found = result.printers) }
                    }
                }
                ScanOutcome.NoPermission -> finish(slot, PrinterNotice.ScanNoPermission)
                ScanOutcome.BluetoothOff -> finish(slot, PrinterNotice.ScanBluetoothOff)
            }
        }
    }

    fun dismissPicker() = _state.update { it.copy(picking = null, found = emptyList()) }

    /** Memasang printer pilihan, menyalakan Jaga sambungan bila belum, lalu langsung mencetak satu kertas uji. */
    fun pair(device: DiscoveredPrinter, slotName: String) {
        val slot = _state.value.picking ?: return
        _state.update { it.copy(picking = null, found = emptyList(), busy = slot) }
        viewModelScope.launch {
            val outcome = printers.pair(slot, device)
            if (outcome != PrintOutcome.Ok) {
                finish(slot, PrinterNotice.Failed(outcome))
                return@launch
            }
            if (!printers.keepAlive.value) printers.setKeepAlive(true)
            runCheck(slot, slotName)
        }
    }

    /** Cetak uji ulang; untuk struk pembayaran sekaligus menyimpan ulang logo dan menanyakan hasilnya lagi. */
    fun check(slot: PrinterSlot, slotName: String) {
        if (_state.value.busy != null) return
        _state.update { it.copy(busy = slot, notices = it.notices - slot) }
        viewModelScope.launch { runCheck(slot, slotName) }
    }

    // Hanya struk pembayaran yang berlogo; printer stasiun cukup mencetak kertas uji teks.
    private suspend fun runCheck(slot: PrinterSlot, slotName: String) {
        val paper = printers.paired.value[slot]?.paper ?: PaperSize.Mm80
        if (slot != PrinterSlot.Receipt) {
            val tested = printers.print(slot, testPage(slotName, paper, null))
            finish(slot, if (tested == PrintOutcome.Ok) PrinterNotice.TestPrinted else PrinterNotice.Failed(tested))
            return
        }
        val define = ReceiptLogo.define()
        val saved = define?.let { printers.print(slot, it) } ?: PrintOutcome.Interrupted
        if (saved != PrintOutcome.Ok) {
            finish(slot, PrinterNotice.Failed(saved))
            return
        }
        // Printer menulis ke memori tetapnya dulu; perintah cetak yang datang terlalu cepat bisa terbuang.
        delay(LogoWriteMillis)
        val tested = printers.print(slot, testPage(slotName, paper, ReceiptLogo.stored))
        finish(slot, if (tested == PrintOutcome.Ok) PrinterNotice.LogoCheck else PrinterNotice.Failed(tested))
    }

    /** Jawaban "Struk dan logo tercetak utuh?": ya memakai logo tersimpan, tidak mencetak struk tanpa logo. */
    fun confirmLogo(printedRight: Boolean) {
        val slot = PrinterSlot.Receipt
        printers.setLogoVersion(slot, if (printedRight) ReceiptLogo.Version else null)
        printers.setLogoOff(slot, !printedRight)
        _state.update { it.copy(notices = it.notices + (slot to if (printedRight) PrinterNotice.LogoStored else PrinterNotice.LogoOff)) }
    }

    fun forget(slot: PrinterSlot) {
        viewModelScope.launch {
            printers.forget(slot)
            _state.update { it.copy(notices = it.notices - slot) }
        }
    }

    fun setPaper(slot: PrinterSlot, paper: PaperSize) = printers.setPaper(slot, paper)

    fun setKeepAlive(enabled: Boolean) {
        viewModelScope.launch { printers.setKeepAlive(enabled) }
    }

    private fun finish(slot: PrinterSlot, value: PrinterNotice) =
        _state.update { it.copy(busy = null, notices = it.notices + (slot to value)) }
}
