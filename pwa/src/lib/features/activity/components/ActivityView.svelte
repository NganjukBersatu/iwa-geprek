<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import IconBadge from '$lib/components/card/IconBadge.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import ChoiceRow from '$lib/components/choice/ChoiceRow.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import PagedListCard from '$lib/components/pagination/PagedListCard.svelte';
	import { whenLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { ACTIVITY_GROUPS, ActivityState, eventDetail, eventIcon, eventTitle } from '../activity.svelte';

	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const activity = new ActivityState(() => onSessionExpired());

	$effect(() => {
		void activity.load();
	});
</script>

<div class="flex size-full justify-center overflow-y-auto" use:dynamicStyle={{ 'padding-inline': 'var(--page-padding)' }}>
	<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-3" use:dynamicStyle={{ 'padding-bottom': '24px' }}>
		<ChoiceRow
			label={t('activity_filter_label')}
			options={ACTIVITY_GROUPS.map((group) => t(group.label))}
			selectedIndex={ACTIVITY_GROUPS.indexOf(activity.group)}
			onselect={(index) => {
				const group = ACTIVITY_GROUPS[index];
				if (group) activity.select(group);
			}}
		/>
		{#if activity.failure}
			<ListCard><FailureState failure={activity.failure} onRetry={() => activity.retry()} /></ListCard>
		{:else}
			<PagedListCard
				items={activity.pageEvents}
				page={activity.page}
				pageCount={activity.pageCount}
				onPageChange={(page) => activity.setPage(page)}
				emptyText={t('dashboard_empty_history')}
				loading={activity.loading}
				skeletonRows={4}
			>
				{#snippet row(event)}
					<ListRow title={eventTitle(event)} detail={eventDetail(event)} caption={whenLabel(event.at)}>
						{#snippet leading()}<IconBadge icon={eventIcon(event)} />{/snippet}
					</ListRow>
				{/snippet}
			</PagedListCard>
		{/if}
	</div>
</div>
