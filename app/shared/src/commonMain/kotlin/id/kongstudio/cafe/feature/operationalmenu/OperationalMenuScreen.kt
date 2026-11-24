package id.kongstudio.cafe.feature.operationalmenu

import id.kongstudio.cafe.feature.operational.OperationalDestination
import id.kongstudio.cafe.feature.operational.OperationalGroup
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.nav_more
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Halaman Menu untuk layar sempit: semua tujuan yang boleh dibuka, dikelompokkan seperti di rail. */
@Composable
internal fun OperationalMenuScreen(
    destinations: List<OperationalDestination>,
    onSelect: (OperationalDestination) -> Unit,
    signOutLabel: String,
    /** Null selama sesi kasir masih berjalan; keluar baru tersedia setelah sesi ditutup di halaman Sesi Kasir Saya. */
    onSignOut: (() -> Unit)?,
    modifier: Modifier = Modifier,
) {
    val groups = OperationalGroup.entries.mapNotNull { group ->
        destinations.filter { it.group == group }.takeIf { it.isNotEmpty() }?.let { group to it }
    }

    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        LazyColumn(
            modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).fillMaxHeight(),
            contentPadding = PaddingValues(horizontal = AppTheme.windowSize.pagePadding, vertical = AppTheme.spacing.lg),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
        ) {
            groups.forEach { (group, items) ->
                item(key = group.name) {
                    SectionTitle(text = stringResource(group.label))
                }
                item(key = "${group.name}-items") {
                    ListCard {
                        DividedItems(items) { destination ->
                            ListRow(
                                title = stringResource(destination.label),
                                leading = { IconBadge(destination.icon) },
                                trailing = { IconBadge(AppIcons.ChevronRight) },
                                onClick = { onSelect(destination) },
                            )
                        }
                    }
                }
            }
            if (onSignOut != null) {
                item(key = "sign-out") {
                    ListCard {
                        ListRow(
                            title = signOutLabel,
                            leading = { IconBadge(AppIcons.Logout) },
                            onClick = onSignOut,
                        )
                    }
                }
            }
        }
    }
}

/** Judul tab Menu di bilah bawah; satu tempat supaya rail dan bilah bawah tidak punya dua tafsir. */
@Composable
internal fun menuTabLabel(): String = stringResource(Res.string.nav_more)
