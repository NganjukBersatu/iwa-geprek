package id.kongstudio.cafe.feature.permission

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import android.os.Build
import androidx.activity.ComponentActivity
import androidx.activity.result.IntentSenderRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.core.location.LocationManagerCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.google.android.gms.common.api.ResolvableApiException
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.LocationSettingsRequest
import com.google.android.gms.location.Priority
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Harus dibuat di onCreate Activity, sebelum STARTED, karena mendaftarkan peluncur izin. */
class AndroidDevicePermissions(private val activity: ComponentActivity) : DevicePermissions {
    private val _status = MutableStateFlow(read())
    override val status: StateFlow<Map<PermissionKind, PermissionStatus>> = _status.asStateFlow()

    private var pending: CompletableDeferred<Unit>? = null

    private val permissionLauncher = activity.registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { pending?.complete(Unit) }

    private val gpsLauncher = activity.registerForActivityResult(
        ActivityResultContracts.StartIntentSenderForResult(),
    ) { pending?.complete(Unit) }

    init {
        activity.lifecycle.addObserver(
            LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_RESUME) refresh() },
        )
    }

    override fun refresh() {
        _status.value = read()
    }

    override suspend fun request(kind: PermissionKind) {
        if (pending != null || _status.value[kind] == PermissionStatus.Granted) return
        try {
            when (kind) {
                PermissionKind.Location -> askPermissions(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION,
                )
                PermissionKind.Camera -> askPermissions(Manifest.permission.CAMERA)
                PermissionKind.Gps -> askGps()
                PermissionKind.Bluetooth -> askPermissions(*bluetoothPermissions())
            }
        } finally {
            pending = null
            refresh()
        }
    }

    private suspend fun askPermissions(vararg permissions: String) {
        val waiting = CompletableDeferred<Unit>()
        pending = waiting
        // Activity yang sedang berganti bisa menolak membuka kotak izin; statusnya tetap dibaca ulang sesudahnya.
        if (runCatching { permissionLauncher.launch(arrayOf(*permissions)) }.isFailure) return
        waiting.await()
    }

    /** Dialog sistem "Nyalakan lokasi"; tidak muncul bila layanan lokasi sudah menyala. */
    private suspend fun askGps() {
        val settings = LocationSettingsRequest.Builder()
            .addLocationRequest(LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, GPS_INTERVAL_MS).build())
            .setAlwaysShow(true)
            .build()
        val outcome = CompletableDeferred<Exception?>()
        LocationServices.getSettingsClient(activity).checkLocationSettings(settings)
            .addOnSuccessListener { outcome.complete(null) }
            .addOnFailureListener { outcome.complete(it) }

        val error = outcome.await() as? ResolvableApiException ?: return
        val waiting = CompletableDeferred<Unit>()
        pending = waiting
        if (runCatching { gpsLauncher.launch(IntentSenderRequest.Builder(error.resolution).build()) }.isFailure) return
        waiting.await()
    }

    private fun read(): Map<PermissionKind, PermissionStatus> =
        PermissionKind.entries.associateWith { if (isReady(it)) PermissionStatus.Granted else PermissionStatus.Denied }

    private fun isReady(kind: PermissionKind): Boolean = when (kind) {
        // Lokasi harus yang tepat; izin perkiraan saja tidak cukup untuk menilai jarak ke kafe.
        PermissionKind.Location -> isGranted(Manifest.permission.ACCESS_FINE_LOCATION)
        PermissionKind.Camera -> isGranted(Manifest.permission.CAMERA)
        PermissionKind.Gps -> {
            val manager = activity.getSystemService(Context.LOCATION_SERVICE) as LocationManager
            LocationManagerCompat.isLocationEnabled(manager)
        }
        PermissionKind.Bluetooth -> bluetoothPermissions().all(::isGranted)
    }

    /** Sama dengan yang diminta printer: Android 12 ke atas cukup pindai dan sambung, sebelumnya izin lokasi tepat. */
    private fun bluetoothPermissions(): Array<String> =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }

    private fun isGranted(permission: String): Boolean =
        ContextCompat.checkSelfPermission(activity, permission) == PackageManager.PERMISSION_GRANTED

    private companion object {
        const val GPS_INTERVAL_MS = 10_000L
    }
}
