package id.kongstudio.cafe.feature.menumanage

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.network.LiveChange
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_edit
import id.kongstudio.cafe.resources.menu_category
import id.kongstudio.cafe.resources.menu_cost_basis
import id.kongstudio.cafe.resources.menu_cost_fixed
import id.kongstudio.cafe.resources.menu_cost_none
import id.kongstudio.cafe.resources.menu_cost_recipe
import id.kongstudio.cafe.resources.menu_cost_resale
import id.kongstudio.cafe.resources.menu_description
import id.kongstudio.cafe.resources.menu_detail_extras
import id.kongstudio.cafe.resources.menu_detail_info
import id.kongstudio.cafe.resources.menu_detail_price
import id.kongstudio.cafe.resources.menu_detail_variants
import id.kongstudio.cafe.resources.menu_made_at
import id.kongstudio.cafe.resources.menu_made_direct
import id.kongstudio.cafe.resources.menu_no_photo
import id.kongstudio.cafe.resources.menu_photo_add
import id.kongstudio.cafe.resources.menu_ready
import id.kongstudio.cafe.resources.menu_recipe_empty
import id.kongstudio.cafe.resources.menu_recipe_line_qty
import id.kongstudio.cafe.resources.menu_recipe_line_stock
import id.kongstudio.cafe.resources.menu_recipe_none_left
import id.kongstudio.cafe.resources.menu_recipe_portions
import id.kongstudio.cafe.resources.menu_recipe_title
import id.kongstudio.cafe.resources.menu_sold_today
import id.kongstudio.cafe.resources.menu_sold_today_value
import id.kongstudio.cafe.resources.menu_toggle_label
import id.kongstudio.cafe.resources.menu_variant_optional
import id.kongstudio.cafe.resources.menu_variant_required
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.loadable.Loadable
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.productcard.BlockedLabel
import id.kongstudio.cafe.ui.component.productcard.BlockedTone
import id.kongstudio.cafe.ui.component.remoteimage.RemoteImage
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.subpage.SubPage
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.flow.Flow
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/**
 * Halaman rincian satu menu untuk pekerja cabang: bisa dijual atau tidak beserta sebabnya, isi yang ditanyakan pelanggan,
 * dan stok bahan resepnya; dimuat ulang setiap sinyal /live yang menyentuh menu, bahan, atau pesanan.
 */
@Composable
internal fun MenuDetailPage(
    entry: MenuEntry,
    blocked: Pair<String, BlockedTone>?,
    listTitle: String,
    repository: MenuManageRepository,
    changes: Flow<LiveChange>,
    canManage: Boolean,
    canToggle: Boolean,
    acting: Boolean,
    onBack: () -> Unit,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
    onToggle: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var detail by remember(entry.id) { mutableStateOf<MenuDetail?>(null) }
    var failure by remember(entry.id) { mutableStateOf<AppFailure?>(null) }
    var attempt by remember(entry.id) { mutableIntStateOf(0) }
    var signal by remember(entry.id) { mutableIntStateOf(0) }

    LaunchedEffect(entry.id, changes) { changes.collect { signal += 1 } }
    LaunchedEffect(entry.id, attempt, signal) {
        when (val result = repository.detail(entry.id)) {
            is DeviceResult.Ok -> {
                detail = result.value
                failure = null
            }
            is DeviceResult.Failed -> failure = result.failure
        }
    }

    SubPage(title = entry.name, backLabel = stringResource(Res.string.back_to_page, listTitle), onBack = onBack, modifier = modifier, canLeave = !acting) {
        val photo = entry.imageUrl
        if (photo != null) {
            RemoteImage(url = photo, contentDescription = entry.name)
        } else if (canManage) {
            Notice(text = stringResource(Res.string.menu_no_photo), icon = AppIcons.Photo)
            SecondaryButton(text = stringResource(Res.string.menu_photo_add), onClick = onEdit)
        }

        if (blocked != null) {
            BlockedLabel(text = blocked.first, tone = blocked.second)
        } else {
            StatusBadge(text = stringResource(Res.string.menu_ready), tone = BadgeTone.Positive, icon = AppIcons.Check)
        }
        if (canToggle && !entry.switchedOffForAll) {
            ToggleSwitch(label = stringResource(Res.string.menu_toggle_label), checked = entry.available, onCheckedChange = { onToggle() })
        }

        val loaded = detail
        SectionTitle(stringResource(Res.string.menu_detail_info))
        DetailCard(
            rows = listOf(
                stringResource(Res.string.menu_detail_price) to formatRupiah(entry.price),
                stringResource(Res.string.menu_category) to entry.category,
                stringResource(Res.string.menu_description) to entry.description,
                stringResource(Res.string.menu_made_at) to loaded?.let { it.makerStation ?: stringResource(Res.string.menu_made_direct) },
                stringResource(Res.string.menu_sold_today) to loaded?.let { stringResource(Res.string.menu_sold_today_value, it.soldToday) },
                stringResource(Res.string.menu_cost_basis) to loaded?.let { costBasisOf(it.costBasis) }?.let { stringResource(it) },
            ),
        )

        val problem = failure
        if (loaded == null && problem != null) {
            FailureState(failure = problem, onRetry = { attempt += 1 })
        } else {
            Loadable(loading = loaded == null) {
                loaded?.let { DetailSections(it) }
            }
        }
        problem?.takeIf { loaded != null }?.let { AppText(text = failureText(it), role = TextRole.Caption, color = AppTheme.colors.danger) }

        if (canManage) {
            PrimaryButton(text = stringResource(Res.string.common_edit), onClick = onEdit)
            SecondaryButton(text = stringResource(Res.string.common_delete), onClick = onDelete, tone = ButtonTone.Danger)
        }
    }
}

// Satu kolom sendiri karena Loadable menumpuk isinya; tanpa ini setiap bagian saling menimpa.
@Composable
private fun DetailSections(detail: MenuDetail) = Column(
    modifier = Modifier.fillMaxWidth(),
    verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
) {
    if (detail.variantGroups.isNotEmpty()) {
        SectionTitle(stringResource(Res.string.menu_detail_variants))
        ListCard {
            DividedItems(detail.variantGroups) { group ->
                ListRow(
                    title = group.name,
                    detail = group.choices.joinToString(", "),
                    caption = stringResource(if (group.required) Res.string.menu_variant_required else Res.string.menu_variant_optional),
                )
            }
        }
    }
    if (detail.extras.isNotEmpty()) {
        SectionTitle(stringResource(Res.string.menu_detail_extras))
        ListCard {
            DividedItems(detail.extras) { extra ->
                ListRow(title = extra.name, trailing = { AppText(text = formatRupiah(extra.price)) })
            }
        }
    }
    detail.recipe?.let { lines -> RecipeSection(lines, detail.portionsLeft) }
}

@Composable
private fun RecipeSection(lines: List<MenuRecipeLine>, portionsLeft: Int?) {
    val colors = AppTheme.colors
    SectionTitle(stringResource(Res.string.menu_recipe_title))
    if (lines.isEmpty()) {
        Notice(text = stringResource(Res.string.menu_recipe_empty), icon = AppIcons.Book)
        return
    }
    portionsLeft?.let { portions ->
        if (portions > 0) {
            StatusBadge(text = stringResource(Res.string.menu_recipe_portions, portions), tone = BadgeTone.Positive, icon = AppIcons.Check)
        } else {
            StatusBadge(text = stringResource(Res.string.menu_recipe_none_left), tone = BadgeTone.Danger, icon = AppIcons.Alert)
        }
    }
    ListCard {
        DividedItems(lines) { line ->
            ListRow(
                title = line.ingredient,
                caption = stringResource(Res.string.menu_recipe_line_qty, StockQuantity.withUnit(line.qty, line.unit)),
                trailing = {
                    AppText(
                        text = stringResource(Res.string.menu_recipe_line_stock, StockQuantity.withUnit(line.stock, line.unit)),
                        color = if (line.short) colors.danger else colors.content,
                    )
                },
            )
        }
    }
}

// Nilai baru dari server yang belum dikenal tablet tidak ditampilkan, daripada ditebak.
private fun costBasisOf(basis: CostBasis): StringResource? = when (basis) {
    CostBasis.Fixed -> Res.string.menu_cost_fixed
    CostBasis.Recipe -> Res.string.menu_cost_recipe
    CostBasis.Resale -> Res.string.menu_cost_resale
    CostBasis.None -> Res.string.menu_cost_none
    CostBasis.Unknown -> null
}
