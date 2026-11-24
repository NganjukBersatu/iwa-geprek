package id.kongstudio.cafe.feature.tasks

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.batches.Batch
import id.kongstudio.cafe.feature.batches.BatchAnswer
import id.kongstudio.cafe.feature.batches.BatchRepository
import id.kongstudio.cafe.feature.batches.StoredRun
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

private const val WeekDays = 7
private const val SearchDebounceMillis = 400L

internal data class TaskUiState(
    val filter: TaskFilter = TaskFilter.Pending,
    /** Rentang tanggal yang dilihat; bawaannya bulan ini. */
    val period: TaskPeriod = TaskPeriod.ThisMonth,
    /** Rentang pilihan sendiri; hanya berlaku saat [period] adalah Custom. */
    val customFrom: String = DateTimeFormat.todayWib(),
    val customTo: String = DateTimeFormat.todayWib(),
    /** Kata yang dicari di judul, isi, dan nama orang. */
    val search: String = "",
    /** Hanya tugas yang diberikan ke orang ini; null berarti siapa pun. */
    val assigneeId: String? = null,
    /** Cabang yang disaring; null berarti semua cabang yang boleh dilihat. */
    val outletId: String? = null,
    /** Halaman berbasis nol. */
    val page: Int = 0,
    val items: List<TaskItem> = emptyList(),
    val total: Int = 0,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val options: TaskOptions? = null,
    /** Sedang mengirim perubahan tugas. */
    val submitting: Boolean = false,
    val submitError: UiText? = null,
    /** Tugas outlet hari ini untuk orang ini; kosong bila belum absen dalam rentang waktunya. */
    val batches: List<Batch> = emptyList(),
    val batchSubmitting: Boolean = false,
    val batchError: UiText? = null,
    /** Tugas yang pengisian asalnya sedang dibuka; null berarti lembarnya tertutup. */
    /** Pengisian yang sedang diperbaiki, sudah beserta jawaban tersimpannya. */
    val fixing: StoredRun? = null,
    val sourceTaskId: String? = null,
    val sourceRun: SourceRun? = null,
    val sourceFailure: AppFailure? = null,
) {
    val pageCount: Int get() = (total + TaskPageSize - 1) / TaskPageSize

    val dateFrom: String?
        get() = when (period) {
            TaskPeriod.ThisMonth -> null
            TaskPeriod.Today -> DateTimeFormat.todayWib()
            TaskPeriod.Week -> DateTimeFormat.daysAgo(WeekDays - 1)
            TaskPeriod.Custom -> customFrom
        }

    val dateTo: String?
        get() = when (period) {
            TaskPeriod.ThisMonth -> null
            TaskPeriod.Today, TaskPeriod.Week -> DateTimeFormat.todayWib()
            TaskPeriod.Custom -> customTo
        }

    /** Jumlah penyaring yang dipilih selain status dan kata pencarian, untuk lencana tombol filter. */
    val activeFilterCount: Int
        get() = listOf(period != TaskPeriod.ThisMonth, assigneeId != null, outletId != null).count { it }
}

internal class TaskViewModel(
    private val repository: TaskRepository,
    private val batchRepository: BatchRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(TaskUiState())
    val state: StateFlow<TaskUiState> = _state.asStateFlow()
    private var job: Job? = null
    private var searchJob: Job? = null

    init {
        loadOptions(outletId = null)
    }

    fun setFilter(filter: TaskFilter) {
        if (filter == _state.value.filter) return
        _state.update { it.copy(filter = filter, page = 0) }
        load()
    }

    fun setPeriod(period: TaskPeriod) {
        if (period == _state.value.period) return
        _state.update { it.copy(period = period, page = 0) }
        load()
    }

    fun setCustomRange(from: String, to: String) {
        _state.update { it.copy(period = TaskPeriod.Custom, customFrom = from, customTo = to, page = 0) }
        load()
    }

    /** Kata pencarian langsung berlaku; pemuatan menunggu sebentar agar tidak berjalan di setiap ketukan huruf. */
    fun setSearch(search: String) {
        _state.update { it.copy(search = search, page = 0) }
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(SearchDebounceMillis)
            load()
        }
    }

    fun setAssignee(assigneeId: String?) {
        if (assigneeId == _state.value.assigneeId) return
        _state.update { it.copy(assigneeId = assigneeId, page = 0) }
        load()
    }

    /** Mengembalikan tanggal, orang, dan cabang ke bawaan; kata pencarian dan status tetap. */
    fun resetFilters() {
        _state.update { it.copy(period = TaskPeriod.ThisMonth, assigneeId = null, outletId = null, page = 0) }
        load()
    }

    fun setOutlet(outletId: String?) {
        if (outletId == _state.value.outletId) return
        _state.update { it.copy(outletId = outletId, page = 0) }
        load()
    }

    fun setPage(page: Int) {
        val last = (_state.value.pageCount - 1).coerceAtLeast(0)
        _state.update { it.copy(page = page.coerceIn(0, last)) }
        load()
    }

    fun create(task: NewTask, onSuccess: () -> Unit) {
        val showDone = { _state.update { it.copy(filter = TaskFilter.Done, period = TaskPeriod.ThisMonth, page = 0) } }
        submit(onSuccess, afterSuccess = { if (task.complete) showDone() }) { repository.create(task) }
    }

    fun update(taskId: String, title: String, description: String, due: String?, onSuccess: () -> Unit) =
        submit(onSuccess) { repository.update(taskId, title, description, due) }

    fun complete(taskId: String, note: String, media: List<PickedMedia>, onSuccess: () -> Unit) =
        submit(onSuccess) { repository.complete(taskId, note, media) }

    fun addAttachments(taskId: String, media: List<PickedMedia>, onSuccess: () -> Unit) =
        submit(onSuccess) { repository.addAttachments(taskId, media) }

    fun removeAttachment(taskId: String, attachmentId: String) =
        submit(onSuccess = {}) { repository.removeAttachment(taskId, attachmentId) }

    fun delete(taskId: String, onSuccess: () -> Unit) = submit(onSuccess) { repository.delete(taskId) }

    fun clearSubmitError() = _state.update { it.copy(submitError = null) }

    /** Gagal memuat tugas outlet tidak menggagalkan halaman; kartunya hanya tidak tampil. */
    fun loadBatches() {
        viewModelScope.launch {
            when (val result = batchRepository.today()) {
                is ApiResult.Success -> _state.update { it.copy(batches = result.value) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> Unit
            }
        }
    }

    fun completeBatch(batchId: String, answers: List<BatchAnswer>, onSuccess: () -> Unit) {
        if (_state.value.batchSubmitting) return
        _state.update { it.copy(batchSubmitting = true, batchError = null) }
        viewModelScope.launch {
            when (val result = batchRepository.complete(batchId, answers)) {
                is WriteResult.Success -> {
                    _state.update { it.copy(batchSubmitting = false) }
                    onSuccess()
                    loadBatches()
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> _state.update {
                    it.copy(batchSubmitting = false, batchError = UiText.Failed(result.failure))
                }
            }
        }
    }

    fun clearBatchError() = _state.update { it.copy(batchError = null) }

    /** Mengambil jawaban tersimpan lalu membuka form perbaikan. */
    fun openFix(runId: String) {
        if (_state.value.batchSubmitting) return
        _state.update { it.copy(batchSubmitting = true, batchError = null) }
        viewModelScope.launch {
            when (val result = batchRepository.stored(runId)) {
                is ApiResult.Success -> _state.update { it.copy(batchSubmitting = false, fixing = result.value) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(batchSubmitting = false, batchError = UiText.Failed(result.failure)) }
            }
        }
    }

    fun closeFix() = _state.update { it.copy(fixing = null, batchError = null) }

    fun fixBatch(runId: String, answers: List<BatchAnswer>, onSuccess: () -> Unit) =
        changeBatch(onSuccess = { closeFix(); onSuccess() }) { batchRepository.fix(runId, answers) }

    fun cancelBatch(runId: String, onSuccess: () -> Unit) = changeBatch(onSuccess) { batchRepository.cancel(runId) }

    fun deleteBatch(runId: String, onSuccess: () -> Unit) = changeBatch(onSuccess) { batchRepository.delete(runId) }

    fun fixCompletion(taskId: String, note: String, onSuccess: () -> Unit) = submit(onSuccess) { repository.fixCompletion(taskId, note) }

    private fun <T> changeBatch(onSuccess: () -> Unit, send: suspend () -> WriteResult<T>) {
        if (_state.value.batchSubmitting) return
        _state.update { it.copy(batchSubmitting = true, batchError = null) }
        viewModelScope.launch {
            when (val result = send()) {
                is WriteResult.Success -> {
                    _state.update { it.copy(batchSubmitting = false) }
                    onSuccess()
                    loadBatches()
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> _state.update { it.copy(batchSubmitting = false, batchError = UiText.Failed(result.failure)) }
            }
        }
    }

    /** Membuka isi pengisian yang ditindaklanjuti [taskId]; dipanggil ulang untuk mencoba lagi. */
    fun openSourceRun(taskId: String) {
        _state.update { it.copy(sourceTaskId = taskId, sourceRun = null, sourceFailure = null) }
        viewModelScope.launch {
            val result = repository.sourceRun(taskId)
            if (_state.value.sourceTaskId != taskId) return@launch
            when (result) {
                is ApiResult.Success -> _state.update { it.copy(sourceRun = result.value) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(sourceFailure = result.failure) }
            }
        }
    }

    fun closeSourceRun() = _state.update { it.copy(sourceTaskId = null, sourceRun = null, sourceFailure = null) }

    /** Memuat karyawan yang boleh diberi tugas di [outletId]; null memakai cabang akun ini. */
    fun loadOptions(outletId: String?) {
        viewModelScope.launch {
            when (val result = repository.options(outletId)) {
                is ApiResult.Success -> _state.update { it.copy(options = result.value) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> Unit
            }
        }
    }

    fun load() {
        job?.cancel()
        _state.update { it.copy(loading = true, failure = null) }
        val current = _state.value
        job = viewModelScope.launch {
            val query = TaskQuery(
                filter = current.filter,
                dateFrom = current.dateFrom,
                dateTo = current.dateTo,
                outletId = current.outletId,
                search = current.search,
                assigneeId = current.assigneeId,
                page = current.page,
            )
            when (val result = repository.load(query)) {
                is ApiResult.Success -> _state.update {
                    it.copy(items = result.value.items, total = result.value.total, loading = false)
                }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }

    private fun submit(
        onSuccess: () -> Unit,
        afterSuccess: () -> Unit = {},
        send: suspend () -> WriteResult<Unit>,
    ) {
        if (_state.value.submitting) return
        _state.update { it.copy(submitting = true, submitError = null) }
        viewModelScope.launch {
            when (val result = send()) {
                is WriteResult.Success -> {
                    _state.update { it.copy(submitting = false) }
                    afterSuccess()
                    onSuccess()
                    load()
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> _state.update {
                    it.copy(submitting = false, submitError = UiText.Failed(result.failure))
                }
            }
        }
    }
}
