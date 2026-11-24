package id.kongstudio.cafe.feature.stationboard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.station_contents
import id.kongstudio.cafe.resources.station_destinations
import id.kongstudio.cafe.resources.station_finish_deliver
import id.kongstudio.cafe.resources.station_finish_handover
import id.kongstudio.cafe.resources.station_finish_make
import id.kongstudio.cafe.resources.station_pick_destination
import id.kongstudio.cafe.resources.station_pick_hint
import id.kongstudio.cafe.resources.station_recipe_empty
import id.kongstudio.cafe.resources.station_recipe_hint
import id.kongstudio.cafe.resources.station_recipe_line
import id.kongstudio.cafe.resources.station_recipe_missing
import id.kongstudio.cafe.resources.station_recipe_title
import id.kongstudio.cafe.resources.station_start_deliver
import id.kongstudio.cafe.resources.station_start_handover
import id.kongstudio.cafe.resources.station_start_make
import id.kongstudio.cafe.resources.station_destinations_more
import id.kongstudio.cafe.resources.station_section_started
import id.kongstudio.cafe.resources.station_stage_handover
import id.kongstudio.cafe.resources.station_stage_deliver
import id.kongstudio.cafe.resources.station_state_waiting
import id.kongstudio.cafe.resources.station_task_group
import id.kongstudio.cafe.resources.station_worker_caption
import id.kongstudio.cafe.resources.station_worker_caption_role
import id.kongstudio.cafe.resources.station_worker_change
import id.kongstudio.cafe.resources.station_worker_default
import id.kongstudio.cafe.resources.station_worker_pick_hint
import id.kongstudio.cafe.resources.station_worker_pick_title
import id.kongstudio.cafe.resources.station_worker_since
import id.kongstudio.cafe.resources.station_worker_use
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import androidx.compose.foundation.layout.width
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.resources.station_undo
import id.kongstudio.cafe.resources.station_undo_message
import id.kongstudio.cafe.resources.station_undo_title
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.subpageheader.HeaderBack
import id.kongstudio.cafe.ui.component.subpageheader.HeaderWidth
import id.kongstudio.cafe.ui.component.subpageheader.SubPageHeader
import id.kongstudio.cafe.ui.component.worktimer.WorkTimerPill
import id.kongstudio.cafe.ui.component.initialsavatar.InitialsAvatar
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

// Bahan lebih dari ini ditampilkan sebagai baris padat supaya resep panjang tetap terbaca.
private const val DenseIngredientThreshold = 8
private val WorkerButtonWidth = 120.dp
private const val VisibleDestinations = 3

// Halaman kerja satu kelompok: satu kolom selebar layar berisi penghitung, tujuan, dan takaran atau isi pesanan, dengan bilah langkah di dasar.
@Composable
internal fun StationDetail(
    station: Station,
    portions: List<Portion>,
    labels: DestinationLabels,
    recipe: RecipeState,
    workers: List<StationWorker>,
    chosenWorkerId: String?,
    onChooseWorker: (String) -> Unit,
    enabled: Boolean,
    stepping: Boolean,
    failure: AppFailure?,
    onStep: (StepKind, taskIds: List<String>, seen: Stage) -> Unit,
    backLabel: String,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val stage = portions.first().task.stage
    // Semua tujuan terpilih sejak awal; mengetuk satu tujuan mengeluarkan atau memasukkannya.
    var unpicked by rememberSaveable(stage) { mutableStateOf(emptySet<String>()) }
    val picked = portions.filter { it.task.id !in unpicked }
    var confirmingUndo by rememberSaveable { mutableStateOf(false) }
    var triedWithoutDestination by rememberSaveable(stage) { mutableStateOf(false) }
    val units = picked.sumOf { it.line.quantity }
    val ids = picked.map { it.task.id }
    val none = ids.isEmpty()

    val leave = { if (!stepping) onClose() }
    PlatformBackHandler(enabled = true, onBack = leave)
    Column(modifier = modifier.fillMaxSize()) {
        // Penghitung dan keadaan ada di baris judul yang tidak ikut bergulir, supaya selalu terlihat.
        SubPageHeader(
            title = portions.first().line.name,
            back = HeaderBack(backLabel, leave),
            width = HeaderWidth.Page,
            trailing = { TitleStatus(portions = portions, stage = stage, kind = station.kind) },
        )
        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = AppTheme.windowSize.pagePadding, vertical = spacing.sm),
            verticalArrangement = Arrangement.spacedBy(spacing.xs),
        ) {
            GroupTitle(stringResource(Res.string.station_task_group))
            GroupCard {
                WorkerRow(menuName = portions.first().line.name, workers = workers, chosenWorkerId = chosenWorkerId, onChoose = onChooseWorker)
                AppDivider()
                DestinationRow(
                    station = station,
                    portions = portions,
                    unpicked = unpicked,
                    labels = labels,
                    onToggle = { id -> unpicked = if (id in unpicked) unpicked - id else unpicked + id },
                )
            }
            if (portions.size > 1) {
                AppText(
                    text = stringResource(Res.string.station_pick_hint),
                    role = TextRole.Caption,
                    color = AppTheme.colors.contentMuted,
                    modifier = Modifier.padding(start = spacing.xs),
                )
            }
            ContentGroup(station = station, portions = portions, recipe = recipe)
        }
        ActionBar {
            failure?.let { InlineMessage(text = failureText(it)) }
            if (none && triedWithoutDestination) InlineMessage(text = stringResource(Res.string.station_pick_destination))
            Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm), verticalAlignment = Alignment.CenterVertically) {
                if (stage == Stage.Waiting) {
                    PrimaryButton(
                        text = startLabel(station.kind, units),
                        onClick = { if (none) triedWithoutDestination = true else onStep(StepKind.Start, ids, stage) },
                        enabled = enabled,
                        loading = stepping,
                        modifier = Modifier.weight(1f),
                    )
                } else {
                    // Tombol selalu mengisi lebar penuh, jadi keduanya wajib berbobot supaya berbagi baris sama lebar.
                    PrimaryButton(
                        text = finishLabel(station.kind, units),
                        onClick = { if (none) triedWithoutDestination = true else onStep(StepKind.Finish, ids, stage) },
                        enabled = enabled,
                        loading = stepping,
                        modifier = Modifier.weight(1f),
                    )
                    SecondaryButton(
                        text = stringResource(Res.string.station_undo),
                        onClick = { if (none) triedWithoutDestination = true else confirmingUndo = true },
                        tone = ButtonTone.Cancel,
                        enabled = enabled && !stepping,
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }

    if (confirmingUndo) {
        ConfirmSheet(
            title = stringResource(Res.string.station_undo_title),
            message = stringResource(Res.string.station_undo_message, picked.joinToString(", ") { lineLabel(it.line) }),
            confirmLabel = stringResource(Res.string.station_undo),
            onConfirm = {
                confirmingUndo = false
                onStep(StepKind.Back, picked.map { it.task.id }, stage)
            },
            onDismiss = { confirmingUndo = false },
        )
    }
}

// Pelaku menu ini: pilihan terakhir atau akun yang login; Ganti membuka daftar karyawan yang bisa dipilih, dan server memeriksa ulang saat langkah dikirim.
@Composable
private fun WorkerRow(menuName: String, workers: List<StationWorker>, chosenWorkerId: String?, onChoose: (String) -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val current = workers.firstOrNull { it.userId == chosenWorkerId } ?: workers.firstOrNull { it.isLogin }
    var picking by rememberSaveable { mutableStateOf(false) }
    var pending by rememberSaveable(chosenWorkerId) { mutableStateOf<String?>(null) }
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = spacing.md, vertical = spacing.sm),
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        val name = current?.name.orEmpty()
        if (name.isBlank()) IconBadge(icon = AppIcons.User) else InitialsAvatar(name = name)
        Column(modifier = Modifier.weight(1f)) {
            AppText(text = name, role = TextRole.Label, color = colors.content)
            val caption = current?.roleName?.let { stringResource(Res.string.station_worker_caption_role, it) } ?: stringResource(Res.string.station_worker_caption)
            AppText(text = caption, role = TextRole.Caption, color = colors.contentMuted)
        }
        if (workers.size > 1) {
            SecondaryButton(text = stringResource(Res.string.station_worker_change), onClick = { picking = true }, modifier = Modifier.width(WorkerButtonWidth))
        }
    }
    if (picking) {
        val selected = pending ?: current?.userId
        val chosen = workers.firstOrNull { it.userId == selected }
        AppBottomSheet(title = stringResource(Res.string.station_worker_pick_title, menuName), onDismiss = { picking = false }) {
            AppText(text = stringResource(Res.string.station_worker_pick_hint), role = TextRole.Caption, color = colors.contentMuted)
            GroupCard {
                workers.forEachIndexed { index, worker ->
                    if (index > 0) AppDivider()
                    val isSelected = worker.userId == selected
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(if (isSelected) colors.selected else colors.surface)
                            .selectable(selected = isSelected, role = Role.RadioButton) { pending = worker.userId }
                            .padding(horizontal = spacing.md, vertical = spacing.sm),
                        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            AppText(text = worker.name, role = TextRole.Label, color = colors.content)
                            val detail = listOfNotNull(worker.roleName, DateTimeFormat.clock(worker.clockInAt)?.let { stringResource(Res.string.station_worker_since, it) }).joinToString(" · ")
                            if (detail.isNotBlank()) AppText(text = detail, role = TextRole.Caption, color = colors.contentMuted)
                        }
                        if (worker.isLogin) StatusBadge(stringResource(Res.string.station_worker_default), BadgeTone.Neutral)
                        if (isSelected) AppIcon(icon = AppIcons.Check, tint = colors.primary, size = AppTheme.sizes.iconSmall)
                    }
                }
            }
            PrimaryButton(
                text = chosen?.let { stringResource(Res.string.station_worker_use, it.name) } ?: stringResource(Res.string.station_worker_change),
                onClick = {
                    chosen?.let { onChoose(it.userId) }
                    picking = false
                },
                enabled = chosen != null,
                modifier = Modifier.padding(bottom = spacing.sm),
            )
        }
    }
}

// Bilah dasar yang tidak ikut bergulir, supaya tombol langkah selalu terlihat walaupun resepnya panjang.
@Composable
private fun ActionBar(content: @Composable ColumnScope.() -> Unit) {
    val spacing = AppTheme.spacing
    Column(modifier = Modifier.fillMaxWidth().background(AppTheme.colors.surface)) {
        AppDivider()
        Column(
            modifier = Modifier.fillMaxWidth().padding(horizontal = AppTheme.windowSize.pagePadding, vertical = spacing.sm),
            verticalArrangement = Arrangement.spacedBy(spacing.sm),
            content = content,
        )
    }
}

@Composable
private fun GroupTitle(text: String) {
    AppText(
        text = text,
        role = TextRole.Caption,
        color = AppTheme.colors.contentMuted,
        modifier = Modifier.padding(start = AppTheme.spacing.xs, top = AppTheme.spacing.sm),
    )
}

@Composable
private fun GroupCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(AppTheme.shapes.card)
            .background(AppTheme.colors.surface),
        content = content,
    )
}

/** Jumlah, keadaan menurut jenis stasiun, dan penghitung di samping judul. */
@Composable
private fun TitleStatus(portions: List<Portion>, stage: Stage, kind: StationKind) {
    val since = portions.minOf { (if (stage == Stage.Started) it.task.startedEpoch else it.task.arrivedEpoch) ?: it.order.createdEpoch }
    val target = if (stage == Stage.Started) portions.mapNotNull { it.task.targetSeconds }.minOrNull() else null
    StatusBadge("${portions.sumOf { it.line.quantity }}x", BadgeTone.Neutral)
    if (stage == Stage.Started) {
        val started = when (kind) {
            StationKind.Make -> Res.string.station_section_started
            StationKind.Deliver -> Res.string.station_stage_deliver
            StationKind.Handover -> Res.string.station_stage_handover
        }
        StatusBadge(stringResource(started), BadgeTone.Accent, icon = AppIcons.Refresh)
    } else {
        StatusBadge(stringResource(Res.string.station_state_waiting), BadgeTone.Neutral, icon = AppIcons.History)
    }
    WorkTimerPill(sinceEpoch = since, targetSeconds = target, labels = timerLabels(stage))
}

// Tujuan sebagai chip sebaris: tiga pertama, sisanya dibuka lewat "+ n lain"; mengetuk chip memilih atau melepas tujuan itu.
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun DestinationRow(
    station: Station,
    portions: List<Portion>,
    unpicked: Set<String>,
    labels: DestinationLabels,
    onToggle: (String) -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    var expanded by rememberSaveable { mutableStateOf(false) }
    val shown = if (expanded) portions else portions.take(VisibleDestinations)
    // Nomor nota hanya ditambahkan bila dua pesanan berlabel sama, misalnya dua pesanan di meja yang sama.
    val names = portions.map { labels.of(it.order) }
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = spacing.md, vertical = spacing.sm),
        horizontalArrangement = Arrangement.spacedBy(spacing.md),
        verticalAlignment = Alignment.Top,
    ) {
        AppText(
            text = stringResource(Res.string.station_destinations),
            role = TextRole.Body,
            color = colors.contentMuted,
            modifier = Modifier.padding(top = spacing.sm),
        )
        FlowRow(
            modifier = Modifier.weight(1f),
            horizontalArrangement = Arrangement.spacedBy(spacing.xs, Alignment.End),
            verticalArrangement = Arrangement.spacedBy(spacing.xs),
        ) {
            shown.forEach { portion ->
                val label = labels.of(portion.order)
                val receipt = "#${portion.order.receipt}"
                val repeated = station.kind == StationKind.Make && label != receipt && names.count { it == label } > 1
                val text = (if (repeated) "$label $receipt" else label) + " · ${portion.line.quantity}x"
                AppChip(
                    label = text,
                    selected = portions.size > 1 && portion.task.id !in unpicked,
                    onClick = { if (portions.size > 1) onToggle(portion.task.id) },
                )
            }
            val hidden = portions.size - shown.size
            if (hidden > 0) {
                AppChip(label = stringResource(Res.string.station_destinations_more, hidden), selected = false, onClick = { expanded = true })
            }
        }
    }
}

// Pembuat melihat takaran dikalikan porsi; pengantar dan penyerah melihat isi pesanan yang dibawa.
@Composable
private fun ContentGroup(station: Station, portions: List<Portion>, recipe: RecipeState) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    if (station.kind != StationKind.Make) {
        GroupTitle(stringResource(Res.string.station_contents))
        GroupCard {
            portions.forEachIndexed { index, portion ->
                if (index > 0) AppDivider()
                Column(modifier = Modifier.fillMaxWidth().padding(horizontal = spacing.md, vertical = spacing.sm)) {
                    AppText(text = lineLabel(portion.line), role = TextRole.Body, color = colors.content)
                    val detail = (portion.line.options + listOfNotNull(portion.line.note)).joinToString(" · ")
                    if (detail.isNotBlank()) AppText(text = detail, role = TextRole.Caption, color = colors.warning)
                }
            }
        }
        return
    }
    when (recipe) {
        RecipeState.Idle, RecipeState.Loading -> LoadingState()
        is RecipeState.Failed -> InlineMessage(text = failureText(recipe.failure))
        is RecipeState.Ready -> {
            val found = recipe.recipe
            GroupTitle(stringResource(Res.string.station_recipe_title, found.portions, found.ingredients.size))
            if (found.ingredients.isEmpty()) {
                AppText(
                    text = stringResource(Res.string.station_recipe_empty),
                    role = TextRole.Body,
                    color = colors.contentMuted,
                    modifier = Modifier.padding(start = spacing.xs),
                )
            } else {
                val dense = found.ingredients.size > DenseIngredientThreshold
                GroupCard {
                    found.ingredients.forEachIndexed { index, ingredient ->
                        if (index > 0) AppDivider()
                        val unit = ingredient.unit?.let { " $it" }.orEmpty()
                        val perPortion = stringResource(Res.string.station_recipe_line, "${ingredient.perPortion}$unit", found.portions)
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(horizontal = spacing.md, vertical = if (dense) spacing.xs else spacing.sm),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            if (dense) {
                                AppText(text = "${ingredient.name}  $perPortion", role = TextRole.Body, color = colors.content, modifier = Modifier.weight(1f))
                            } else {
                                Column(modifier = Modifier.weight(1f)) {
                                    AppText(text = ingredient.name, role = TextRole.Body, color = colors.content)
                                    AppText(text = perPortion, role = TextRole.Caption, color = colors.contentMuted)
                                }
                            }
                            AppText(text = "${ingredient.total}$unit", role = if (dense) TextRole.Label else TextRole.Title, color = colors.content)
                        }
                    }
                }
                AppText(
                    text = stringResource(Res.string.station_recipe_hint),
                    role = TextRole.Caption,
                    color = colors.contentMuted,
                    modifier = Modifier.padding(start = spacing.xs, top = spacing.xs),
                )
            }
            if (found.withoutRecipe.isNotEmpty()) {
                AppText(
                    text = stringResource(Res.string.station_recipe_missing, found.withoutRecipe.joinToString(", ")),
                    role = TextRole.Caption,
                    color = colors.warning,
                    modifier = Modifier.padding(start = spacing.xs, top = spacing.xs),
                )
            }
        }
    }
}

@Composable
private fun startLabel(kind: StationKind, units: Int): String = when (kind) {
    StationKind.Make -> stringResource(Res.string.station_start_make, units)
    StationKind.Deliver -> stringResource(Res.string.station_start_deliver, units)
    StationKind.Handover -> stringResource(Res.string.station_start_handover)
}

@Composable
private fun finishLabel(kind: StationKind, units: Int): String = when (kind) {
    StationKind.Make -> stringResource(Res.string.station_finish_make, units)
    StationKind.Deliver -> stringResource(Res.string.station_finish_deliver, units)
    StationKind.Handover -> stringResource(Res.string.station_finish_handover)
}
