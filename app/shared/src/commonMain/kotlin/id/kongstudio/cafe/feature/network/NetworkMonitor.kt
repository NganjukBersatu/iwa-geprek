package id.kongstudio.cafe.feature.network

import kotlinx.coroutines.flow.StateFlow

/** Jembatan ke keadaan internet perangkat; implementasinya diberikan oleh platform. */
interface NetworkMonitor {
    /** True bila perangkat benar-benar bisa menjangkau internet, bukan sekadar tersambung ke Wi-Fi atau data seluler. */
    val online: StateFlow<Boolean>
}
