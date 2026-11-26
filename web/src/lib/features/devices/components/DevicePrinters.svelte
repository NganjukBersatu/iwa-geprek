<script lang="ts">
	import { api } from '$lib/api';
	import type { StationRoute } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import type { Tone } from '$lib/components/card/tone';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { actionText } from '$lib/text/actions';
	import { deviceText } from '$lib/text/devices';
	import { format } from '$lib/text/format';

	/** Status tiap struk yang dicetak dari satu perangkat, dari jalur cetak cabangnya; [version] berubah saat data perangkat dimuat ulang. */
	let { outletId, deviceId, version }: { outletId: string; deviceId: string; version: string } = $props();

	let routes = $state<StationRoute[] | null>(null);
	let failure = $state('');

	whenChanged(
		() => [outletId, deviceId, version] as const,
		() => void load()
	);

	async function load(): Promise<void> {
		failure = '';
		try {
			routes = (await api.printers.stations(outletId)).stations;
		} catch (cause) {
			failure = userMessage(cause, deviceText.printersLoadFailed);
		}
	}

	// Struk pengantar tanpa printer belum aktif; itu bukan kegagalan, jadi tampil netral.
	const rows = $derived(
		(routes ?? [])
			.filter((route) => route.sender?.device_id === deviceId && (route.state !== 'unused' || route.kind === 'deliver'))
			.map((route) => ({
				route,
				label: route.kind === 'handover' ? deviceText.receiptPrint : format(deviceText.stationPrint, { station: route.station_name }),
				pending: route.kind === 'deliver' && (route.printer === null || route.state === 'unused')
			}))
	);

	function look(route: StationRoute, pending: boolean): { label: string; tone: Tone; icon: string } {
		if (pending) return { label: deviceText.printerPending, tone: 'neutral', icon: 'circle-minus' };
		if (route.printer?.connected) return { label: deviceText.printerConnected, tone: 'success', icon: 'plug-connected' };
		if (route.printer) return { label: deviceText.printerDisconnected, tone: 'danger', icon: 'plug-connected-x' };
		return { label: deviceText.printerMissing, tone: 'warning', icon: 'plug-x' };
	}
</script>

<div class="flex flex-col gap-2">
	<div>
		<h3 class="text-sm font-semibold text-slate-800">{deviceText.printersTitle}</h3>
		<p class="text-xs text-slate-500">{deviceText.printersDescription}</p>
	</div>
	{#if failure}
		<Notice text={failure}>
			<Button label={actionText.retry} icon="refresh" variant="tertiary" onclick={() => void load()} />
		</Notice>
	{:else if routes === null}
		<Notice text={deviceText.printersLoading} loading />
	{:else if rows.length === 0}
		<Notice text={deviceText.printersEmpty} />
	{:else}
		<ul class="divide-y divide-slate-100">
			{#each rows as row (row.route.station_id)}
				{@const state = look(row.route, row.pending)}
				<li class="flex flex-wrap items-center justify-between gap-2 py-2">
					<span class="min-w-0">
						<span class="block text-sm font-semibold text-slate-800">{row.label}</span>
						<span class="block break-words text-xs text-slate-500">{row.route.printer?.name ?? (row.pending ? deviceText.deliverPending : deviceText.noPrinterReported)}</span>
					</span>
					<Badge tone={state.tone}><i class="ti ti-{state.icon}" aria-hidden="true"></i>{state.label}</Badge>
				</li>
			{/each}
		</ul>
	{/if}
</div>
