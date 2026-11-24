package id.kongstudio.cafe.feature.release

import id.kongstudio.cafe.resources.release_apk_cashier
import id.kongstudio.cafe.resources.release_apk_open_bills
import id.kongstudio.cafe.resources.release_apk_printing
import id.kongstudio.cafe.resources.release_apk_stock
import id.kongstudio.cafe.resources.release_apk_attendance
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.StringResource

// Milik klien dan diganti setiap rilis APK; dibaca juga oleh halaman Unduhan lewat generate-release.mjs, jadi bentuk barisnya dijaga tetap.
internal val ApkReleaseNotes: List<Pair<StringResource, ImageVector>> = listOf(
    Res.string.release_apk_cashier to AppIcons.Cart,
    Res.string.release_apk_open_bills to AppIcons.Receipt,
    Res.string.release_apk_printing to AppIcons.Printer,
    Res.string.release_apk_stock to AppIcons.ClipboardList,
    Res.string.release_apk_attendance to AppIcons.Qrcode,
)
