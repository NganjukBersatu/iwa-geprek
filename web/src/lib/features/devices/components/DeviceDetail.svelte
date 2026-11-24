<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Device, DeviceCode, DeviceUpdate } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { REGISTERED } from '../sections';
	import DeviceCodeDialog from './DeviceCodeDialog.svelte';
	import DeviceForm from './DeviceForm.svelte';
	import { deviceText } from '$lib/text/devices';
	import { termText } from '$lib/text/terms';
	import RichText from '$lib/components/text/RichText.svelte';

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Device, DeviceUpdate, null>(untrack(() => id), {
		load: (deviceId) => api.devices.detail(deviceId),
		update: (device, body) => api.devices.update(device.id, body),
		remove: (device) => api.devices.revoke(device.id),
		name: (device) => device.name,
		text: { ...recordText('perangkat', PAGES.devices.label), remove: deviceText.revoke, removeTitle: deviceText.revokeTitle }
	});

	let renewing = $state(false);
	let issued = $state<DeviceCode | null>(null);

	const date = (value: string | null) => (value ? formatDateTime(value) : EMPTY_VALUE);
	const plain = (value: string | null) => value || EMPTY_VALUE;

	async function renew(device: Device): Promise<void> {
		let code: DeviceCode | null = null;
		const done = await detail.run(async () => {
			code = await api.devices.newCode(device.id);
		}, deviceText.newCodeFailed);
		if (!done) return;
		renewing = false;
		issued = code;
		await detail.refresh();
	}
</script>

<RecordDetailView
	{detail}
	back={PAGES.devices}
	trail={(device) => [{ label: PAGES.devices.label, href: PAGES.devices.path }, { label: device.name }]}
	tables={['devices', 'device_links', 'device_stations', 'stations']}
	title={(device) => device.name}
	description={(device) => `${device.station_names.join(', ') || deviceText.noStations} · ${device.outlet_name}`}
>
	{#snippet badge(device)}
		<Badge tone={device.status === REGISTERED ? 'success' : 'warning'}>{device.status === REGISTERED ? deviceText.registered : deviceText.waiting}</Badge>
	{/snippet}
	{#snippet extraActions()}
		<Button label={deviceText.newCode} icon="key" variant="tertiary" disabled={detail.busy} onclick={() => (renewing = true)} />
	{/snippet}
	{#snippet body(device)}
		<Card flush class="grid laptop:grid-cols-2">
			<div class="border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<FigureList
					title={deviceText.device}
					figures={[
						{ label: termText.name, value: device.name },
						{ label: termText.branch, value: device.outlet_name },
						{ label: deviceText.mode, value: device.mode === 'cashier' ? deviceText.modeCashier : deviceText.modeStation },
						{ label: deviceText.stationsTitles[device.mode], value: [...device.station_names, ...device.print_station_names].join(', ') || deviceText.noStations },
						{ label: termText.status, value: device.status === REGISTERED ? deviceText.registered : deviceText.waiting },
						{ label: deviceText.created, value: date(device.created_at) },
						{ label: deviceText.paired, value: date(device.paired_at) },
						{ label: deviceText.lastUsed, value: date(device.last_used_at) }
					]}
				/>
			</div>
			<div class="p-4 tablet:p-5">
				<FigureList
					title={deviceText.hardware}
					figures={[
						{ label: deviceText.brand, value: plain(device.brand) },
						{ label: deviceText.model, value: plain(device.model) },
						{ label: deviceText.serial, value: plain(device.serial) },
						{ label: deviceText.androidId, value: plain(device.android_id) }
					]}
				/>
			</div>
		</Card>

		<ConfirmDialog open={renewing} title={deviceText.newCodeTitle} confirmLabel="Terbitkan" busy={detail.busy} error={detail.actionError} onconfirm={() => void renew(device)} oncancel={() => (renewing = false)}>
			<RichText template={deviceText.deviceRenewNote} values={{ name: device.name }} />
		</ConfirmDialog>
	{/snippet}
	{#snippet form(props)}
		<DeviceForm device={props.record} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as DeviceUpdate)} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote(device)}
		<RichText template={deviceText.deviceRemoveNote} values={{ name: device.name }} />
	{/snippet}
</RecordDetailView>

{#if issued}
	<DeviceCodeDialog {issued} onclose={() => (issued = null)} />
{/if}
