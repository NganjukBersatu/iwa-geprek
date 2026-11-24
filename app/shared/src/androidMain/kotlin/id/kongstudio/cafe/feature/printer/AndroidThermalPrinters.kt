package id.kongstudio.cafe.feature.printer

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.BluetoothStatusCodes
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.ComponentActivity
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import java.util.UUID
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withTimeoutOrNull

private const val ScanMillis = 6_000L
private const val ConnectTimeoutMillis = 12_000L
private const val DiscoverTimeoutMillis = 8_000L
private const val MtuTimeoutMillis = 2_000L
private const val WriteTimeoutMillis = 3_000L
private const val BusyRetryMillis = 10L
private const val BusyWaitMillis = 3_000L
// Batas kecepatan untuk printer yang hanya menerima kirim tanpa jawaban, di bawah kecepatan cetak printer termal 58/80 mm.
private const val NoResponseBytesPerSecond = 2_048L
private const val MillisPerSecond = 1_000L
private const val ConnectAttempts = 2
private const val RetryPauseMillis = 600L
private const val RequestedMtu = 185
private const val AttOverhead = 3
private const val MinChunk = 20
private const val MaxChunk = 180

/** Jeda penyambungan ulang setelah putus: cepat di awal, lalu melambat supaya baterai printer tidak terkuras. */
private val ReconnectBackoffMillis = longArrayOf(1_000, 3_000, 10_000, 30_000, 60_000)

// Layanan bawaan Bluetooth (akses umum, atribut, info perangkat, baterai) tidak pernah menerima data cetak.
private val StandardServices = setOf("1800", "1801", "180a", "180f").map(::shortUuid).toSet()

// Layanan cetak yang dipakai printer termal umum; didahulukan bila printer punya beberapa jalur tulis.
private val PrinterServices = listOf(
    shortUuid("18f0"),
    shortUuid("ff00"),
    UUID.fromString("e7810a71-73ae-499d-8c15-faa9aef0c3f2"),
    UUID.fromString("49535343-fe7d-4ae5-8fa9-9fafd205e455"),
)

private fun shortUuid(hex: String): UUID = UUID.fromString("0000$hex-0000-1000-8000-00805f9b34fb")

/** Hasil satu upaya sambung: siap, gagal (bisa dicoba lagi), atau perangkatnya memang bukan printer. */
internal enum class Connection { Ready, Failed, NotAPrinter }

private fun Connection.asFailure(): PrintOutcome =
    if (this == Connection.NotAPrinter) PrintOutcome.NotAPrinter else PrintOutcome.Unreachable

/**
 * Printer termal BLE (ESC/POS) satu untuk seluruh umur aplikasi: tetap tersambung, disambung ulang sendiri bila putus,
 * dan setiap slot selalu ke alamat printernya sendiri.
 */
@SuppressLint("MissingPermission")
class AndroidThermalPrinters private constructor(context: Context) : ThermalPrinters {
    private val context = context.applicationContext
    private val store = PrinterStore(this.context)
    private val adapter: BluetoothAdapter? =
        (this.context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter
    // Kegagalan penyambungan di belakang tidak boleh menutup aplikasi; upaya berikutnya tinggal mencoba lagi.
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default + CoroutineExceptionHandler { _, _ -> })
    private val storeLock = Any()
    // Harus di atas _links: linkOf() membaca keduanya saat _links diisi, dan dengan printer tersimpan
    // sessions yang belum terisi membuat aplikasi tertutup setiap kali dibuka.
    private val sessions = HashMap<String, Session>()

    // Selama memasang, status slot mengikuti printer yang sedang dicoba, bukan printer lamanya atau "belum dipasang".
    @Volatile
    private var pairing: Pair<PrinterSlot, String>? = null

    @Volatile
    private var stored: Map<PrinterSlot, StoredPrinter> = store.load()
    private val _paired = MutableStateFlow(stored.toPaired())
    override val paired: StateFlow<Map<PrinterSlot, PairedPrinter>> = _paired.asStateFlow()

    private val _links = MutableStateFlow(currentLinks())
    override val links: StateFlow<Map<PrinterSlot, PrinterLink>> = _links.asStateFlow()

    private val _keepAlive = MutableStateFlow(store.loadKeepAlive())
    override val keepAlive: StateFlow<Boolean> = _keepAlive.asStateFlow()

    private var permissionLauncher: ActivityResultLauncher<Array<String>>? = null
    private var permissionOwner: ComponentActivity? = null
    private var permissionWaiting: CompletableDeferred<Unit>? = null

    private val bluetoothState = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.getIntExtra(BluetoothAdapter.EXTRA_STATE, BluetoothAdapter.ERROR)) {
                BluetoothAdapter.STATE_ON -> keepAllConnected()
                BluetoothAdapter.STATE_TURNING_OFF, BluetoothAdapter.STATE_OFF -> allSessions().forEach { it.pause() }
            }
        }
    }

    init {
        ContextCompat.registerReceiver(
            this.context,
            bluetoothState,
            IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED),
            ContextCompat.RECEIVER_NOT_EXPORTED,
        )
        keepAllConnected()
    }

    /** Dipanggil di onCreate tiap Activity; hanya peluncur izinnya yang ikut Activity, sambungan tidak. */
    fun attach(activity: ComponentActivity) {
        permissionOwner = activity
        permissionLauncher = activity.registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
            permissionWaiting?.complete(Unit)
            keepAllConnected()
            syncKeepAlive()
        }
        keepAllConnected()
        syncKeepAlive()
    }

    /** Dipanggil di onDestroy Activity; sambungan printer tetap hidup untuk Activity berikutnya. */
    fun detach(activity: ComponentActivity) {
        if (permissionOwner !== activity) return
        permissionOwner = null
        permissionLauncher = null
        permissionWaiting?.complete(Unit)
    }

    override suspend fun scan(): ScanOutcome {
        if (!ensurePermission()) return ScanOutcome.NoPermission
        val bluetooth = adapter?.takeIf { it.isEnabled } ?: return ScanOutcome.BluetoothOff
        val scanner = bluetooth.bluetoothLeScanner ?: return ScanOutcome.BluetoothOff

        val found = LinkedHashMap<String, DiscoveredPrinter>()
        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                val address = result.device.address
                val name = result.scanRecord?.deviceName ?: result.device.name
                // Perangkat tanpa nama hampir selalu bukan printer; menampilkannya hanya membuat daftar ramai.
                if (name != null) found[address] = DiscoveredPrinter(name, address)
            }
        }
        scanner.startScan(callback)
        try {
            delay(ScanMillis)
        } finally {
            scanner.stopScan(callback)
        }
        return ScanOutcome.Found(found.values.toList())
    }

    override suspend fun pair(slot: PrinterSlot, device: DiscoveredPrinter): PrintOutcome {
        if (!ensurePermission()) return PrintOutcome.NoPermission
        if (adapter?.isEnabled != true) return PrintOutcome.BluetoothOff

        val address = device.address.uppercase()
        val session = sessionFor(address)
        pairing = slot to address
        refreshLinks()
        val connection = try {
            session.lock.withLock { session.connectLocked() }
        } finally {
            pairing = null
        }
        if (connection != Connection.Ready) {
            if (stored[slot]?.address != address) releaseUnused()
            refreshLinks()
            return connection.asFailure()
        }
        val previous = stored[slot]
        val paper = previous?.paper ?: PaperSize.Mm80.name
        update(slot, StoredPrinter(name = device.name, address = address, paper = paper))
        releaseUnused()
        return PrintOutcome.Ok
    }

    override suspend fun forget(slot: PrinterSlot) {
        update(slot, null)
        releaseUnused()
    }

    override fun move(from: PrinterSlot, to: PrinterSlot) {
        val moved = synchronized(storeLock) {
            val printer = stored[from] ?: return
            // Slot tujuan yang sudah dipasang tidak ditimpa; pemasangan lama cukup dilepas.
            stored = if (to in stored) stored - from else stored - from + (to to printer)
            store.save(stored)
            true
        }
        if (moved) {
            _paired.value = stored.toPaired()
            refreshLinks()
        }
    }

    override fun setPaper(slot: PrinterSlot, paper: PaperSize) {
        val current = stored[slot] ?: return
        update(slot, current.copy(paper = paper.name))
    }

    override fun setLogoVersion(slot: PrinterSlot, version: Int?) {
        val current = stored[slot] ?: return
        update(slot, current.copy(logoVersion = version))
    }

    override fun setLogoOff(slot: PrinterSlot, off: Boolean) {
        val current = stored[slot] ?: return
        update(slot, current.copy(logoOff = off))
    }

    override suspend fun setKeepAlive(enabled: Boolean) {
        store.saveKeepAlive(enabled)
        _keepAlive.value = enabled
        // Hanya Android 13 ke atas yang punya izin ini; ditolak pun layanannya tetap jalan, notifikasinya saja yang tersembunyi.
        if (enabled && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) ensurePermission(arrayOf(Manifest.permission.POST_NOTIFICATIONS))
        syncKeepAlive()
    }

    override suspend fun reconnect(slot: PrinterSlot): PrintOutcome = withSession(slot) { true }

    override suspend fun print(slot: PrinterSlot, data: ByteArray): PrintOutcome =
        withSession(slot) { session -> session.write(data) }

    /** Menjalankan [action] pada sambungan printer milik [slot] sendiri, dibaca ulang dari pemasangannya setiap kali. */
    private suspend fun withSession(slot: PrinterSlot, action: suspend (Session) -> Boolean): PrintOutcome {
        val address = stored[slot]?.address ?: return PrintOutcome.NotPaired
        if (!ensurePermission()) return PrintOutcome.NoPermission
        if (adapter?.isEnabled != true) return PrintOutcome.BluetoothOff

        val session = sessionFor(address)
        return session.lock.withLock {
            val connection = session.connectLocked()
            if (connection != Connection.Ready) return@withLock connection.asFailure()
            val done = try {
                action(session)
            } catch (_: SecurityException) {
                false
            }
            if (done) PrintOutcome.Ok else {
                session.dropLocked()
                PrintOutcome.Interrupted
            }
        }
    }

    private fun update(slot: PrinterSlot, printer: StoredPrinter?) {
        synchronized(storeLock) {
            stored = if (printer == null) stored - slot else stored + (slot to printer)
            store.save(stored)
        }
        _paired.value = stored.toPaired()
        refreshLinks()
        syncKeepAlive()
    }

    /** Jalur tulis yang baru terbukti berhasil disimpan untuk semua slot yang memakai printer ini. */
    private fun rememberWritePath(address: String, service: UUID, characteristic: UUID) = synchronized(storeLock) {
        val changed = stored.mapValues { (_, printer) ->
            if (printer.address == address) {
                printer.copy(serviceUuid = service.toString(), characteristicUuid = characteristic.toString())
            } else {
                printer
            }
        }
        if (changed != stored) {
            stored = changed
            store.save(stored)
        }
    }

    private fun sessionFor(address: String): Session = synchronized(sessions) {
        sessions.getOrPut(address) { Session(address) }
    }

    private fun allSessions(): List<Session> = synchronized(sessions) { sessions.values.toList() }

    /** Sambungan ke printer yang tidak lagi dipakai slot mana pun ditutup, supaya printernya bebas untuk perangkat lain. */
    private fun releaseUnused() {
        val inUse = stored.values.map { it.address }.toSet()
        val unused = synchronized(sessions) {
            sessions.keys.filter { it !in inUse }.map { sessions.remove(it)!! }
        }
        unused.forEach { it.dispose() }
        refreshLinks()
    }

    /**
     * Layanan latar hanya hidup selama pilihannya menyala, ada printer yang dipasang, dan izin Bluetooth ada; izin itu
     * juga syarat Android 14 untuk layanan tipe perangkat tersambung, jadi tanpa izin layanannya tidak pernah diminta.
     */
    internal fun wantsKeepAlive(): Boolean = _keepAlive.value && stored.isNotEmpty() && permissionsGranted()

    /** Dipanggil saat aplikasi di depan karena Android 12 ke atas melarang memulai layanan latar dari belakang, dan penolakan sistem hanya berarti layanannya tidak jalan. */
    private fun syncKeepAlive() {
        if (wantsKeepAlive()) {
            runCatching { ContextCompat.startForegroundService(context, Intent(context, PrinterKeepAliveService::class.java)) }
        } else {
            PrinterKeepAliveService.stopRunning()
        }
    }

    private fun keepAllConnected() {
        if (!permissionsGranted() || adapter?.isEnabled != true) return
        stored.values.map { it.address }.toSet().forEach { sessionFor(it).keepConnected() }
    }

    private fun linkOf(slot: PrinterSlot): PrinterLink {
        val trying = pairing?.takeIf { it.first == slot }?.second
        val address = trying ?: stored[slot]?.address ?: return PrinterLink.NotPaired
        val link = synchronized(sessions) { sessions[address] }?.link ?: PrinterLink.Offline
        return if (trying != null && link == PrinterLink.Offline) PrinterLink.Connecting else link
    }

    private fun refreshLinks() {
        _links.value = currentLinks()
    }

    // Slot tanpa pemasangan tidak dimuat; pembaca menganggap slot yang tidak ada sebagai belum dipasang.
    private fun currentLinks(): Map<PrinterSlot, PrinterLink> =
        (stored.keys + listOfNotNull(pairing?.first)).associateWith { linkOf(it) }

    private fun requiredPermissions(): Array<String> =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }

    private fun permissionsGranted(permissions: Array<String> = requiredPermissions()): Boolean = permissions.all {
        ContextCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED
    }

    /** Meminta izin hanya dari tindakan orang (cari, pasang, cetak); penyambungan di belakang tidak pernah memunculkan dialog. */
    private suspend fun ensurePermission(permissions: Array<String> = requiredPermissions()): Boolean {
        if (permissionsGranted(permissions)) return true
        val launcher = permissionLauncher ?: return false
        if (permissionWaiting != null) return false
        val waiting = CompletableDeferred<Unit>()
        permissionWaiting = waiting
        try {
            // Activity yang sedang berganti bisa menolak membuka kotak izin; itu sama dengan izin yang belum didapat.
            if (runCatching { launcher.launch(permissions) }.isFailure) return false
            waiting.await()
        } finally {
            permissionWaiting = null
        }
        return permissionsGranted(permissions)
    }

    private fun Map<PrinterSlot, StoredPrinter>.toPaired(): Map<PrinterSlot, PairedPrinter> = mapValues { (_, printer) ->
        val paper = PaperSize.entries.firstOrNull { it.name == printer.paper } ?: PaperSize.Mm80
        PairedPrinter(printer.name, printer.address, paper, printer.logoVersion, printer.logoOff)
    }

    /** Satu sambungan GATT ke satu alamat printer, dipakai bersama semua slot yang memasang printer itu. */
    private inner class Session(private val address: String) {
        val lock = Mutex()

        @Volatile
        var link: PrinterLink = PrinterLink.Offline
            private set

        @Volatile
        private var gatt: BluetoothGatt? = null
        private var characteristic: BluetoothGattCharacteristic? = null
        private var withoutResponse = false
        private var chunkSize = MinChunk
        private var connectionResult: CompletableDeferred<Boolean>? = null
        private var servicesResult: CompletableDeferred<Boolean>? = null
        private var mtuResult: CompletableDeferred<Unit>? = null
        private var writeResult: CompletableDeferred<Boolean>? = null
        private var reconnectJob: Job? = null

        @Volatile
        private var disposed = false

        private val callback = object : BluetoothGattCallback() {
            override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
                if (newState == BluetoothProfile.STATE_CONNECTED && status == BluetoothGatt.GATT_SUCCESS) {
                    connectionResult?.complete(true)
                    return
                }
                connectionResult?.complete(false)
                writeResult?.complete(false)
                // Putus dari sisi printer: objeknya ditutup di sini juga, karena Android membatasi sambungan yang terbuka.
                if (g === gatt) {
                    closeGatt()
                    setState(PrinterLink.Offline)
                    keepConnected()
                } else {
                    runCatching { g.close() }
                }
            }

            override fun onMtuChanged(g: BluetoothGatt, mtu: Int, status: Int) {
                if (status == BluetoothGatt.GATT_SUCCESS) chunkSize = (mtu - AttOverhead).coerceIn(MinChunk, MaxChunk)
                mtuResult?.complete(Unit)
            }

            override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
                servicesResult?.complete(status == BluetoothGatt.GATT_SUCCESS)
            }

            override fun onCharacteristicWrite(g: BluetoothGatt, c: BluetoothGattCharacteristic, status: Int) {
                writeResult?.complete(status == BluetoothGatt.GATT_SUCCESS)
            }
        }

        /** Menyambung bila belum, tanpa mencoba ulang perangkat yang ternyata bukan printer, dan dipanggil dengan [lock] dipegang. */
        suspend fun connectLocked(): Connection {
            if (gatt != null && characteristic != null) return Connection.Ready
            if (disposed) return Connection.Failed
            setState(PrinterLink.Connecting)
            repeat(ConnectAttempts) { attempt ->
                closeGatt()
                if (attempt > 0) delay(RetryPauseMillis)
                when (withTimeoutOrNull(ConnectTimeoutMillis) { openSafely() } ?: Connection.Failed) {
                    Connection.Ready -> {
                        setState(PrinterLink.Ready)
                        return Connection.Ready
                    }
                    Connection.NotAPrinter -> {
                        closeGatt()
                        setState(PrinterLink.Offline)
                        return Connection.NotAPrinter
                    }
                    Connection.Failed -> Unit
                }
            }
            closeGatt()
            setState(PrinterLink.Offline)
            return Connection.Failed
        }

        /** Sambungan dianggap rusak setelah gagal kirim: ditutup lalu disambung ulang di belakang; dipanggil dengan [lock] dipegang. */
        fun dropLocked() {
            closeGatt()
            setState(PrinterLink.Offline)
            keepConnected()
        }

        /** Menjaga satu upaya penyambungan di belakang selama printer masih dipasang, tanpa coba ulang berjadwal karena Android yang mengabari begitu printer kembali. */
        fun keepConnected() {
            if (disposed || reconnectJob?.isActive == true) return
            reconnectJob = scope.launch {
                var attempt = 0
                while (isActive && !disposed) {
                    if (!permissionsGranted() || adapter?.isEnabled != true) return@launch
                    // Bukan printer berarti tidak akan pernah berhasil; berhenti, bukan mengulang selamanya.
                    if (lock.withLock { connectLocked() } != Connection.Failed) return@launch
                    val pause = ReconnectBackoffMillis[attempt.coerceAtMost(ReconnectBackoffMillis.lastIndex)]
                    // Kembali pertama kali disambung seketika; yang terjangkau tetapi terus gagal baru diberi jeda.
                    if (awaitInRange()) {
                        if (attempt > 0) delay(pause)
                    } else {
                        delay(pause)
                    }
                    attempt++
                }
            }
        }

        /** Menunggu printer terjangkau lewat sambungan otomatis Android lalu langsung melepasnya untuk penyambungan biasa, dan false bila Android menolak menunggu. */
        private suspend fun awaitInRange(): Boolean {
            val device = adapter?.let { runCatching { it.getRemoteDevice(address) }.getOrNull() } ?: return false
            val back = CompletableDeferred<Unit>()
            val watcher = object : BluetoothGattCallback() {
                override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
                    if (newState == BluetoothProfile.STATE_CONNECTED) back.complete(Unit)
                }
            }
            val probe = runCatching { device.connectGatt(context, true, watcher, BluetoothDevice.TRANSPORT_LE) }.getOrNull() ?: return false
            return try {
                back.await()
                true
            } finally {
                runCatching { probe.disconnect() }
                runCatching { probe.close() }
            }
        }

        /** Bluetooth dimatikan: sambungan dilepas dan baru dicoba lagi saat Bluetooth menyala. */
        fun pause() {
            reconnectJob?.cancel()
            closeGatt()
            setState(PrinterLink.Offline)
        }

        fun dispose() {
            disposed = true
            reconnectJob?.cancel()
            closeGatt()
        }

        /** Izin Bluetooth yang dicabut di tengah jalan menjadi gagal sambung biasa, bukan aplikasi tertutup. */
        private suspend fun openSafely(): Connection = try {
            open()
        } catch (_: SecurityException) {
            Connection.Failed
        }

        private suspend fun open(): Connection {
            val bluetooth = adapter ?: return Connection.Failed
            val device = runCatching { bluetooth.getRemoteDevice(address) }.getOrNull() ?: return Connection.Failed
            val connected = CompletableDeferred<Boolean>().also { connectionResult = it }
            gatt = runCatching { device.connectGatt(context, false, callback, BluetoothDevice.TRANSPORT_LE) }.getOrNull()
                ?: return Connection.Failed
            if (!connected.await()) return Connection.Failed

            val mtu = CompletableDeferred<Unit>().also { mtuResult = it }
            if (gatt?.requestMtu(RequestedMtu) == true) withTimeoutOrNull(MtuTimeoutMillis) { mtu.await() }

            val services = CompletableDeferred<Boolean>().also { servicesResult = it }
            if (gatt?.discoverServices() != true) return Connection.Failed
            if (withTimeoutOrNull(DiscoverTimeoutMillis) { services.await() } != true) return Connection.Failed

            characteristic = findWritable(gatt ?: return Connection.Failed)
            return if (characteristic != null) Connection.Ready else Connection.NotAPrinter
        }

        /** Jalur yang pernah berhasil dipakai lebih dulu, lalu layanan cetak yang dikenal, baru jalur tulis lain. */
        private fun findWritable(g: BluetoothGatt): BluetoothGattCharacteristic? {
            val saved = stored.values.firstOrNull { it.address == address && it.characteristicUuid != null }
            if (saved != null) {
                val service = runCatching { UUID.fromString(saved.serviceUuid) }.getOrNull()
                val target = runCatching { UUID.fromString(saved.characteristicUuid) }.getOrNull()
                val found = service?.let { g.getService(it) }?.characteristics?.firstOrNull { it.uuid == target }
                if (found != null && writable(found)) return found
            }
            val candidates = g.services.filter { it.uuid !in StandardServices }
                .sortedBy { service -> PrinterServices.indexOf(service.uuid).let { if (it < 0) PrinterServices.size else it } }
            return candidates.flatMap { it.characteristics }.firstOrNull(::writable)
        }

        // Kirim berjawaban didahulukan: printer baru menerima potongan berikutnya setelah menyatakan siap, jadi datanya tidak pernah dibuang.
        private fun writable(candidate: BluetoothGattCharacteristic): Boolean {
            val properties = candidate.properties
            if (properties and BluetoothGattCharacteristic.PROPERTY_WRITE != 0) {
                withoutResponse = false
                return true
            }
            if (properties and BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE != 0) {
                withoutResponse = true
                return true
            }
            return false
        }

        /** Mengirim [data] terpotong sesuai MTU; false bila ada potongan yang gagal. */
        suspend fun write(data: ByteArray): Boolean {
            val g = gatt ?: return false
            val target = characteristic ?: return false
            val type = if (withoutResponse) {
                BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
            } else {
                BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
            }
            var offset = 0
            while (offset < data.size) {
                val piece = data.copyOfRange(offset, minOf(offset + chunkSize, data.size))
                val result = CompletableDeferred<Boolean>().also { writeResult = it }
                if (!send(g, target, piece, type)) return false
                // Android memanggil onCharacteristicWrite juga untuk kirim tanpa jawaban saat potongan sudah diteruskan, jadi keduanya menunggu tanda itu.
                if (withTimeoutOrNull(WriteTimeoutMillis) { result.await() } != true) return false
                if (withoutResponse) delay(piece.size * MillisPerSecond / NoResponseBytesPerSecond)
                offset += piece.size
            }
            rememberWritePath(address, target.service.uuid, target.uuid)
            return true
        }

        /** Antrean tulis Android yang sedang penuh ditunggu sampai 3 detik, bukan dianggap printer putus. */
        @Suppress("DEPRECATION")
        private suspend fun send(g: BluetoothGatt, c: BluetoothGattCharacteristic, bytes: ByteArray, type: Int): Boolean {
            repeat((BusyWaitMillis / BusyRetryMillis).toInt()) {
                val accepted = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    when (g.writeCharacteristic(c, bytes, type)) {
                        BluetoothStatusCodes.SUCCESS -> true
                        BluetoothStatusCodes.ERROR_GATT_WRITE_REQUEST_BUSY -> false
                        else -> return false
                    }
                } else {
                    c.writeType = type
                    c.value = bytes
                    g.writeCharacteristic(c)
                }
                if (accepted) return true
                delay(BusyRetryMillis)
            }
            return false
        }

        private fun setState(state: PrinterLink) {
            link = state
            refreshLinks()
        }

        private fun closeGatt() {
            val current = gatt
            gatt = null
            characteristic = null
            runCatching { current?.disconnect() }
            runCatching { current?.close() }
        }
    }

    companion object {
        @Volatile
        private var instance: AndroidThermalPrinters? = null

        /** Satu pengelola untuk seluruh proses, supaya Activity yang dibuat ulang tidak membuka sambungan kedua ke printer yang sama. */
        fun get(context: Context): AndroidThermalPrinters =
            instance ?: synchronized(this) { instance ?: AndroidThermalPrinters(context).also { instance = it } }
    }
}
