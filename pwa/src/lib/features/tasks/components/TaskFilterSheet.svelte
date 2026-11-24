<script lang="ts">
	import IconButton from '$lib/components/button/IconButton.svelte';
	import ChoiceFlow from '$lib/components/choice/ChoiceFlow.svelte';
	import DateRangeFields from '$lib/components/field/DateRangeFields.svelte';
	import DropdownField from '$lib/components/field/DropdownField.svelte';
	import type { DropdownOption } from '$lib/components/field/types';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { todayWib } from '$lib/format/datetime';
	import { t } from '$lib/text/t';
	import { ServerClock } from '$lib/time/server-clock';
	import type { TaskPeriod, TasksState } from '../tasks.svelte';

	const PERIODS: TaskPeriod[] = ['month', 'today', 'week', 'custom'];
	const PERIOD_LABELS = { month: 'tasks_filter_period_month', today: 'tasks_filter_period_today', week: 'tasks_filter_period_week', custom: 'tasks_filter_period_custom' } as const;

	/** Lembar penyaring daftar tugas: tanggal, orang, dan cabang. Setiap pilihan langsung berlaku tanpa tombol terapkan, dan ikon di pojok bawah mengembalikan semuanya ke bawaan. */
	let { tasks, ownUserId, onDismiss }: { tasks: TasksState; ownUserId: string; onDismiss: () => void } = $props();

	const people = $derived<DropdownOption[]>([
		{ key: null, label: t('tasks_filter_person_all') },
		{ key: ownUserId, label: t('tasks_filter_person_mine') },
		...(tasks.options?.assignees ?? []).filter((person) => person.id !== ownUserId).map((person) => ({ key: person.id, label: person.name }))
	]);
	const outlets = $derived<DropdownOption[]>([{ key: null, label: t('tasks_filter_outlet_all') }, ...(tasks.options?.outlets ?? []).map((outlet) => ({ key: outlet.id, label: outlet.name }))]);
</script>

<BottomSheet title={t('tasks_filter_title')} {onDismiss}>
	<div class="flex w-full flex-col gap-3">
		<AppText role="caption" color="content-muted">{t('tasks_filter_count', String(tasks.total))}</AppText>
		<ChoiceFlow label={t('tasks_filter_date')} options={PERIODS.map((period) => t(PERIOD_LABELS[period]))} selectedIndex={PERIODS.indexOf(tasks.period)} onselect={(index) => tasks.setPeriod(PERIODS[index] ?? 'month')} />
		{#if tasks.period === 'custom'}
			<DateRangeFields
				from={tasks.customFrom}
				to={tasks.customTo}
				today={todayWib(ServerClock.nowEpochSeconds())}
				fromLabel={t('tasks_filter_from')}
				toLabel={t('tasks_filter_to')}
				onchange={(from, to) => tasks.setCustomRange(from, to)}
				sideBySide
			/>
		{/if}
		<DropdownField
			label={t('tasks_filter_person')}
			options={people}
			selectedKey={tasks.assigneeId}
			onSelect={(key) => tasks.setAssignee(key)}
			searchLabel={t('tasks_filter_person_search')}
			emptyText={t('tasks_filter_no_match')}
		/>
		<DropdownField label={t('tasks_filter_outlet')} options={outlets} selectedKey={tasks.outletId} onSelect={(key) => tasks.setOutlet(key)} />
		<div class="flex items-center gap-3">
			<div class="flex-1"><AppText role="caption" color="content-muted">{t('tasks_filter_hint')}</AppText></div>
			<IconButton icon="Refresh" label={t('tasks_filter_reset')} onclick={() => tasks.resetFilters()} tint="primary" container="selected" />
		</div>
	</div>
</BottomSheet>
