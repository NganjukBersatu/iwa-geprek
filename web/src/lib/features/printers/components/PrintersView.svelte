<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import MenuSinglePicker from '$lib/features/menu/components/MenuSinglePicker.svelte';
	import { PAGES } from '$lib/nav/pages';
	import { format } from '$lib/text/format';
	import { printerText as text } from '$lib/text/printers';
	import { routeColumns } from '../columns';
	import { printedAt, ROUTE_LOOKS, shownOn, type PrintersState } from '../printers.svelte';

	let { printers }: { printers: PrintersState } = $props();

	const routes = $derived(printers.routes);
	const readiness = $derived(printers.readiness);
	const allReady = $derived(readiness.used > 0 && readiness.ready === readiness.used);
	const rows = $derived((routes ?? []).map((route) => ({ ...route, id: route.station_id })));
	const preview = $derived(printers.menuRoute);
</script>

{#if routes}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<Card flush>
			<CardHeader divided title={text.stationsTitle} description={text.stationsDescription}>
				{#snippet actions()}
					{#if readiness.used > 0}
						<Badge tone={allReady ? 'success' : 'warning'}>
							<i class="ti {allReady ? 'ti-circle-check' : 'ti-alert-triangle'}" aria-hidden="true"></i>{allReady ? text.ready : format(text.readyOf, { ready: readiness.ready, used: readiness.used })}
						</Badge>
					{/if}
				{/snippet}
			</CardHeader>
			{#if rows.length === 0}
				<Notice text={text.noStations}>
					<Button label={text.openStationSetup} icon="settings" variant="primary" href={PAGES.stationSetup.path} />
				</Notice>
			{:else}
				<DataTable columns={routeColumns} {rows} rowKey={(row) => row.id} loading={printers.loading} trailing="status">
					{#snippet cell(row, column)}
						{#if column.key === 'status'}
							{@const look = ROUTE_LOOKS[row.state]}
							<Badge tone={look.tone}><i class="ti ti-{look.icon}" aria-hidden="true"></i>{look.label}</Badge>
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
				</DataTable>
			{/if}
		</Card>

		<Card>
			<CardHeader title={text.previewTitle} description={text.previewDescription} icon="route" tone="info" />
			<div class="mt-4 flex max-w-md flex-col gap-1">
				<MenuSinglePicker onchoose={(menu) => void printers.preview(menu.id)} />
			</div>
			{#if printers.menuProblem}
				<div class="mt-4"><Notice text={printers.menuProblem} /></div>
			{:else if printers.menuLoading && !preview}
				<div class="mt-4"><Notice text={text.previewLoading} loading /></div>
			{:else if preview}
				{@const route = preview.route}
				{@const steps = [
					{ label: text.stepCategory, value: preview.category_name ?? text.noCategory, icon: 'category', warn: false },
					{
						label: text.stepScreen,
						value: route ? (route.holders.length > 0 ? shownOn(route) : format(text.noStationTablet, { station: route.station_name })) : text.delivered,
						icon: 'device-tablet',
						warn: route?.state === 'unused'
					},
					{ label: text.stepReceipt, value: route ? printedAt(route) : text.notPrinted, icon: 'printer', warn: route !== null && route.state !== 'ready' }
				]}
				<ol class="mt-4 grid gap-2 tablet:grid-cols-3">
					{#each steps as step, index (step.label)}
						<li class="flex items-start gap-2 rounded-xl border p-3 {step.warn ? 'border-warning-200 bg-warning-50' : 'border-slate-100 bg-slate-50'}">
							<i class="ti ti-{step.icon} mt-0.5 {step.warn ? 'text-warning-700' : 'text-brand'}" aria-hidden="true"></i>
							<span class="min-w-0">
								<span class="block text-xs text-slate-500">{index + 1}. {step.label}</span>
								<span class="block break-words text-sm font-semibold text-slate-800">{step.value}</span>
							</span>
						</li>
					{/each}
				</ol>
				{#if route && route.state !== 'ready' && route.state !== 'unused'}
					<p class="mt-2 text-xs text-warning-700">{format(text.fixPrinter, { look: ROUTE_LOOKS[route.state].label, sender: route.sender?.name ?? text.cashierTablet })}</p>
				{/if}
			{/if}
		</Card>
	</div>
{/if}
