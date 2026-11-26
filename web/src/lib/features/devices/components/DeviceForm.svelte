<script lang="ts">
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
import Button from '$lib/components/button/Button.svelte';
	import { api } from '$lib/api';
	import type { Device, DeviceCreate, DeviceUpdate, StationOption } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import RichText from '$lib/components/text/RichText.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { PAGES, devicePath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { userMessage } from '$lib/api/user-message';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { deviceText } from '$lib/text/devices';
	import { format } from '$lib/text/format';

	let {
		device,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		device: Device | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: DeviceCreate | DeviceUpdate, outletId: string) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => device);
	const trail = [
		{ label: PAGES.devices.label, href: PAGES.devices.path },
		...(current ? [{ label: current.name, href: devicePath(current.id) }, { label: actionText.edit }] : [{ label: deviceText.addDevice }])
	];

	const MAX_NAME = 80;

	let name = $state(current?.name ?? '');
	// Nama tablet baru mengikuti stasiun yang dicentang sampai pengguna mengetik namanya sendiri.
	let nameTouched = $state(current !== null);
	let outletId = $state(current?.outlet_id ?? '');
	let stations = $state<StationOption[] | null>(null);
	let stationsError = $state('');
	type Mode = 'cashier' | 'station';
	type DeviceLayout = Device['layout'];
	const MODES: { value: Mode; label: string }[] = [
		{ value: 'cashier', label: deviceText.modeCashier },
		{ value: 'station', label: deviceText.modeStation }
	];
	// Perangkat baru bawaannya Mode Kasir: perangkat pertama sebuah usaha hampir selalu kasir, dan panduan siap jualan memintanya.
	let mode = $state<string>(current?.mode ?? 'cashier');
	const chosenMode = $derived<Mode>(mode === 'cashier' ? 'cashier' : 'station');
	const LAYOUTS: { value: DeviceLayout; label: string }[] = (['auto', 'phone', 'tablet'] as const).map((value) => ({ value, label: deviceText.layouts[value] }));
	let layout = $state<string>(current?.layout ?? 'auto');
	const chosenLayout = $derived<DeviceLayout>(layout === 'phone' || layout === 'tablet' ? layout : 'auto');
	// Yang dicentang adalah gabungan stasiun yang dipegang dan yang dicetak; server menurunkan keduanya dari mode.
	const picked = new SvelteSet<string>([...(current?.station_ids ?? []), ...(current?.print_station_ids ?? [])]);

	// Tablet lain yang memegang stasiun ini; server tetap penentu.
	const holders = (station: StationOption): string[] => station.device_names.filter((holder) => holder !== current?.name);
	// Stasiun selain Kasir hanya milik satu tablet per cabang, dipegang maupun dicetak; server tetap penentu.
	const taken = (station: StationOption): boolean =>
		station.kind !== 'handover' && [...station.holder_device_ids, ...station.printer_device_ids].some((id) => id !== current?.id);
	// Mode Kasir selalu memegang stasiun Kasir di server, jadi yang dipilih di sini hanya struk stasiun lain yang ikut dicetak.
	const cashierStation = $derived((stations ?? []).find((station) => station.kind === 'handover') ?? null);
	const shown = $derived(chosenMode === 'cashier' ? (stations ?? []).filter((station) => station.kind !== 'handover') : (stations ?? []));
	const errors = new FieldErrors({ outlet_id: termText.branch, name: deviceText.deviceName, station_ids: deviceText.stationsOnTablet }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	// Pilihan stasiun semua stasiun cabang tablet, termasuk yang belum aktif; cabang berganti berarti pilihan dimuat ulang.
	whenChanged(
		() => outletId,
		() => void loadStations()
	);

	async function loadStations(): Promise<void> {
		stations = null;
		stationsError = '';
		if (!outletId) return;
		try {
			stations = await api.devices.stations(outletId);
		} catch (failure) {
			stationsError = userMessage(failure, deviceText.stationsLoadFailed);
		}
	}

	function autoName(): void {
		if (nameTouched || !stations) return;
		const chosen = shown.filter((station) => picked.has(station.id)).map((station) => station.name);
		if (chosenMode === 'cashier' && cashierStation) chosen.unshift(cashierStation.name);
		name = chosen.length > 0 ? format(deviceText.autoName, { stations: chosen.join(' + ') }).slice(0, MAX_NAME) : '';
	}

	// Berganti mode atau selesai memuat stasiun mengubah usulan nama selama nama belum diketik sendiri.
	whenChanged(
		() => [chosenMode, stations] as const,
		() => autoName()
	);

	function toggle(id: string): void {
		if (picked.has(id)) picked.delete(id);
		else picked.add(id);
		autoName();
	}

	function submit(): void {
		const found: Record<string, string> = {};
		if (!current && !outletId) found.outlet_id = deviceText.branchRequired;
		if (!name.trim()) found.name = deviceText.nameRequired;
		const active = new Set(shown.map((station) => station.id));
		const chosen = [...picked].filter((id) => active.has(id));
		if (chosenMode === 'station' && stations !== null && chosen.length === 0) found.station_ids = deviceText.stationRequired;
		if (!errors.check(found)) return;
		const body = { name: name.trim(), mode: chosenMode, layout: chosenLayout, station_ids: chosen };
		// Mengganti mode perangkat yang sudah ada mengubah cara kerjanya, jadi akibatnya dikonfirmasi dulu.
		if (current && current.mode !== chosenMode) {
			pendingSave = body;
			return;
		}
		onsave(body, outletId);
	}

	let pendingSave = $state<DeviceUpdate | null>(null);

	function confirmMode(): void {
		if (pendingSave) onsave(pendingSave, outletId);
		pendingSave = null;
	}
</script>

<FormPage
	title={current ? format(deviceText.editDeviceTitle, { name: current.name }) : deviceText.addDevice}
	description={current ? deviceText.formTitleDescription : deviceText.formDescription}
	stacked
	{trail}
	{busy}
	{onclose}
>
	<FormSection icon="device-tablet" title={deviceText.device} description={deviceText.nameSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			{#if !current}
				<BranchField bind:value={outletId} error={errors.get('outlet_id')} />
			{/if}
			<TextField
				label={deviceText.deviceName}
				bind:value={name}
				maxlength={MAX_NAME}
				placeholder={deviceText.nameExample}
				hint={current ? undefined : deviceText.nameAutoHint}
				required
				error={errors.get('name')}
				oninput={() => (nameTouched = true)}
			/>
		</div>
		<div class="mt-4">
			<SelectField label={deviceText.mode} bind:value={mode} options={MODES} hint={deviceText.modeHints[chosenMode]} />
		</div>
		<div class="mt-4">
			<SelectField label={deviceText.layout} bind:value={layout} options={LAYOUTS} hint={deviceText.layoutHint} />
		</div>
		<div class="mt-4 flex flex-col gap-1">
			<span class="text-xs font-semibold text-slate-600">{deviceText.stationsTitles[chosenMode]}</span>
			<span class="text-xs text-slate-500">{deviceText.stationsHints[chosenMode]}</span>
			{#if !outletId}
				<Notice text={deviceText.chooseBranchFirst} />
			{:else if stationsError}
				<Notice text={stationsError} />
			{:else if stations === null}
				<Notice text={deviceText.stationsLoading} loading />
			{:else if shown.length === 0}
				<Notice text={chosenMode === 'cashier' ? deviceText.noOtherStationsToPrint : deviceText.noStationsToPick}>
					<Button label={deviceText.openStationSetup} icon="settings" href={PAGES.stationSetup.path} />
				</Notice>
			{:else}
				<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('station_ids') ? true : undefined}>
					{#each shown as station (station.id)}
						{@const shared = holders(station)}
						{@const locked = taken(station)}
						<CheckRow
							label={station.name}
							hint={locked
								? shared.length > 0
									? format(deviceText.takenByNamed, { names: shared.join(', ') })
									: deviceText.takenByOther
								: shared.length > 0
									? format(deviceText.alsoHeldBy, { names: shared.join(', ') })
									: undefined}
							checked={picked.has(station.id)}
							disabled={locked && !picked.has(station.id)}
							onchange={() => toggle(station.id)}
						/>
					{/each}
				</div>
				{#if errors.get('station_ids')}<p class="text-xs text-danger-700" role="alert">{errors.get('station_ids')}</p>{/if}
			{/if}
		</div>
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton label={current ? actionText.save : deviceText.saveAndIssue} busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>

<ConfirmDialog
	open={pendingSave !== null}
	title={deviceText.modeChangeTitles[chosenMode]}
	confirmLabel={deviceText.modeChangeConfirm[chosenMode]}
	onconfirm={confirmMode}
	oncancel={() => (pendingSave = null)}
>
	<RichText template={deviceText.modeChangeEffects[chosenMode]} values={{ name: current?.name ?? '' }} />
</ConfirmDialog>
