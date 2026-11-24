package id.kongstudio.cafe.feature.notices

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.network.ApiResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Pengumuman selalu diminta ke server begitu masuk, baik sesudah login maupun saat sesi dipulihkan. */
internal class NoticeViewModel(
    private val repository: NoticeRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _items = MutableStateFlow<List<NoticeItem>>(emptyList())
    val items: StateFlow<List<NoticeItem>> = _items.asStateFlow()

    init {
        viewModelScope.launch {
            when (val result = repository.visible()) {
                is ApiResult.Success -> _items.value = result.value
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> Unit
            }
        }
    }

    /** Lembar langsung tertutup; penandaan sudah dibaca berjalan di belakang dan gagalnya hanya membuat pengumuman muncul lagi nanti. */
    fun close() {
        val ids = _items.value.map { it.id }
        if (ids.isEmpty()) return
        _items.value = emptyList()
        viewModelScope.launch { repository.markRead(ids) }
    }
}
