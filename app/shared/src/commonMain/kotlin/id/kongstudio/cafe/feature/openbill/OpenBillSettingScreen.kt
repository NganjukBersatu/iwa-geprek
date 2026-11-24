package id.kongstudio.cafe.feature.openbill

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.openbill_setting_blocked
import id.kongstudio.cafe.resources.openbill_setting_caption
import id.kongstudio.cafe.resources.openbill_setting_check_failed
import id.kongstudio.cafe.resources.openbill_setting_off_hint
import id.kongstudio.cafe.resources.openbill_setting_title
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.pageframe.PageFrame
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

/** Menyalakan atau mematikan Open Bill di tablet ini; mematikan ditolak selama masih ada bill yang belum dibayar, supaya tidak ada bill yang terkunci. */
@Composable
internal fun OpenBillSettingScreen(
    title: String,
    switch: OpenBillSwitch,
    repository: OpenBillRepository,
    modifier: Modifier = Modifier,
) {
    val enabled by switch.enabled.collectAsState()
    val scope = rememberCoroutineScope()
    var checking by remember { mutableStateOf(false) }
    var unpaid by remember { mutableIntStateOf(0) }
    var checkFailed by remember { mutableStateOf(false) }

    PageFrame(modifier = modifier) {
        item { PageTitle(title = title) }
        item {
            ListCard {
                ListRow(
                    title = stringResource(Res.string.openbill_setting_title),
                    caption = stringResource(Res.string.openbill_setting_caption),
                    leading = { IconBadge(AppIcons.Receipt) },
                    trailing = {
                        ToggleSwitch(
                            label = "",
                            accessibleName = stringResource(Res.string.openbill_setting_title),
                            checked = enabled,
                            onCheckedChange = { next ->
                                if (checking) return@ToggleSwitch
                                unpaid = 0
                                checkFailed = false
                                scope.launch {
                                    if (next) {
                                        switch.set(true)
                                        return@launch
                                    }
                                    checking = true
                                    when (val result = repository.bills()) {
                                        is DeviceResult.Ok -> if (result.value.isEmpty()) switch.set(false) else unpaid = result.value.size
                                        is DeviceResult.Failed -> checkFailed = true
                                    }
                                    checking = false
                                }
                            },
                        )
                    },
                )
            }
        }
        if (unpaid > 0) {
            item { Notice(text = stringResource(Res.string.openbill_setting_blocked, unpaid), icon = AppIcons.Alert) }
        }
        if (checkFailed) {
            item { Notice(text = stringResource(Res.string.openbill_setting_check_failed), icon = AppIcons.Alert) }
        }
        if (!enabled) {
            item { Notice(text = stringResource(Res.string.openbill_setting_off_hint), icon = AppIcons.Info) }
        }
    }
}
