package id.kongstudio.cafe.feature.notices

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.notice_due_changed
import id.kongstudio.cafe.resources.notice_task_assigned
import id.kongstudio.cafe.resources.notice_task_overdue
import id.kongstudio.cafe.resources.notices_close
import id.kongstudio.cafe.resources.notices_title
import id.kongstudio.cafe.ui.component.noticesheet.NoticeSheet
import id.kongstudio.cafe.ui.component.noticesheet.NoticeSheetItem
import io.ktor.client.HttpClient
import org.jetbrains.compose.resources.stringResource

/** Lembar pengumuman yang muncul sendiri setelah masuk bila ada yang perlu disampaikan. */
@Composable
internal fun NoticeRoute(session: LoginSession, client: HttpClient, onSessionExpired: () -> Unit) {
    val repository = remember(session.accessToken) {
        KtorNoticeRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken))
    }
    val viewModel = viewModel(key = "notices-${session.accessToken}") {
        NoticeViewModel(repository, onSessionExpired)
    }
    val items by viewModel.items.collectAsState()
    if (items.isEmpty()) return

    NoticeSheet(
        title = stringResource(Res.string.notices_title),
        items = items.map { NoticeSheetItem(title = it.text(), caption = it.showAt?.let { stamp -> whenLabel(stamp) }) },
        closeLabel = stringResource(Res.string.notices_close),
        onClose = viewModel::close,
    )
}

@Composable
private fun NoticeItem.text(): String = when (kind) {
    NoticeKind.TaskAssigned -> stringResource(Res.string.notice_task_assigned, title)
    NoticeKind.TaskOverdue -> stringResource(Res.string.notice_task_overdue, title)
    NoticeKind.DueChanged -> stringResource(Res.string.notice_due_changed, title)
}
