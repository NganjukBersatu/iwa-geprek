<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import type { ManagedStation } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import FilterButton from '$lib/components/filter/FilterButton.svelte';
	import FilterChips from '$lib/components/filter/FilterChips.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { live } from '$lib/live/live';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { NEW_STATION_PATH, stationPath } from '$lib/nav/pages';
	import { loadBranchOptions } from '$lib/stores/branch';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { formatTarget, KIND_LABEL } from '../labels';
	import { DIRECT_LABEL, type CategoryRow, type SetupState } from '../setup.svelte';
	import CategoryRouteDialog from './CategoryRouteDialog.svelte';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';
	import { stationText } from '$lib/text/stations';
	import { termText } from '$lib/text/terms';

	let { setup }: { setup: SetupState } = $props();

	whenChanged(() => setup.branch, () => void setup.load());
	onMount(() => {
		void loadBranchOptions().then((options) => setup.filters.setOptions('cabang', options));
		return live.on(setup.tables, () => void setup.load(true));
	});

	const data = $derived(setup.data);
	const branchChosen = $derived(setup.branch !== null);
	const workStations = $derived((data?.stations ?? []).filter((station) => station.kind !== 'handover'));
	const cashierStations = $derived((data?.stations ?? []).filter((station) => station.kind === 'handover'));
	const usedText = (row: ManagedStation) => (row.used ? stationText.setupActive : stationText.setupInactive);
	const showTablets = $derived(branchChosen && setup.coverage !== null);
	const tabletText = (row: ManagedStation): string => {
		const names = setup.holders(row);
		if (names === null) return EMPTY_VALUE;
		return names.length > 0 ? names.join(', ') : stationText.setupNoTablet;
	};
	const tabletColumn: Column<ManagedStation> = { key: 'tablet', label: stationText.tablet, align: 'left', value: tabletText };

	const stationColumns = $derived<Column<ManagedStation>[]>([
		{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => row.name },
		{ key: 'jenis', label: termText.kind, align: 'left', value: (row) => KIND_LABEL[row.kind] },
		{ key: 'target', label: stationText.target, align: 'left', value: (row) => (row.kind === 'make' ? stationText.setupTimePerMenu : formatTarget(row.branch_target_seconds ?? row.target_seconds)) },
		{ key: 'kategori', label: termText.category, align: 'left', value: (row) => (row.kind === 'make' ? row.categories.join(', ') || stationText.setupNoCategory : stationText.setupEveryMadeItem) },
		...(branchChosen ? [{ key: 'aktif', label: stationText.inThisBranch, align: 'left' as const, value: usedText }] : []),
		...(showTablets ? [tabletColumn] : [])
	]);

	const cashierColumns = $derived<Column<ManagedStation>[]>([
		{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => row.name },
		{ key: 'isi', label: stationText.cashierContent, align: 'left', value: () => stationText.cashierContentValue },
		{ key: 'selesai', label: stationText.cashierDone, align: 'left', value: () => stationText.cashierDoneValue },
		...(branchChosen ? [{ key: 'aktif', label: stationText.inThisBranch, align: 'left' as const, value: usedText }] : []),
		...(showTablets ? [tabletColumn] : [])
	]);

	const categoryColumns = $derived<Column<CategoryRow>[]>([
		{ key: 'kategori', label: termText.category, align: 'left', value: (row) => (row.first ? row.categoryName : '') },
		{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => setup.stationName(row.stationId) },
		{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => (row.outletId ? row.outletName : termText.allBranches) }
	]);

	const removing = $derived(setup.removing);
	const fallbackStation = $derived(removing ? setup.stationName(data?.categories.find((category) => category.id === removing.categoryId)?.station_id ?? null) : '');
	const removeWhere = $derived(fallbackStation === DIRECT_LABEL ? stationText.fixRemoveDirect : format(stationText.fixRemoveToStation, { station: fallbackStation }));
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={stationText.setupTitle} description={stationText.setupIntro}>
		{#snippet actions()}
			<FilterButton filters={setup.filters} />
			<Button label={stationText.new} icon="plus" variant="primary" href={NEW_STATION_PATH} />
		{/snippet}
	</PageHeader>

	<FilterChips filters={setup.filters} />

	{#if setup.error}
		<Banner tone="danger" icon="alert-triangle" title={stationText.setupLoadFailedTitle}>
			{setup.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void setup.load()} />
			{/snippet}
		</Banner>
	{:else if setup.loading && !data}
		<SkeletonPage label={stationText.setupLoading} />
	{:else if data}
		{#if setup.actionError && !setup.form && !setup.removing}
			<Banner tone="danger" icon="alert-triangle">{setup.actionError}</Banner>
		{/if}

		<Card flush>
			<CardHeader divided title={termText.station} description={stationText.setupStationsDescription} icon="tools-kitchen-2" />
			{#if workStations.length === 0}
				<Notice text={stationText.setupNoWorkStations} />
			{:else}
				<DataTable columns={stationColumns} rows={workStations} rowKey={(row) => row.id} onopen={(row) => void goto(stationPath(row.id))}>
					{#snippet cell(row, column)}
						{#if column.key === 'aktif'}
							<Badge tone={row.used ? 'success' : 'neutral'}>{column.value(row)}</Badge>
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
				</DataTable>
			{/if}
		</Card>

		<Card flush>
			<CardHeader divided title={stationText.cashierTitle} description={stationText.cashierDescription} icon="receipt" />
			{#if cashierStations.length === 0}
				<Notice text={stationText.noCashier} />
			{:else}
				<DataTable columns={cashierColumns} rows={cashierStations} rowKey={(row) => row.id} onopen={(row) => void goto(stationPath(row.id))}>
					{#snippet cell(row, column)}
						{#if column.key === 'aktif'}
							<Badge tone={row.used ? 'success' : 'neutral'}>{column.value(row)}</Badge>
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
				</DataTable>
			{/if}
		</Card>

		<Card flush>
			<CardHeader divided title={stationText.categoryRoutingHeading} description={stationText.categoryRoutingBody} icon="category">
				{#snippet actions()}
					{#if data.categories.length > 0}
						<Button label={stationText.addBranchRow} icon="plus" compact onclick={() => setup.openAdd()} />
					{/if}
				{/snippet}
			</CardHeader>
			{#if data.categories.length === 0}
				<Notice text={stationText.noMenuCategories} />
			{:else}
				<DataTable columns={categoryColumns} rows={setup.rows} rowKey={(row) => row.id}>
					{#snippet cell(row, column)}
						{#if column.key === 'cabang'}
							<Badge tone={row.outletId ? 'info' : 'neutral'}>{column.value(row)}</Badge>
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
					{#snippet actions(row)}
						<Button label={actionText.edit} icon="pencil" compact disabled={setup.busy} onclick={() => setup.openEdit(row)} />
						{#if row.outletId}
							<Button label={actionText.remove} icon="trash" variant="danger" compact disabled={setup.busy} onclick={() => setup.askRemove(row)} />
						{/if}
					{/snippet}
				</DataTable>
			{/if}
		</Card>
	{/if}
</div>

<CategoryRouteDialog {setup} />
<ConfirmDialog
	open={removing !== null}
	title={removing ? format(stationText.fixRemoveTitle, { branch: removing.outletName, category: removing.categoryName }) : ''}
	confirmLabel={stationText.fixRemoveConfirm}
	danger
	busy={setup.busy}
	error={setup.actionError}
	onconfirm={() => void setup.remove()}
	oncancel={() => setup.closeDialogs()}
>
	{#if removing}
		{format(stationText.fixRemoveNote, { category: removing.categoryName, branch: removing.outletName, where: removeWhere })}
		{#if fallbackStation !== DIRECT_LABEL}{format(stationText.fixRemoveReady, { station: fallbackStation, branch: removing.outletName })}{/if}
	{/if}
</ConfirmDialog>
