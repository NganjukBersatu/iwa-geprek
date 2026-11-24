package id.kongstudio.cafe.feature.cashier

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.core.time.ShiftDay
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.network.LiveChange
import id.kongstudio.cafe.feature.printer.PairedPrinter
import id.kongstudio.cafe.feature.printer.PrinterLink
import id.kongstudio.cafe.feature.openbill.OpenBillRepository
import id.kongstudio.cafe.feature.stationboard.CashierOrder
import id.kongstudio.cafe.feature.printer.PrintPlan
import id.kongstudio.cafe.feature.printer.PrinterSlot
import id.kongstudio.cafe.feature.printer.adoptLegacyPrinters
import id.kongstudio.cafe.feature.printer.ThermalPrinters
import androidx.compose.runtime.snapshotFlow
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

// Jeda setelah ketikan terakhir sebelum mencari pelanggan, supaya satu nama tidak menjadi satu panggilan per huruf.
private const val SuggestionDelayMillis = 250L

/** Hasil menyimpan bill atau menambah menunya: [added] membedakan keduanya untuk teks pemberitahuan. */
internal class BillNotice(val receipt: String?, val added: Boolean)

internal data class CashierUiState(
    val loading: Boolean = true,
    /** Sebab katalog gagal dimuat; null bila lancar. */
    val failure: AppFailure? = null,
    val items: List<CashierItem> = emptyList(),
    /** Id menu terlaris menurut server, urut dari yang paling laku. */
    val bestsellerIds: List<String> = emptyList(),
    /** Tab kategori pilihan kasir; dipakai bersama oleh sidebar dan daftar menu. */
    val category: String = TabBestseller,
    /** Karyawan yang login punya shift aktif; tanpa itu server menolak transaksi. */
    val shiftOpen: Boolean = true,
    val methods: List<PaymentMethod> = emptyList(),
    val visitors: VisitorChoices = VisitorChoices(),
    /** Promo yang belum berakhir, urut menurut server. */
    val promos: List<CashierPromo> = emptyList(),
    /** Promo pilihan kasir untuk pesanan ini; null berarti mengikuti promo otomatis. */
    val promoId: String? = null,
    /** Kasir memilih "Tanpa promo", jadi promo otomatis tidak dipasang di pesanan ini. */
    val promoOff: Boolean = false,
    val takeAway: Boolean = false,
    val customerName: String = "",
    /** Pelanggan terdaftar yang dipilih dari saran; mengetik ulang nama melepasnya, jadi pesanan kembali tanpa pelanggan terdaftar. */
    val customerId: String? = null,
    val customerSuggestions: List<CustomerSuggestion> = emptyList(),
    /** Saran pelanggan gagal dibaca; kasir tetap bisa mengetik nama bebas. */
    val suggestionFailure: AppFailure? = null,
    val tableNo: String = "",
    val visitorCategoryId: String? = null,
    val visitorGenderId: String? = null,
    val notes: List<OrderNote> = emptyList(),
    val noteId: String? = null,
    /** Sebab catatan baru gagal ditambahkan; null bila lancar. */
    val noteFailure: AppFailure? = null,
    val submitting: Boolean = false,
    val submitFailure: AppFailure? = null,
    /** Bill sedang disimpan atau ditambah menunya; layar tidak menerima ketukan kedua. */
    val savingBill: Boolean = false,
    /** Bill yang baru disimpan atau ditambah; ditampilkan sampai kasir menutupnya. */
    val billNotice: BillNotice? = null,
    val billFailure: AppFailure? = null,
    /** Bill yang sedang ditambah menunya; null berarti keranjang ini pesanan baru. */
    val addingTo: CashierOrder? = null,
    /** Ada data pendukung yang gagal dimuat; penjualan tetap jalan dan kasir diberi tahu. */
    val incomplete: Boolean = false,
    /** Keranjang diisi dari simpanan saat dibuka; kasir diminta memeriksa isinya. */
    val cartRestored: Boolean = false,
    /** Pesanan yang baru tersimpan; ditampilkan sampai kasir menutupnya. */
    val placed: PlacedOrder? = null,
    /** Metode bayar pesanan yang baru tersimpan; menentukan warna dan isi layar sukses. */
    val placedMethod: PaymentMethod? = null,
    val shop: ShopInfo = ShopInfo("", "", "", ""),
    /** Rencana cetak tablet ini; null sampai terbaca pertama kali (dari server atau simpanan offline). */
    val printPlan: PrintPlan? = null,
    /** Pesanan terakhir dalam bentuk cetak; dipakai untuk cetak ulang bila ada printer yang gagal. */
    val printable: PrintableOrder? = null,
    val printing: Boolean = false,
    val printReport: PrintReport? = null,
    /** Nomor nota yang direbut saat layar bayar dibuka, supaya tiket dapur/bar dan struk sama. */
    val paymentReceipt: String? = null,
    /** Nomor nota gagal direbut saat layar bayar dibuka; tiket dicetak tanpa nomor dan server memberi nomor saat pesanan diterima. */
    val receiptFailure: AppFailure? = null,
    val ticketPrinting: Boolean = false,
    /** Tiket dapur/bar pesanan ini sudah dicetak dari layar bayar, jadi setelah bayar hanya struk yang dicetak. */
    val ticketsPrinted: Boolean = false,
    val ticketFailures: Set<PrinterSlot> = emptySet(),
) {
    /** Slot printer stasiun tanpa tablet yang tiketnya dicetak dari kasir ini. */
    val ticketSlots: Set<PrinterSlot> get() = printPlan?.stations?.filter { !it.held }?.map { it.slot }?.toSet().orEmpty()
}

internal class CashierViewModel(
    private val repository: CashierRepository,
    private val printers: ThermalPrinters,
    private val cashierName: String,
    private val onUnauthorized: () -> Unit,
    private val draft: CartDraftStore?,
    private val bills: OpenBillRepository,
    printPlanChanges: Flow<LiveChange>,
    menuChanges: Flow<LiveChange>,
    referenceChanges: Flow<LiveChange>,
) : ViewModel() {
    private val _state = MutableStateFlow(CashierUiState())
    val state: StateFlow<CashierUiState> = _state.asStateFlow()

    val cart = CartState()

    /** Printer yang terpasang dan sambungannya, untuk peringatan di keranjang. */
    val printerPaired: StateFlow<Map<PrinterSlot, PairedPrinter>> = printers.paired
    val printerLinks: StateFlow<Map<PrinterSlot, PrinterLink>> = printers.links

    /** Rencana cetak untuk layar Printer dan papan stasiun; satu sumber dengan yang dipakai kasir saat mencetak. */
    val printPlan: StateFlow<PrintPlan?> = _state.map { it.printPlan }.distinctUntilChanged().stateIn(viewModelScope, SharingStarted.Eagerly, null)

    private val _printPlanFailure = MutableStateFlow<AppFailure?>(null)

    /** Rencana cetak gagal dibaca dan belum ada simpanan; layar Printer menampilkannya dengan tombol coba lagi. */
    val printPlanFailure: StateFlow<AppFailure?> = _printPlanFailure.asStateFlow()
    private val printLock = Mutex()
    private var suggestionJob: Job? = null

    init {
        load()
        // Stasiun tablet, kategori stasiun, dan tablet stasiun baru diubah dari web; cetakan berikutnya langsung mengikuti.
        viewModelScope.launch { printPlanChanges.collect { loadPrintPlan() } }
        // Menu yang ditandai tidak tersedia, harga, atau bahan habis diubah dari web atau tablet lain; katalog kasir langsung mengikuti.
        viewModelScope.launch { menuChanges.collect { reloadMenu() } }
        // Promo, cara bayar, identitas struk, pilihan pengunjung, dan catatan pesanan diubah dari web; kasir yang sedang masuk langsung mengikuti.
        viewModelScope.launch { referenceChanges.collect { reloadReference() } }
        viewModelScope.launch { keepCartDraft() }
    }

    // Keranjang dipulihkan sekali, dibersihkan dari menu yang sudah hilang setelah katalog termuat, lalu setiap perubahannya disimpan.
    private suspend fun keepCartDraft() {
        // Tanpa identitas karyawan yang terbaca, keranjang tidak disimpan supaya tidak tercampur antarkaryawan.
        val draft = draft ?: return
        cart.restore(draft.load())
        if (!cart.isEmpty) _state.update { it.copy(cartRestored = true) }
        val catalog = _state.first { it.items.isNotEmpty() }.items
        cart.retainValid(catalog.associateBy { it.id })
        snapshotFlow { cart.entries() }.collectLatest { draft.save(it) }
    }

    // Gagal dimuat berarti data terakhir tetap dipakai; berjualan tidak terhenti.
    private suspend fun reloadReference() {
        val loaded = listOf(
            repository.paymentMethods().consume { methods -> _state.update { it.copy(methods = methods.value) } },
            repository.shopInfo().consume { shop -> _state.update { it.copy(shop = shop.value) } },
            repository.visitorChoices().consume { choices -> _state.update { it.copy(visitors = choices.value) } },
            repository.promos().consume { promos -> _state.update { it.copy(promos = promos.value) } },
            repository.orderNotes().consume { notes -> _state.update { it.copy(notes = notes.value) } },
        )
        // Pemuatan ulang yang utuh membersihkan tanda "belum lengkap" dari kegagalan sebelumnya.
        if (loaded.all { it } && _printPlanFailure.value == null) _state.update { it.copy(incomplete = false) }
    }

    // Gagal dimuat berarti katalog terakhir tetap dipakai dan server menolak menu yang tidak bisa dijual saat pesanan dikirim.
    private suspend fun reloadMenu() {
        repository.menu().consume { menu -> _state.update { it.copy(items = menu.value) } }
    }

    fun dismissRestoredNotice() {
        _state.update { it.copy(cartRestored = false) }
    }

    fun reloadPrintPlan() {
        viewModelScope.launch { loadPrintPlan() }
    }

    // Gagal dimuat berarti tetap memakai rencana terakhir yang tersimpan; berjualan tidak terhenti.
    private suspend fun loadPrintPlan() {
        when (val result = repository.printPlan()) {
            is DeviceResult.Ok -> {
                adoptLegacyPrinters(printers, result.value)
                _printPlanFailure.value = null
                _state.update { it.copy(printPlan = result.value) }
            }
            is DeviceResult.Failed -> {
                if (fail(result.failure)) return
                _printPlanFailure.value = result.failure
                _state.update { it.copy(incomplete = true) }
            }
        }
    }

    fun load() {
        _state.update { it.copy(loading = true, failure = null, incomplete = false) }
        viewModelScope.launch {
            when (val menu = repository.menu()) {
                is DeviceResult.Failed -> {
                    if (fail(menu.failure)) return@launch
                    _state.update { it.copy(loading = false, failure = menu.failure) }
                    return@launch
                }
                is DeviceResult.Ok -> _state.update { it.copy(items = menu.value) }
            }
            // Tanpa daftar terlaris tab itu hanya tidak tampil; berjualan tetap jalan.
            when (val best = repository.bestsellerIds()) {
                is DeviceResult.Ok -> _state.update { it.copy(bestsellerIds = best.value) }
                is DeviceResult.Failed -> if (fail(best.failure)) return@launch
            }
            when (val shift = repository.activeShift()) {
                is DeviceResult.Ok -> follow(shift.value)
                is DeviceResult.Failed -> if (fail(shift.failure)) return@launch
            }
            // Bahan struk dan data pendukung tidak menghalangi berjualan; bila gagal dimuat, yang terakhir tersimpan dipakai.
            reloadReference()
            loadPrintPlan()
            _state.update { it.copy(loading = false) }
        }
    }

    /** Dipanggil setelah sesi dibuka atau ditutup supaya tombol bayar mengikuti. */
    fun refreshShift() {
        viewModelScope.launch {
            repository.activeShift().consume { shift -> follow(shift.value) }
        }
    }

    private fun follow(shift: ShiftDay) {
        BusinessDay.follow(shift)
        _state.update { it.copy(shiftOpen = shift is ShiftDay.Running) }
    }

    fun selectCategory(tab: String) = _state.update { it.copy(category = tab) }

    fun setTakeAway(value: Boolean) = _state.update { it.copy(takeAway = value) }

    fun setCustomerName(value: String) {
        _state.update { it.copy(customerName = value, customerId = null) }
        suggestionJob?.cancel()
        val query = value.trim()
        if (query.isEmpty()) {
            _state.update { it.copy(customerSuggestions = emptyList(), suggestionFailure = null) }
            return
        }
        suggestionJob = viewModelScope.launch {
            delay(SuggestionDelayMillis)
            // Saran hanya bantuan: gagal dikabarkan di bawah isian, kasir tetap bisa mengetik bebas seperti tamu biasa.
            when (val result = repository.customerSuggestions(query)) {
                is DeviceResult.Ok -> _state.update { it.copy(customerSuggestions = result.value, suggestionFailure = null) }
                is DeviceResult.Failed -> _state.update { it.copy(customerSuggestions = emptyList(), suggestionFailure = result.failure) }
            }
        }
    }

    fun pickCustomer(customer: CustomerSuggestion) {
        suggestionJob?.cancel()
        _state.update { it.copy(customerName = customer.name, customerId = customer.id, customerSuggestions = emptyList(), suggestionFailure = null) }
    }

    /** Kategori yang tidak menanyakan gender ikut mengosongkan gender yang sudah dipilih. */
    fun chooseVisitorCategory(id: String?) = _state.update { current ->
        val asksGender = current.visitors.categories.firstOrNull { it.id == id }?.asksGender == true
        current.copy(visitorCategoryId = id, visitorGenderId = current.visitorGenderId.takeIf { asksGender })
    }

    fun chooseVisitorGender(id: String?) = _state.update { it.copy(visitorGenderId = id) }

    fun chooseNote(id: String?) = _state.update { it.copy(noteId = id, noteFailure = null) }

    fun addNote(name: String) {
        viewModelScope.launch {
            when (val added = repository.addOrderNote(name)) {
                is DeviceResult.Ok -> _state.update { current ->
                    val notes = (current.notes.filterNot { it.id == added.value.id } + added.value).sortedBy { it.name.lowercase() }
                    current.copy(notes = notes, noteId = added.value.id, noteFailure = null)
                }
                is DeviceResult.Failed -> {
                    if (fail(added.failure)) return@launch
                    _state.update { it.copy(noteFailure = added.failure) }
                }
            }
        }
    }

    fun setTableNo(value: String) = _state.update { it.copy(tableNo = value) }

    /** [promoId] null berarti "Tanpa promo". */
    fun choosePromo(promoId: String?) = _state.update { it.copy(promoId = promoId, promoOff = promoId == null) }

    fun clearOrder() {
        cart.clear()
        _state.update { it.copy(submitFailure = null, promoId = null, promoOff = false).withoutIdentity() }
    }

    /** Identitas pesanan kembali kosong untuk pesanan berikutnya. */
    private fun CashierUiState.withoutIdentity() = copy(
        customerName = "",
        customerId = null,
        customerSuggestions = emptyList(),
        suggestionFailure = null,
        tableNo = "",
        visitorCategoryId = null,
        visitorGenderId = null,
        noteId = null,
        noteFailure = null,
    )

    fun dismissPlaced() = _state.update { it.copy(placed = null) }

    fun dismissBillNotice() = _state.update { it.copy(billNotice = null, billFailure = null) }

    /** Menu yang dipilih berikutnya masuk ke bill ini, bukan pesanan baru; keranjang yang sudah terisi ikut tertambah. */
    fun startAdding(bill: CashierOrder) = _state.update { it.copy(addingTo = bill, billFailure = null, billNotice = null) }

    fun cancelAdding() = _state.update { it.copy(addingTo = null, billFailure = null) }

    /** Tiket stasiun saja; struk dicetak saat bill dibayar. */
    private fun ticketSlots(order: PrintableOrder): Set<PrinterSlot> = reprintSlots(order).filter { it != PrinterSlot.Receipt }.toSet()

    /** Menyimpan keranjang sebagai bill: dapur langsung menerimanya, pembayaran menyusul. Butuh koneksi dan tidak pernah masuk antrean offline. */
    fun saveBill() {
        val current = _state.value
        if (current.savingBill || current.submitting || cart.isEmpty) return
        _state.update { it.copy(savingBill = true, billFailure = null, billNotice = null) }
        val total = cart.lines(current.items.associateBy { it.id }).sumOf { it.subtotal }
        viewModelScope.launch {
            // Gagal merebut nomor tidak menahan bill: server memberi nomor sendiri.
            val receipt = (repository.takeReceiptNumber() as? DeviceResult.Ok)?.value
            val draft = OrderDraft(
                takeAway = current.takeAway,
                customerName = current.customerName.trim().ifEmpty { null },
                tableNo = current.tableNo.trim().ifEmpty { null },
                paymentCode = "",
                cashReceived = null,
                entries = cart.entries(),
                visitorCategoryId = current.visitorCategoryId,
                visitorGenderId = current.visitorGenderId,
                customerId = current.customerId,
                noteId = current.noteId,
                noteLabel = current.notes.firstOrNull { it.id == current.noteId }?.name,
                openBill = true,
            )
            when (val result = repository.submit(draft, total, receipt)) {
                is DeviceResult.Ok -> {
                    val printable = current.printableNow(receipt = result.value.receiptNumber, paymentLabel = "", total = result.value.total, cashReceived = null, change = 0, queued = false)
                    cart.clear()
                    _state.update {
                        it.copy(promoId = null, promoOff = false, savingBill = false, billNotice = BillNotice(result.value.receiptNumber, added = false), printable = printable, printReport = null, paymentReceipt = null, ticketsPrinted = false, ticketFailures = emptySet()).withoutIdentity()
                    }
                    print(printable, only = ticketSlots(printable))
                }
                is DeviceResult.Failed -> {
                    if (fail(result.failure)) return@launch
                    _state.update { it.copy(savingBill = false, billFailure = result.failure) }
                }
            }
        }
    }

    /** Menambahkan isi keranjang ke bill yang dipilih; dapur menerima tiket baris barunya saja. */
    fun addToBill() {
        val current = _state.value
        val bill = current.addingTo ?: return
        if (current.savingBill || cart.isEmpty) return
        _state.update { it.copy(savingBill = true, billFailure = null, billNotice = null) }
        viewModelScope.launch {
            when (val result = bills.addMenus(bill, cart.entries())) {
                is DeviceResult.Ok -> {
                    val printable = current.printableNow(receipt = bill.receipt, paymentLabel = "", total = result.value.total, cashReceived = null, change = 0, queued = false)
                    cart.clear()
                    _state.update {
                        it.copy(savingBill = false, addingTo = null, billNotice = BillNotice(bill.receipt, added = true), printable = printable, printReport = null).withoutIdentity()
                    }
                    print(printable, only = ticketSlots(printable))
                }
                is DeviceResult.Failed -> {
                    if (fail(result.failure)) return@launch
                    // Bill yang berubah dari tablet lain dibaca ulang, supaya percobaan berikutnya membawa versi terbaru.
                    val fresh = (bills.bills() as? DeviceResult.Ok)?.value?.firstOrNull { it.id == bill.id }
                    _state.update { it.copy(savingBill = false, billFailure = result.failure, addingTo = fresh ?: it.addingTo) }
                }
            }
        }
    }

    fun clearSubmitFailure() = _state.update { it.copy(submitFailure = null) }

    /** Layar bayar dibuka: tiket lama dilupakan dan nomor nota direbut sedini mungkin, karena tombol Dapur/Bar membutuhkannya. */
    fun startPayment() {
        _state.update { it.copy(submitFailure = null, paymentReceipt = null, receiptFailure = null, ticketsPrinted = false, ticketFailures = emptySet()) }
        viewModelScope.launch {
            when (val receipt = repository.takeReceiptNumber()) {
                is DeviceResult.Ok -> _state.update { it.copy(paymentReceipt = receipt.value) }
                is DeviceResult.Failed -> _state.update { it.copy(receiptFailure = receipt.failure) }
            }
        }
    }

    /** Pesanan di keranjang dalam bentuk cetak; dipakai tiket sebelum bayar dan struk sesudahnya. */
    private fun CashierUiState.printableNow(
        receipt: String?,
        paymentLabel: String,
        total: Long,
        cashReceived: Long?,
        change: Long,
        queued: Boolean,
    ): PrintableOrder {
        val cartLines = cart.lines(items.associateBy { it.id })
        val today = BusinessDay.today()
        val promo = promoFor(cartLines, today)
        val discount = promo?.discountOf(cartLines, today) ?: 0
        return PrintableOrder(
            receiptNumber = receipt,
            takeAway = takeAway,
            customerName = customerName.trim().ifEmpty { null },
            tableNo = tableNo.trim().ifEmpty { null },
            paymentLabel = paymentLabel,
            lines = cartLines.map { line ->
                PrintableLine(
                    name = line.item.name,
                    quantity = line.quantity,
                    unitPrice = line.unitPrice,
                    details = line.details,
                    note = line.note,
                    category = line.item.category,
                    categoryId = line.item.categoryId,
                    variants = line.variants,
                    extras = line.extras,
                )
            },
            promoName = promo?.name?.takeIf { discount > 0 },
            discount = discount,
            total = total,
            cashReceived = cashReceived,
            change = change,
            cashier = cashierName,
            dateText = today,
            timeText = DateTimeFormat.stampAt(ServerClock.nowEpochSeconds()).time,
            queued = queued,
            epochSeconds = ServerClock.nowEpochSeconds(),
            noteLabel = notes.firstOrNull { it.id == noteId }?.name,
        )
    }

    /** Tombol Dapur/Bar: tiket dicetak sebelum pelanggan membayar, dengan nomor nota yang nanti juga tercetak di struk. */
    fun printTickets() {
        val current = _state.value
        if (current.ticketPrinting || cart.isEmpty) return
        val order = current.printableNow(current.paymentReceipt, "", 0, null, 0, queued = false)
        _state.update { it.copy(ticketPrinting = true) }
        viewModelScope.launch {
            printLock.withLock {
                val report = printOrder(
                    printers = printers,
                    shop = _state.value.shop,
                    plan = _state.value.printPlan,
                    order = order,
                    only = _state.value.ticketSlots,
                )
                _state.update {
                    it.copy(
                        ticketPrinting = false,
                        ticketsPrinted = it.ticketsPrinted || report.printedAny,
                        ticketFailures = report.failures.keys,
                    )
                }
            }
        }
    }

    fun submit(paymentCode: String, cashReceived: Long?) {
        val current = _state.value
        if (current.submitting || cart.isEmpty) return
        _state.update { it.copy(submitting = true, submitFailure = null) }
        val cartLines = cart.lines(current.items.associateBy { it.id })
        val today = BusinessDay.today()
        val promo = current.promoFor(cartLines, today)
        val discount = promo?.discountOf(cartLines, today) ?: 0
        // Total tampilan untuk pesanan yang tertunda; server tetap menghitung ulang saat menerimanya dengan rumus yang sama.
        val localTotal = (cartLines.sumOf { it.subtotal } - discount).coerceAtLeast(0)
        val method = current.methods.firstOrNull { it.code == paymentCode }
        val paymentLabel = method?.label ?: paymentCode
        viewModelScope.launch {
            val draft = OrderDraft(
                takeAway = current.takeAway,
                customerName = current.customerName.trim().ifEmpty { null },
                tableNo = current.tableNo.trim().ifEmpty { null },
                paymentCode = paymentCode,
                cashReceived = cashReceived,
                entries = cart.entries(),
                visitorCategoryId = current.visitorCategoryId,
                visitorGenderId = current.visitorGenderId,
                promoId = promo?.id,
                customerId = current.customerId,
                noteId = current.noteId,
                noteLabel = current.notes.firstOrNull { it.id == current.noteId }?.name,
            )
            when (val result = repository.submit(draft, localTotal, current.paymentReceipt)) {
                is DeviceResult.Ok -> {
                    // Bentuk cetak disusun sebelum keranjang dikosongkan, karena sesudahnya barisnya sudah tidak ada.
                    val printable = current.printableNow(
                        receipt = result.value.receiptNumber,
                        paymentLabel = paymentLabel,
                        total = result.value.total,
                        cashReceived = cashReceived,
                        change = result.value.change,
                        queued = result.value.queued,
                    )
                    val ticketsDone = _state.value.ticketsPrinted
                    cart.clear()
                    _state.update {
                        it.copy(
                            promoId = null,
                            promoOff = false,
                            submitting = false,
                            placed = result.value,
                            placedMethod = method,
                            printable = printable,
                            printReport = null,
                            paymentReceipt = null,
                            ticketsPrinted = false,
                            ticketFailures = emptySet(),
                        ).withoutIdentity()
                    }
                    // Tiket yang sudah keluar dari tombol Dapur/Bar tidak dicetak dua kali.
                    print(printable, only = if (ticketsDone) setOf(PrinterSlot.Receipt) else null)
                }
                is DeviceResult.Failed -> {
                    if (fail(result.failure)) return@launch
                    _state.update { it.copy(submitting = false, submitFailure = result.failure) }
                }
            }
        }
    }

    /** Mencetak ulang hanya ke printer yang tadi gagal, supaya struk yang sudah keluar tidak tercetak dua kali. */
    fun reprint() {
        val state = _state.value
        val order = state.printable ?: return
        val failed = state.printReport?.failed?.takeIf { it.isNotEmpty() } ?: return
        print(order, only = failed)
    }

    /** UUID kategori menu terbaru dari katalog kasir, untuk membagi struk pesanan saat cetak ulang. */
    fun categoryOfMenu(menuId: String?): String? = menuId?.let { id -> _state.value.items.firstOrNull { it.id == id }?.categoryId }

    /** Struk yang bisa dicetak ulang: struk pembayaran, struk pesanan yang dicetak dari kasir ini, dan struk antar bila printer pengantar sudah dipasang. */
    fun reprintSlots(order: PrintableOrder): List<PrinterSlot> {
        val plan = _state.value.printPlan
        val paired = printers.paired.value
        val stations = plan?.let { ticketGroups(it, order.lines) }.orEmpty().filter { !it.first.delivers || it.first.slot in paired }.map { it.first.slot }
        return listOf(PrinterSlot.Receipt) + stations
    }

    /** Cetak ulang pesanan lama dari station Kasir ke satu printer pilihan kasir, lewat antrean cetak yang sama. */
    suspend fun reprint(order: PrintableOrder, slot: PrinterSlot): PrintReport = printLock.withLock {
        printOrder(
            printers = printers,
            shop = _state.value.shop,
            plan = _state.value.printPlan,
            order = order,
            only = setOf(slot),
        )
    }

    /** Cetakan berurutan satu per satu, supaya pesanan yang dibayar beruntun tidak saling menimpa di printer. */
    private fun print(order: PrintableOrder, only: Set<PrinterSlot>?) {
        viewModelScope.launch {
            printLock.withLock {
                _state.update { it.copy(printing = true) }
                val report = printOrder(
                    printers = printers,
                    shop = _state.value.shop,
                    plan = _state.value.printPlan,
                    order = order,
                    only = only,
                )
                _state.update { current ->
                    // Laporan hanya milik pesanan yang sedang ditampilkan; cetakan pesanan lama tidak menimpanya.
                    current.copy(printing = false, printReport = if (current.printable === order) report else current.printReport)
                }
            }
        }
    }

    /** Hasil baca opsional: yang berhasil dipakai, yang gagal ditandai supaya kasir tahu datanya bisa belum lengkap. */
    private fun <T> DeviceResult<T>.consume(onOk: (DeviceResult.Ok<T>) -> Unit): Boolean = when (this) {
        is DeviceResult.Ok -> {
            onOk(this)
            true
        }
        is DeviceResult.Failed -> {
            if (!fail(failure)) _state.update { it.copy(incomplete = true) }
            false
        }
    }

    /** True bila token karyawan ditolak: perangkat meminta pindai ulang dan proses dihentikan. */
    private fun fail(failure: AppFailure): Boolean {
        if (failure != AppFailure.Unauthorized) return false
        onUnauthorized()
        return true
    }
}
