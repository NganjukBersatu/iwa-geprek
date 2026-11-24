package id.kongstudio.cafe.feature.ingredientstock

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Masalah satu baris sebelum dikirim; [Server] membawa alasan dari server setelah dikirim. */
internal sealed interface LineProblem {
    data object NoIngredient : LineProblem

    data object Quantity : LineProblem

    data object Duplicate : LineProblem

    class Server(val message: String) : LineProblem
}

/** Satu baris isian: bahan yang dipilih dan stok awalnya; [uid] tetap walau baris lain dihapus. */
internal data class OpeningLine(val uid: Int, val ingredient: StockIngredient? = null, val text: String = "", val problem: LineProblem? = null) {
    val blank: Boolean get() = ingredient == null && text.isBlank()
}

/** Hasil simpan terakhir: berapa bahan tersimpan dan berapa yang gagal; alasannya ada di baris yang gagal. */
internal class OpeningBulkReport(val saved: Int, val failed: Int)

internal data class OpeningBulkState(
    val lines: List<OpeningLine> = listOf(OpeningLine(uid = 0)),
    /** Baris yang sedang memilih bahan; null bila pemilih tertutup. */
    val picking: Int? = null,
    val confirming: Boolean = false,
    val saving: Boolean = false,
    val saveFailure: AppFailure? = null,
    val report: OpeningBulkReport? = null,
) {
    /** Baris yang akan dikirim: bahan dipilih dan stok awal diisi. */
    val ready: List<OpeningLine> get() = lines.filter { it.ingredient != null && it.text.isNotBlank() }
    val canAddLine: Boolean get() = lines.size < OpeningBulkMax
}

/**
 * Mengisi stok awal banyak bahan sekaligus seperti dialog isi banyak di web: baris ditambah satu per satu, bahan dipilih lewat
 * pencarian server, lalu satu kiriman lewat pintu massal; setiap baris berhasil atau gagal sendiri.
 */
internal class OpeningBulkViewModel(
    private val repository: IngredientStockRepository,
    private val onUnauthorized: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(OpeningBulkState())
    val state: StateFlow<OpeningBulkState> = _state.asStateFlow()
    private var nextUid = 1

    fun addLine() {
        if (!_state.value.canAddLine) return
        _state.update { it.copy(lines = it.lines + OpeningLine(uid = nextUid++), report = null) }
    }

    /** Baris terakhir yang dihapus diganti baris kosong supaya halaman tidak pernah tanpa isian. */
    fun removeLine(uid: Int) = _state.update { state ->
        val left = state.lines.filterNot { it.uid == uid }
        state.copy(lines = left.ifEmpty { listOf(OpeningLine(uid = nextUid++)) }, report = null)
    }

    fun openPicker(uid: Int) = _state.update { it.copy(picking = uid) }

    fun closePicker() = _state.update { it.copy(picking = null) }

    /** Bahan yang sudah ada di baris lain tidak dipasang dua kali; barisnya ditandai supaya orang tahu sebabnya. */
    fun pick(ingredient: StockIngredient) = _state.update { state ->
        val uid = state.picking ?: return@update state
        val duplicate = state.lines.any { it.uid != uid && it.ingredient?.id == ingredient.id }
        state.copy(
            picking = null,
            report = null,
            lines = state.lines.map { line ->
                when {
                    line.uid != uid -> line
                    duplicate -> line.copy(problem = LineProblem.Duplicate)
                    else -> line.copy(ingredient = ingredient, problem = null)
                }
            },
        )
    }

    fun setText(uid: Int, text: String) = _state.update { state ->
        state.copy(report = null, lines = state.lines.map { if (it.uid == uid) it.copy(text = text, problem = null) else it })
    }

    /** Semua baris diperiksa dulu; konfirmasi hanya muncul bila tidak ada baris setengah isi dan semua angka sah. */
    fun ask() = _state.update { state ->
        val checked = state.lines.map { line ->
            when {
                line.blank -> line
                line.ingredient == null -> line.copy(problem = LineProblem.NoIngredient)
                StockQuantity.parse(line.text) == null -> line.copy(problem = LineProblem.Quantity)
                else -> line.copy(problem = line.problem.takeIf { it is LineProblem.Duplicate })
            }
        }
        val clean = checked.none { it.problem != null } && checked.any { !it.blank }
        state.copy(lines = checked, confirming = clean, saveFailure = null, report = null)
    }

    fun dismiss() = _state.update { it.copy(confirming = false) }

    fun save() {
        val current = _state.value
        if (current.saving) return
        val sent = current.ready.mapNotNull { line ->
            val ingredient = line.ingredient ?: return@mapNotNull null
            StockQuantity.parse(line.text)?.let { qty -> line to OpeningRow(ingredient.id, qty) }
        }
        _state.update { it.copy(saving = true, saveFailure = null) }
        viewModelScope.launch {
            when (val result = repository.setOpenings(sent.map { it.second })) {
                is DeviceResult.Ok -> {
                    val failedBy = result.value.mapNotNull { row -> row.error?.let { row.ingredientId to it } }.toMap()
                    val sentUids = sent.map { it.first.uid }.toSet()
                    // Baris yang tersimpan dilepas; yang gagal tetap dengan alasannya supaya bisa dibetulkan lalu dikirim lagi.
                    _state.update { state ->
                        val kept = state.lines.mapNotNull { line ->
                            val reason = line.ingredient?.id?.let(failedBy::get)
                            when {
                                line.uid !in sentUids -> line.takeIf { !it.blank }
                                reason != null -> line.copy(problem = LineProblem.Server(reason))
                                else -> null
                            }
                        }
                        state.copy(
                            saving = false,
                            confirming = false,
                            lines = kept.ifEmpty { listOf(OpeningLine(uid = nextUid++)) },
                            report = OpeningBulkReport(saved = sent.size - failedBy.size, failed = failedBy.size),
                        )
                    }
                }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(saving = false, confirming = false, saveFailure = result.failure) }
                }
            }
        }
    }
}
