package id.kongstudio.cafe.feature.printer

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.nav_printer
import id.kongstudio.cafe.resources.printer_connecting
import id.kongstudio.cafe.resources.printer_forget
import id.kongstudio.cafe.resources.printer_hint
import id.kongstudio.cafe.resources.printer_keep_alive
import id.kongstudio.cafe.resources.printer_keep_alive_hint
import id.kongstudio.cafe.resources.printer_logo_check
import id.kongstudio.cafe.resources.printer_logo_no
import id.kongstudio.cafe.resources.printer_logo_off
import id.kongstudio.cafe.resources.printer_logo_stored
import id.kongstudio.cafe.resources.printer_logo_yes
import id.kongstudio.cafe.resources.printer_no_slots
import id.kongstudio.cafe.resources.printer_not_paired
import id.kongstudio.cafe.resources.printer_notice_bluetooth_off
import id.kongstudio.cafe.resources.printer_notice_interrupted
import id.kongstudio.cafe.resources.printer_notice_logo_full
import id.kongstudio.cafe.resources.printer_notice_logo_stored
import id.kongstudio.cafe.resources.printer_notice_no_permission
import id.kongstudio.cafe.resources.printer_notice_not_a_printer
import id.kongstudio.cafe.resources.printer_notice_nothing_found
import id.kongstudio.cafe.resources.printer_notice_test_printed
import id.kongstudio.cafe.resources.printer_notice_unreachable
import id.kongstudio.cafe.resources.printer_offline
import id.kongstudio.cafe.resources.printer_pair
import id.kongstudio.cafe.resources.printer_paper
import id.kongstudio.cafe.resources.printer_pick_title
import id.kongstudio.cafe.resources.printer_ready
import id.kongstudio.cafe.resources.printer_repair
import id.kongstudio.cafe.resources.printer_role_bar
import id.kongstudio.cafe.resources.printer_role_kitchen
import id.kongstudio.cafe.resources.printer_role_receipt
import id.kongstudio.cafe.resources.printer_role_station
import id.kongstudio.cafe.resources.printer_searching
import id.kongstudio.cafe.resources.printer_test
import id.kongstudio.cafe.resources.printer_slot_held
import id.kongstudio.cafe.resources.printer_slot_receipt
import id.kongstudio.cafe.resources.printer_slot_sent
import id.kongstudio.cafe.resources.printer_slot_sent_delivery
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.inlinemessage.MessageTone
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.pageframe.PageFrame
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Layar Printer: satu kartu per slot pada rencana cetak tablet ini, tanpa pilihan mode atau kategori (diatur di web). */
@Composable
internal fun PrinterScreen(viewModel: PrinterViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.state.collectAsState()
    val plan by viewModel.plan.collectAsState()
    val planFailure by viewModel.planFailure.collectAsState()
    val paired by viewModel.paired.collectAsState()
    val links by viewModel.links.collectAsState()
    val keepAlive by viewModel.keepAlive.collectAsState()
    val spacing = AppTheme.spacing
    val current = plan

    PageFrame(modifier = modifier) {
        item {
            PageTitle(title = stringResource(Res.string.nav_printer), subtitle = stringResource(Res.string.printer_hint))
        }
        item {
            ListCard {
                Column(modifier = Modifier.fillMaxWidth().padding(spacing.md), verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
                    ToggleSwitch(label = stringResource(Res.string.printer_keep_alive), checked = keepAlive, onCheckedChange = viewModel::setKeepAlive)
                    AppText(text = stringResource(Res.string.printer_keep_alive_hint), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
                }
            }
        }
        val failure = planFailure
        when {
            current == null && failure != null -> item { FailureState(failure = failure, onRetry = viewModel.onRetryPlan) }
            current == null -> item { LoadingState() }
            current.slots.isEmpty() -> item { Notice(text = stringResource(Res.string.printer_no_slots), icon = AppIcons.Printer) }
            else -> items(current.slots, key = { it.key }) { slot ->
                val name = printerSlotName(slot, current)
                PrinterCard(
                    slot = slot,
                    name = name,
                    explanation = slotExplanation(slot, current),
                    printer = paired[slot],
                    link = links[slot] ?: PrinterLink.NotPaired,
                    busy = state.busy == slot,
                    anyBusy = state.busy != null,
                    notice = state.notices[slot],
                    onPair = { viewModel.search(slot) },
                    onCheck = { viewModel.check(slot, name) },
                    onForget = { viewModel.forget(slot) },
                    onPaper = { viewModel.setPaper(slot, it) },
                    onConfirmLogo = viewModel::confirmLogo,
                )
            }
        }
    }

    state.picking?.let { slot ->
        val name = printerSlotName(slot, current)
        AppBottomSheet(title = stringResource(Res.string.printer_pick_title), onDismiss = viewModel::dismissPicker) {
            ListCard {
                state.found.forEachIndexed { index, device ->
                    if (index > 0) AppDivider()
                    ListRow(
                        title = device.name,
                        caption = device.address,
                        leading = { IconBadge(AppIcons.Printer) },
                        onClick = { viewModel.pair(device, name) },
                    )
                }
            }
        }
    }
}

@Composable
private fun PrinterCard(
    slot: PrinterSlot,
    name: String,
    explanation: String,
    printer: PairedPrinter?,
    link: PrinterLink,
    busy: Boolean,
    anyBusy: Boolean,
    notice: PrinterNotice?,
    onPair: () -> Unit,
    onCheck: () -> Unit,
    onForget: () -> Unit,
    onPaper: (PaperSize) -> Unit,
    onConfirmLogo: (Boolean) -> Unit,
) {
    val spacing = AppTheme.spacing
    val colors = AppTheme.colors
    val papers = PaperSize.entries

    ListCard {
        Column(modifier = Modifier.fillMaxWidth().padding(spacing.md), verticalArrangement = Arrangement.spacedBy(spacing.md)) {
            ListRow(
                title = name,
                detail = explanation,
                caption = printer?.let { listOf(it.name, it.address).joinToString(" · ") },
                leading = { IconBadge(AppIcons.Printer) },
                trailing = {
                    StatusBadge(
                        text = stringResource(linkLabel(link, busy)),
                        tone = when {
                            busy -> BadgeTone.Neutral
                            link == PrinterLink.Ready -> BadgeTone.Positive
                            printer == null || link == PrinterLink.Offline -> BadgeTone.Warning
                            else -> BadgeTone.Neutral
                        },
                        icon = when {
                            busy -> AppIcons.Refresh
                            link == PrinterLink.Ready -> AppIcons.Check
                            else -> AppIcons.Alert
                        },
                    )
                },
            )
            if (printer != null) {
                ChoiceGroup(
                    label = stringResource(Res.string.printer_paper),
                    options = papers.map { "${it.millimeters} mm" },
                    selectedIndex = papers.indexOf(printer.paper),
                    onSelect = { onPaper(papers[it]) },
                )
                if (slot == PrinterSlot.Receipt && notice != PrinterNotice.LogoCheck) {
                    val stored = !printer.logoOff && printer.logoVersion == ReceiptLogo.Version
                    if (printer.logoOff || stored) {
                        AppText(
                            text = stringResource(if (printer.logoOff) Res.string.printer_logo_off else Res.string.printer_logo_stored),
                            role = TextRole.Caption,
                            color = colors.contentMuted,
                        )
                    }
                }
            }
            // Satu pertanyaan setelah kertas uji berlogo keluar, karena printer tidak bisa melaporkan hasil cetaknya.
            if (notice == PrinterNotice.LogoCheck) {
                AppText(text = stringResource(Res.string.printer_logo_check), role = TextRole.Body, color = colors.content)
                Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                    SecondaryButton(text = stringResource(Res.string.printer_logo_no), onClick = { onConfirmLogo(false) }, modifier = Modifier.weight(1f))
                    PrimaryButton(text = stringResource(Res.string.printer_logo_yes), onClick = { onConfirmLogo(true) }, modifier = Modifier.weight(1f))
                }
            }
            notice?.takeIf { it != PrinterNotice.LogoCheck }?.let { value -> NoticeMessage(value) }
            if (printer == null) {
                PrimaryButton(
                    text = stringResource(if (busy) Res.string.printer_searching else Res.string.printer_pair),
                    onClick = onPair,
                    enabled = !anyBusy,
                    loading = busy,
                )
            } else if (notice != PrinterNotice.LogoCheck) {
                Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                    SecondaryButton(
                        text = stringResource(Res.string.printer_forget),
                        onClick = onForget,
                        enabled = !anyBusy,
                        tone = ButtonTone.Danger,
                        modifier = Modifier.weight(1f),
                    )
                    SecondaryButton(text = stringResource(Res.string.printer_repair), onClick = onPair, enabled = !anyBusy, modifier = Modifier.weight(1f))
                    PrimaryButton(text = stringResource(Res.string.printer_test), onClick = onCheck, enabled = !anyBusy, loading = busy, modifier = Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
private fun NoticeMessage(notice: PrinterNotice) {
    val good = notice == PrinterNotice.TestPrinted || notice == PrinterNotice.LogoStored
    InlineMessage(
        text = stringResource(
            when (notice) {
                PrinterNotice.TestPrinted -> Res.string.printer_notice_test_printed
                PrinterNotice.NothingFound -> Res.string.printer_notice_nothing_found
                PrinterNotice.ScanNoPermission -> Res.string.printer_notice_no_permission
                PrinterNotice.ScanBluetoothOff -> Res.string.printer_notice_bluetooth_off
                PrinterNotice.LogoStored, PrinterNotice.LogoCheck -> Res.string.printer_notice_logo_stored
                PrinterNotice.LogoOff -> Res.string.printer_notice_logo_full
                is PrinterNotice.Failed -> when (notice.outcome) {
                    PrintOutcome.NoPermission -> Res.string.printer_notice_no_permission
                    PrintOutcome.BluetoothOff -> Res.string.printer_notice_bluetooth_off
                    PrintOutcome.Interrupted -> Res.string.printer_notice_interrupted
                    PrintOutcome.NotAPrinter -> Res.string.printer_notice_not_a_printer
                    else -> Res.string.printer_notice_unreachable
                }
            },
        ),
        tone = if (good) MessageTone.Success else MessageTone.Error,
    )
}

/** Nama slot printer untuk layar dan pesan: struk pembayaran, atau nama stasiun dari rencana cetak. */
@Composable
internal fun printerSlotName(slot: PrinterSlot, plan: PrintPlan?): String = when {
    slot == PrinterSlot.Receipt -> stringResource(Res.string.printer_role_receipt)
    slot.stationId != null -> plan?.station(slot.stationId!!)?.name ?: stringResource(Res.string.printer_role_station)
    slot == PrinterSlot.LegacyBar -> stringResource(Res.string.printer_role_bar)
    slot == PrinterSlot.LegacyKitchen -> stringResource(Res.string.printer_role_kitchen)
    else -> stringResource(Res.string.printer_role_station)
}

/** Keterangan di bawah nama slot: untuk apa printernya dan siapa yang mengirim cetakannya. */
@Composable
private fun slotExplanation(slot: PrinterSlot, plan: PrintPlan): String {
    val station = slot.stationId?.let(plan::station) ?: return stringResource(Res.string.printer_slot_receipt)
    return when {
        station.held -> stringResource(Res.string.printer_slot_held, station.name)
        station.delivers -> stringResource(Res.string.printer_slot_sent_delivery, station.name)
        else -> stringResource(Res.string.printer_slot_sent, station.name)
    }
}

private fun linkLabel(link: PrinterLink, busy: Boolean) = when {
    busy -> Res.string.printer_connecting
    link == PrinterLink.Ready -> Res.string.printer_ready
    link == PrinterLink.Offline -> Res.string.printer_offline
    link == PrinterLink.Connecting -> Res.string.printer_connecting
    else -> Res.string.printer_not_paired
}
