package id.kongstudio.cafe.feature.release

import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.release_apk_order_type
import id.kongstudio.cafe.resources.release_apk_phone
import id.kongstudio.cafe.resources.release_apk_repair
import id.kongstudio.cafe.resources.release_fix_clipped_numbers
import id.kongstudio.cafe.resources.release_fix_restored_order
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.StringResource

// Milik klien dan diganti setiap rilis APK; dibaca juga oleh halaman Unduhan lewat generate-release.mjs, jadi bentuk barisnya dijaga tetap.
internal val ApkReleaseNotes: List<Pair<StringResource, ImageVector>> = listOf(
    Res.string.release_apk_phone to AppIcons.DeviceMobile,
    Res.string.release_apk_order_type to AppIcons.ShoppingBag,
    Res.string.release_apk_repair to AppIcons.Refresh,
)

// Perbaikan yang dibawa rilis APK ini, tampil terpisah dari "Yang baru"; daftar kosong berarti bagiannya tidak tampil.
internal val ApkReleaseFixes: List<Pair<StringResource, ImageVector>> = listOf(
    Res.string.release_fix_clipped_numbers to AppIcons.Check,
    Res.string.release_fix_restored_order to AppIcons.Check,
)
