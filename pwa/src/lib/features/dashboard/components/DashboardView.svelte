<script lang="ts">
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import ExpandableCard from '$lib/components/card/ExpandableCard.svelte';
	import IconPill from '$lib/components/card/IconPill.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import StatCard from '$lib/components/card/StatCard.svelte';
	import CenteredStat from '$lib/components/card/CenteredStat.svelte';
	import StateListCard from '$lib/components/card/StateListCard.svelte';
	import UserCard from '$lib/components/card/UserCard.svelte';
	import ProgressRing from '$lib/components/chart/ProgressRing.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import BannerBackdrop from '$lib/components/layout/BannerBackdrop.svelte';
	import ScaleToHeight from '$lib/components/layout/ScaleToHeight.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { current } from '$lib/auth/current.svelte';
	import { durationLabel, formatRupiah, whenLabel } from '$lib/format/labels';
	import { t, tArray } from '$lib/text/t';
	import type { StringKey } from '$lib/text/strings';
	import { DashboardState, type PendingKind } from '../dashboard.svelte';
	import { dynamicStyle } from '$lib/platform/dynamic-style';

	/** Tinggi alami tiap blok jadi bobot sekaligus acuan skala, jadi semua blok membesar atau mengecil bersama. */
	const BANNER_BASELINE = 252;
	const TILE_BASELINE = 112;
	const TILE_BASELINE_WIDTH = 140;
	const CONTENT_BASELINE = TILE_BASELINE * 3 + 12 * 2 + 16;
	const PERCENT_FULL = 100;

	let { onOpenAttendance, onSessionExpired }: { onOpenAttendance: () => void; onSessionExpired: () => void } = $props();

	const dashboard = new DashboardState(() => onSessionExpired());

	$effect(() => {
		void dashboard.load();
	});

	// Dimuat ulang setiap app kembali dari latar belakang, agar data tidak basi.
	$effect(() => {
		const reload = () => document.visibilityState === 'visible' && void dashboard.load();
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});

	const user = $derived(current.session?.user);
	const headerName = $derived(dashboard.profile?.name ?? user?.name ?? user?.username ?? '');
	const headerSubtitle = $derived([dashboard.profile?.roleName ?? user?.roleName, dashboard.profile?.outletName].filter(Boolean).join(' · '));

	const attendance = $derived(dashboard.attendance);
	const total = $derived(attendance ? attendance.present + attendance.notPresent : 0);
	const progress = $derived(attendance && total > 0 ? attendance.present / total : 0);
	const heroLabel = $derived(attendance ? t('dashboard_hero_label', tArray('months')[attendance.month.month - 1] ?? '', String(attendance.month.year)) : t('dashboard_section_attendance'));
	const heroValue = $derived(attendance ? t('dashboard_hero_value', String(attendance.present), String(total)) : t('dashboard_hero_empty'));
	const heroSub = $derived(attendance ? t('dashboard_hero_sub', String(attendance.late), String(attendance.notPresent)) : t('common_loading'));
	const taskValue = $derived(dashboard.loading ? t('dashboard_hero_empty') : t('dashboard_task_count', String(dashboard.pendingTasks.length)));
	const personalCount = $derived(dashboard.pendingTasks.filter((task) => task.kind === 'personal').length);
	const routineCount = $derived(dashboard.pendingTasks.filter((task) => task.kind === 'routine').length);
	const outletCount = $derived(dashboard.pendingTasks.filter((task) => task.kind === 'outlet').length);
	const KIND_BADGE: Record<PendingKind, { text: StringKey; tone: 'positive' | 'strong' | 'accent' }> = {
		personal: { text: 'dashboard_task_kind_personal', tone: 'positive' },
		routine: { text: 'dashboard_task_kind_routine', tone: 'strong' },
		outlet: { text: 'dashboard_task_kind_outlet', tone: 'accent' }
	};
</script>

<div class="flex h-full w-full flex-col items-center" data-expand-host>
	<div class="w-full min-h-0" use:dynamicStyle={{ flex: `${BANNER_BASELINE} 1 0%` }}>
		<ScaleToHeight baseline={BANNER_BASELINE}>
			<BannerBackdrop>
				<div class="mx-auto flex w-full max-w-[var(--size-content-max)] flex-col gap-2" use:dynamicStyle={{ 'padding-inline': 'var(--page-padding)' }}>
					<UserCard name={headerName} subtitle={headerSubtitle} photoUrl={dashboard.profile?.photoUrl} tag={dashboard.todayAssignment} containerColor="transparent" padding="16px 0" />
					{#if !dashboard.failure}
						<ExpandableCard containerColor="transparent" actionColor="on-primary-subtle" actionTint="on-primary" openLabel={t('dashboard_open_attendance')} closeLabel={t('sheet_close')} padding="16px 0" onOpen={onOpenAttendance}>
							{#snippet leading()}
								<ProgressRing {progress} label="{Math.round(progress * PERCENT_FULL)}%" trackColor="on-primary-subtle" indicatorColor="accent" labelColor="on-primary" />
							{/snippet}
							{#snippet head()}
								<AppText role="caption" color="on-primary-muted">{heroLabel}</AppText>
								<AppText role="title" color="on-primary">{heroValue}</AppText>
								<AppText role="caption" color="on-primary-muted">{heroSub}</AppText>
							{/snippet}
						</ExpandableCard>
					{/if}
				</div>
			</BannerBackdrop>
		</ScaleToHeight>
	</div>

	<div class="flex w-full min-h-0 max-w-[var(--size-content-max)] flex-col gap-3" use:dynamicStyle={{ flex: `${CONTENT_BASELINE} 1 0%`, padding: '0 var(--page-padding) 16px' }}>
		{#if dashboard.failure}
			<ListCard><FailureState failure={dashboard.failure} onRetry={() => void dashboard.load()} /></ListCard>
		{:else}
			{#if attendance}
				<div class="flex min-h-0 gap-2" use:dynamicStyle={{ flex: `${TILE_BASELINE} 1 0%` }}>
					<div class="min-w-0 flex-1">
						<ScaleToHeight baseline={TILE_BASELINE} baselineWidth={TILE_BASELINE_WIDTH}>
							<StatCard label={t('dashboard_stat_work')} value={durationLabel(attendance.workMinutes)} icon="Clock" centered fill />
						</ScaleToHeight>
					</div>
					<div class="min-w-0 flex-1">
						<ScaleToHeight baseline={TILE_BASELINE} baselineWidth={TILE_BASELINE_WIDTH}>
							<StatCard label={t('dashboard_stat_overtime')} value={durationLabel(attendance.overtimeMinutes)} icon="History" centered fill />
						</ScaleToHeight>
					</div>
				</div>
				<div class="min-h-0" use:dynamicStyle={{ flex: `${TILE_BASELINE} 1 0%` }}>
					<ScaleToHeight baseline={TILE_BASELINE} baselineWidth={TILE_BASELINE_WIDTH}>
						<StatCard label={t('dashboard_stat_penalty')} value={formatRupiah(attendance.penalty)} valueColor={attendance.penalty > 0 ? 'danger' : 'content'} icon="Alert" centered fill />
					</ScaleToHeight>
				</div>
			{/if}
			<div class="min-h-0" use:dynamicStyle={{ flex: `${TILE_BASELINE} 1 0%` }}>
				<ScaleToHeight baseline={TILE_BASELINE}>
					<ExpandableCard containerColor="surface" actionColor="selected" actionTint="primary" centered fill openLabel={t('dashboard_open_tasks')} closeLabel={t('sheet_close')} padding="12px">
						{#snippet head(expanded)}
							<CenteredStat
								label={t('dashboard_task_label')}
								value={taskValue}
								icon="Checklist"
								caption={!dashboard.loading && dashboard.pendingTasks.length === 0 ? t('dashboard_empty_tasks') : null}
							/>
							{#if expanded && !dashboard.loading && dashboard.pendingTasks.length > 0}
								<div class="mt-2 flex flex-wrap justify-center gap-2">
									<IconPill icon="User" text={t('dashboard_task_personal', String(personalCount))} />
									<IconPill icon="CalendarCheck" text={t('dashboard_task_routine', String(routineCount))} container="primary" content="on-primary" />
									<IconPill icon="UsersGroup" text={t('dashboard_task_outlet', String(outletCount))} container="accent" />
								</div>
							{/if}
						{/snippet}
						{#snippet body()}
							<StateListCard loading={dashboard.loading} empty={dashboard.pendingTasks.length === 0} emptyText={t('dashboard_empty_tasks')} skeletonRows={2}>
								<DividedItems items={dashboard.pendingTasks}>
									{#snippet row(task)}
										<ListRow title={task.title} caption={task.caption ?? (task.due ? t('dashboard_task_due', whenLabel(task.due)) : null)}>
											{#snippet trailing()}
												<StatusBadge text={t(KIND_BADGE[task.kind].text)} tone={KIND_BADGE[task.kind].tone} />
											{/snippet}
										</ListRow>
									{/snippet}
								</DividedItems>
							</StateListCard>
						{/snippet}
					</ExpandableCard>
				</ScaleToHeight>
			</div>
		{/if}
	</div>
</div>
