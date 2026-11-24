<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { BranchReadiness } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { ROUTE_LOOKS } from '$lib/features/printers/printers.svelte';
	import { live } from '$lib/live/live';
	import { BRANCH_TABS, branchPath, type BranchTab } from '$lib/nav/pages';
	import { branchDetailText } from '$lib/text/branch-detail';
	import { format } from '$lib/text/format';

	/** Satu daftar periksa sebelum cabang siap jualan; setiap butir yang kurang menunjuk tempat memperbaikinya. */
	let { branchId }: { branchId: string } = $props();

	const text = branchDetailText.readiness;

	type Item = { key: string; title: string; detail: string; tone: 'success' | 'warning' | 'danger'; fix?: { label: string; tab: BranchTab } };

	const TABLES = ['outlets', 'cafe_settings', 'devices', 'device_stations', 'device_station_prints', 'device_printers', 'stations', 'category_stations', 'category_branch_stations'];

	let data = $state<BranchReadiness | null>(null);
	let problem = $state('');

	async function load(): Promise<void> {
		try {
			data = await api.branches.readiness(branchId);
			problem = '';
		} catch (failure) {
			problem = userMessage(failure, text.failed);
		}
	}

	onMount(() => {
		void load();
		return live.on(TABLES, () => void load());
	});

	const items = $derived.by((): Item[] => {
		if (!data) return [];
		const stations: Item[] = data.stations
			.filter((route) => route.kind === 'make' && route.state !== 'unused')
			.map((route) => {
				const look = ROUTE_LOOKS[route.state];
				const holder = route.holders.at(0);
				const sender = route.sender?.name ?? text.cashierTablet;
				const where = holder ? format(text.stationReady, { holder: holder.name }) : format(text.stationNoTablet, { station: route.station_name, sender });
				return {
					key: route.station_id,
					title: format(text.stationTitle, { name: route.station_name }),
					detail: route.state === 'ready' ? where : format(text.stationFix, { look: look.label, sender }),
					tone: route.state === 'ready' ? 'success' : route.state === 'printer_disconnected' ? 'danger' : 'warning',
					fix: route.state === 'ready' ? undefined : { label: text.stationsLink, tab: BRANCH_TABS.printers }
				};
			});
		return [
			{
				key: 'receipt',
				title: text.receiptTitle,
				detail: data.settings_ready ? text.receiptReady : text.receiptMissing,
				tone: data.settings_ready ? 'success' : 'warning',
				fix: data.settings_ready ? undefined : { label: text.receiptLink, tab: BRANCH_TABS.receipt }
			},
			{
				key: 'location',
				title: text.locationTitle,
				detail: data.location_ready ? text.locationReady : text.locationMissing,
				tone: data.location_ready ? 'success' : 'warning'
			},
			{
				key: 'cashier',
				title: text.cashierTitle,
				detail: data.cashier_name ?? text.cashierMissing,
				tone: data.cashier_name ? 'success' : 'warning',
				fix: data.cashier_name ? undefined : { label: text.devicesLink, tab: BRANCH_TABS.devices }
			},
			...stations
		];
	});
	const done = $derived(items.filter((item) => item.tone === 'success').length);
	const ICONS = { success: 'circle-check', warning: 'alert-triangle', danger: 'plug-connected-x' } as const;
	const INK = { success: 'text-success-500', warning: 'text-warning-500', danger: 'text-danger-500' } as const;
</script>

<Card class="laptop:col-span-2">
	<CardHeader class="mb-4" title={text.title} description={text.description}>
		{#snippet actions()}
			{#if data}
				<Badge tone={done === items.length ? 'success' : 'warning'}>
					<i class="ti {done === items.length ? 'ti-circle-check' : 'ti-alert-triangle'}" aria-hidden="true"></i>{done === items.length ? text.ready : format(text.progress, { done, total: items.length })}
				</Badge>
			{/if}
		{/snippet}
	</CardHeader>
	{#if problem}
		<Notice text={problem} />
	{:else if !data}
		<Notice text={text.loading} loading />
	{:else}
		<ul class="grid gap-3 tablet:grid-cols-2">
			{#each items as item (item.key)}
				<li class="flex items-start justify-between gap-3">
					<span class="flex min-w-0 items-start gap-2">
						<i class="ti ti-{ICONS[item.tone]} mt-0.5 {INK[item.tone]}" aria-hidden="true"></i>
						<span class="min-w-0">
							<span class="block text-sm font-semibold text-slate-800">{item.title}</span>
							<span class="block break-words text-xs text-slate-500">{item.detail}</span>
						</span>
					</span>
					{#if item.fix}
						<a href={branchPath(branchId, item.fix.tab)} class="shrink-0 text-xs font-semibold text-brand hover:underline">{item.fix.label}</a>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</Card>
