package id.kongstudio.cafe.feature.release

import id.kongstudio.cafe.resources.release_apk_routine_tasks
import id.kongstudio.cafe.resources.release_apk_task_sections
import id.kongstudio.cafe.resources.release_apk_fix_submission
import id.kongstudio.cafe.resources.release_apk_follow_up_source
import id.kongstudio.cafe.resources.release_apk_photo_retry
import id.kongstudio.cafe.resources.release_apk_menu_order
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.StringResource

// Diganti setiap rilis APK dan dibaca juga oleh halaman Unduhan lewat generate-release.mjs, jadi bentuk barisnya dijaga tetap.
internal val ApkReleaseNotes: List<Pair<StringResource, ImageVector>> = listOf(
    Res.string.release_apk_routine_tasks to AppIcons.CalendarCheck,
    Res.string.release_apk_task_sections to AppIcons.Checklist,
    Res.string.release_apk_fix_submission to AppIcons.Refresh,
    Res.string.release_apk_follow_up_source to AppIcons.FileText,
    Res.string.release_apk_photo_retry to AppIcons.PhotoOff,
    Res.string.release_apk_menu_order to AppIcons.Category,
)
