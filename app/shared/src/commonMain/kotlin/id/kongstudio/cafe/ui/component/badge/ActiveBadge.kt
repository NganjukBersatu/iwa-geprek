package id.kongstudio.cafe.ui.component.badge

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.badge_all_branches
import id.kongstudio.cafe.resources.common_active
import id.kongstudio.cafe.resources.common_inactive
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Lencana Aktif atau Nonaktif untuk baris daftar yang bisa dimatikan, supaya keadaannya tidak dibaca sebagai teks biasa. */
@Composable
fun ActiveBadge(active: Boolean) {
    if (active) {
        StatusBadge(text = stringResource(Res.string.common_active), tone = BadgeTone.Positive, icon = AppIcons.Check)
    } else {
        StatusBadge(text = stringResource(Res.string.common_inactive), tone = BadgeTone.Warning, icon = AppIcons.EyeOff)
    }
}

/** Seperti [ActiveBadge], ditambah penanda bila item berlaku di semua cabang sehingga hanya bisa diubah dari web admin. */
@Composable
fun ScopedActiveBadge(active: Boolean, allBranches: Boolean) {
    if (!allBranches) {
        ActiveBadge(active)
        return
    }
    Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm), verticalAlignment = Alignment.CenterVertically) {
        ActiveBadge(active)
        StatusBadge(text = stringResource(Res.string.badge_all_branches), tone = BadgeTone.Neutral)
    }
}
