<script lang="ts">
	import type { Branch, BranchCreate, BranchUpdate } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import LocationMap from '$lib/components/map/LocationMap.svelte';
	import { parseNumber } from '$lib/format/number';
	import Banner from '$lib/components/card/Banner.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { PAGES, branchPath } from '$lib/nav/pages';
	import { onMount, untrack } from 'svelte';
	import { api } from '$lib/api';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { branchText } from '$lib/text/branches';
	import { format } from '$lib/text/format';

	let {
		branch,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		branch: Branch | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: BranchCreate | BranchUpdate) => void;
		onclose: () => void;
	} = $props();

	const DEFAULT_RADIUS = 50;
	const current = untrack(() => branch);
	const trail = [
		{ label: PAGES.branches.label, href: PAGES.branches.path },
		...(current ? [{ label: current.name, href: branchPath(current.id) }, { label: actionText.edit }] : [{ label: branchText.addBranch }])
	];

	let name = $state(current?.name ?? '');
	let code = $state(current?.code ?? '');
	let receiptNumber = $state(current?.receipt_number ?? '');
	let latitude = $state(current?.latitude != null ? String(current.latitude) : '');
	let longitude = $state(current?.longitude != null ? String(current.longitude) : '');
	let radius = $state(String(current?.attendance_radius_meters ?? DEFAULT_RADIUS));
	let cashFloat = $state(current?.cash_float != null ? String(Number(current.cash_float)) : '');
	let spendingFloat = $state(current?.spending_float != null ? String(Number(current.spending_float)) : '');
	// Periode berjalan hanya dikirim bila diubah, karena mengirimnya menyusun ulang pola semua periode.
	let periodStart = $state('');
	let periodEnd = $state('');
	let periodLoaded = $state<{ start: string; end: string } | null>(null);
	let periodState = $state<'loading' | 'ready' | 'failed'>(untrack(() => (current ? 'loading' : 'ready')));

	onMount(() => {
		if (current) void loadPeriod(current.id);
	});

	async function loadPeriod(id: string): Promise<void> {
		try {
			const periods = await api.outlets.periods(id);
			const running = periods.find((period) => period.running) ?? periods[0];
			if (running) {
				periodStart = running.start;
				periodEnd = running.end;
				periodLoaded = { start: running.start, end: running.end };
			}
			periodState = 'ready';
		} catch {
			periodState = 'failed';
		}
	}

	/** Why the position could not be read from this device; it concerns the button, not a box. */
	let locationProblem = $state('');
	let locating = $state(false);
	const errors = new FieldErrors(
		{
			name: branchText.branchName,
			code: termText.code,
			receipt_number: branchText.branchNumber,
			latitude: branchText.latitude,
			longitude: branchText.longitude,
			attendance_radius_meters: branchText.attendanceRadius,
			cash_float: branchText.drawerFloat,
			spending_float: termText.spendingFloat,
			period_start: branchText.periodStart,
			period_end: branchText.periodEnd
		},
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const point = $derived.by(() => {
		const lat = parseNumber(latitude);
		const lng = parseNumber(longitude);
		return lat !== null && lng !== null && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? { lat, lng } : null;
	});
	const radiusMeters = $derived(parseNumber(radius) ?? DEFAULT_RADIUS);

	function locationFailureText(code: number): string {
		switch (code) {
			case GeolocationPositionError.PERMISSION_DENIED:
				return branchText.locationDenied;
			case GeolocationPositionError.POSITION_UNAVAILABLE:
				return branchText.locationUnavailable;
			case GeolocationPositionError.TIMEOUT:
				return branchText.locationTimeout;
			default:
				return branchText.locationFailed;
		}
	}

	function useMyLocation(): void {
		if (!navigator.geolocation) return void (locationProblem = branchText.locationUnsupported);
		locationProblem = '';
		locating = true;
		navigator.geolocation.getCurrentPosition(
			(position) => {
				latitude = position.coords.latitude.toFixed(6);
				longitude = position.coords.longitude.toFixed(6);
				locating = false;
			},
			(failure) => {
				locationProblem = locationFailureText(failure.code);
				locating = false;
			},
			{ enableHighAccuracy: true, timeout: 15000 }
		);
	}

	const money = (text: string) => (text.trim() ? parseNumber(text) : null);

	function submit(): void {
		const found: Record<string, string> = {};
		if (!name.trim()) found.name = branchText.nameRequired;
		const lat = latitude.trim() ? parseNumber(latitude) : null;
		const lng = longitude.trim() ? parseNumber(longitude) : null;
		if (latitude.trim() && (lat === null || Math.abs(lat) > 90)) found.latitude = 'Lintang harus angka antara −90 dan 90, misalnya -7.600000.';
		if (longitude.trim() && (lng === null || Math.abs(lng) > 180)) found.longitude = 'Bujur harus angka antara −180 dan 180, misalnya 111.900000.';
		if (latitude.trim() && !longitude.trim()) found.longitude = branchText.longitudeRequired;
		if (longitude.trim() && !latitude.trim()) found.latitude = branchText.latitudeRequired;
		const meters = parseNumber(radius);
		if (meters === null || !Number.isInteger(meters) || meters < 1 || meters > 5000) found.attendance_radius_meters = branchText.radiusInvalid;
		const cash = money(cashFloat);
		const spending = money(spendingFloat);
		if (cashFloat.trim() && (cash === null || cash < 0)) found.cash_float = branchText.drawerFloatInvalid;
		if (spendingFloat.trim() && (spending === null || spending < 0)) found.spending_float = branchText.spendingFloatInvalid;
		const periodChanged = periodLoaded !== null && (periodStart !== periodLoaded.start || periodEnd !== periodLoaded.end);
		if (periodChanged && (!periodStart || !periodEnd)) found.period_start = branchText.periodRequired;
		else if (periodChanged && periodEnd < periodStart) found.period_end = branchText.periodEndBeforeStart;
		if (!errors.check(found)) return;
		const radiusValue = meters as number;
		onsave({
			...(periodChanged ? { period_start: periodStart, period_end: periodEnd } : {}),
			name: name.trim(),
			code: code.trim() || null,
			receipt_number: receiptNumber.trim() || null,
			latitude: lat,
			longitude: lng,
			attendance_radius_meters: radiusValue,
			cash_float: cash,
			spending_float: spending
		});
	}
</script>

<FormPage title={current ? format(branchText.editBranchTitle, { name: current.name }) : branchText.addBranch} description={branchText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="building-store" title={branchText.identity} description={branchText.identityDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<TextField label={branchText.branchName} bind:value={name} maxlength={120} required error={errors.get('name')} />
			<TextField label={termText.code} bind:value={code} maxlength={16} placeholder={branchText.codeExample} hint={branchText.codeHint} error={errors.get('code')} />
			<TextField label={branchText.branchNumber} bind:value={receiptNumber} maxlength={8} placeholder="05" hint={branchText.receiptNumberHint} error={errors.get('receipt_number')} />
		</div>
	</FormSection>
	<FormSection icon="map-pin" title={branchText.attendanceLocation} description={branchText.attendanceLocationDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<TextField label={branchText.latitude} inputmode="decimal" bind:value={latitude} placeholder="-7.600000" error={errors.get('latitude')} />
			<TextField label={branchText.longitude} inputmode="decimal" bind:value={longitude} placeholder="111.900000" error={errors.get('longitude')} />
			<TextField label={branchText.attendanceRadiusMeters} inputmode="numeric" bind:value={radius} hint={branchText.radiusHint} error={errors.get('attendance_radius_meters')} />
		</div>
		<Button label={locating ? branchText.locating : branchText.useMyLocation} icon="current-location" disabled={locating} onclick={useMyLocation} class="w-fit" />
		{#if locationProblem}<Banner tone="warning" icon="map-pin-off">{locationProblem}</Banner>{/if}
		{#if point}
			{#key `${point.lat},${point.lng},${radiusMeters}`}
				<LocationMap latitude={point.lat} longitude={point.lng} branchLatitude={point.lat} branchLongitude={point.lng} radius={radiusMeters} />
			{/key}
		{/if}
	</FormSection>
	<FormSection icon="cash" title={branchText.fixedMoney} description={branchText.fixedMoneyDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<MoneyField label={branchText.drawerFloatRupiah} bind:value={cashFloat} hint={branchText.drawerFloatHint} error={errors.get('cash_float')} />
			<MoneyField label={branchText.spendingFloatRupiah} bind:value={spendingFloat} hint={branchText.spendingFloatHint} error={errors.get('spending_float')} />
		</div>
	</FormSection>
	{#if current}
		<FormSection icon="calendar" title={branchText.runningPeriod} description={branchText.runningPeriodDescription}>
			{#if periodState === 'failed'}
				<Banner tone="warning" icon="alert-triangle">{branchText.periodLoadFailed}</Banner>
			{:else}
				<div class="grid gap-2 tablet:grid-cols-2">
					<TextField label={branchText.periodStart} type="date" bind:value={periodStart} disabled={periodState === 'loading'} error={errors.get('period_start')} />
					<TextField label={branchText.periodEnd} type="date" bind:value={periodEnd} disabled={periodState === 'loading'} error={errors.get('period_end')} />
				</div>
				<p class="text-xs text-slate-500">{branchText.periodPatternNote}</p>
			{/if}
		</FormSection>
	{/if}
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
