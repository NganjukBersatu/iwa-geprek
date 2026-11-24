package id.kongstudio.cafe.feature.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Memantau jaringan bawaan perangkat; "online" berarti Android sudah memastikan internetnya terjangkau. */
class AndroidNetworkMonitor(context: Context) : NetworkMonitor {
    private val manager = context.getSystemService(ConnectivityManager::class.java)
    private val _online = MutableStateFlow(reachesInternet(manager.getNetworkCapabilities(manager.activeNetwork)))
    private val callback = object : ConnectivityManager.NetworkCallback() {
        override fun onCapabilitiesChanged(network: Network, capabilities: NetworkCapabilities) {
            _online.value = reachesInternet(capabilities)
        }

        override fun onLost(network: Network) {
            _online.value = false
        }
    }

    override val online: StateFlow<Boolean> = _online.asStateFlow()

    init {
        manager.registerDefaultNetworkCallback(callback)
    }

    /** Melepas pemantau; dipanggil saat aktivitas dimusnahkan agar pemantau tidak menumpuk. */
    fun close() = manager.unregisterNetworkCallback(callback)

    private fun reachesInternet(capabilities: NetworkCapabilities?): Boolean =
        capabilities != null &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
}
