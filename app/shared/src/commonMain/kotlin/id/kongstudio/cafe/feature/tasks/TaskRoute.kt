package id.kongstudio.cafe.feature.tasks

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.LifecycleResumeEffect
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.batches.KtorBatchRepository
import io.ktor.client.HttpClient

@Composable
internal fun TaskRoute(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val api = remember(session.accessToken) { ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken) }
    val repository = remember(api) { KtorTaskRepository(api) }
    val batchRepository = remember(api) { KtorBatchRepository(api) }
    val viewModel = viewModel(key = "tasks-${session.accessToken}") {
        TaskViewModel(repository, batchRepository, onSessionExpired)
    }
    val state by viewModel.state.collectAsState()

    // Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
    LifecycleResumeEffect(viewModel) {
        viewModel.load()
        viewModel.loadBatches()
        onPauseOrDispose {}
    }

    TaskScreen(
        state = state,
        ownUserId = session.user.id,
        actions = TaskActions(
            onFilterChange = viewModel::setFilter,
            onPeriodChange = viewModel::setPeriod,
            onCustomRangeChange = viewModel::setCustomRange,
            onSearchChange = viewModel::setSearch,
            onAssigneeChange = viewModel::setAssignee,
            onResetFilters = viewModel::resetFilters,
            onOutletChange = viewModel::setOutlet,
            onPageChange = viewModel::setPage,
            onRetry = viewModel::load,
            onLoadOptions = viewModel::loadOptions,
            onCreate = viewModel::create,
            onUpdate = viewModel::update,
            onComplete = viewModel::complete,
            onAddAttachments = viewModel::addAttachments,
            onRemoveAttachment = viewModel::removeAttachment,
            onDelete = viewModel::delete,
            onClearSubmitError = viewModel::clearSubmitError,
            onCompleteBatch = viewModel::completeBatch,
            onClearBatchError = viewModel::clearBatchError,
            onOpenFix = viewModel::openFix,
            onCloseFix = viewModel::closeFix,
            onFixBatch = viewModel::fixBatch,
            onCancelBatch = viewModel::cancelBatch,
            onDeleteBatch = viewModel::deleteBatch,
            onFixCompletion = viewModel::fixCompletion,
            onOpenSourceRun = viewModel::openSourceRun,
            onCloseSourceRun = viewModel::closeSourceRun,
        ),
        modifier = modifier,
    )
}
