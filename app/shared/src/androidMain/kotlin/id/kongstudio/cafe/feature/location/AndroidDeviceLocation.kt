package id.kongstudio.cafe.feature.location

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import androidx.core.content.ContextCompat
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

private const val READ_TIMEOUT_MILLIS = 15_000L

class AndroidDeviceLocation(private val context: Context) : DeviceLocation {

    override suspend fun current(): LocationFix? {
        if (!hasPermission()) return null
        return withTimeoutOrNull(READ_TIMEOUT_MILLIS) { read() }
    }

    override fun distanceMeters(fix: LocationFix, latitude: Double, longitude: Double): Double {
        val result = FloatArray(1)
        Location.distanceBetween(fix.latitude, fix.longitude, latitude, longitude, result)
        return result[0].toDouble()
    }

    private fun hasPermission(): Boolean =
        ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED

    @SuppressLint("MissingPermission")
    private suspend fun read(): LocationFix? = suspendCancellableCoroutine { continuation ->
        val source = CancellationTokenSource()
        continuation.invokeOnCancellation { source.cancel() }
        LocationServices.getFusedLocationProviderClient(context)
            .getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, source.token)
            .addOnSuccessListener { location ->
                if (continuation.isActive) {
                    continuation.resume(location?.let { LocationFix(it.latitude, it.longitude, it.accuracy) })
                }
            }
            .addOnFailureListener { if (continuation.isActive) continuation.resume(null) }
    }
}
