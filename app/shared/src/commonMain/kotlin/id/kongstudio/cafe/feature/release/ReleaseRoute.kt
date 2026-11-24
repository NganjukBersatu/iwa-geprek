package id.kongstudio.cafe.feature.release

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.feature.about.appVersionName
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.notices_close
import id.kongstudio.cafe.resources.release_title
import id.kongstudio.cafe.ui.component.noticesheet.NoticeSheet
import id.kongstudio.cafe.ui.component.noticesheet.NoticeSheetItem
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun ReleaseRoute(api: AdminApi, userToken: String, onUnauthorized: () -> Unit) {
    val version = appVersionName()
    val repository = remember(api) { ReleaseRepository(api) }
    val viewModel = viewModel(key = "release-$userToken") { ReleaseViewModel(repository, version, onUnauthorized) }
    val open by viewModel.open.collectAsState()
    if (!open) return

    NoticeSheet(
        title = stringResource(Res.string.release_title, version),
        items = ApkReleaseNotes.map { (text, icon) -> NoticeSheetItem(title = stringResource(text), caption = null, icon = icon) },
        closeLabel = stringResource(Res.string.notices_close),
        onClose = viewModel::close,
    )
}
