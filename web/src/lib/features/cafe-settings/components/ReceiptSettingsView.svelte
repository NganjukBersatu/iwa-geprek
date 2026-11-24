<script lang="ts">
	import type { SocialEntry, WifiEntry } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { actionText } from '$lib/text/actions';
	import { cafeSettingsText as text } from '$lib/text/cafe-settings';
	import type { CafeSettingsState } from '../cafe-settings.svelte';

	let { cafe }: { cafe: CafeSettingsState } = $props();

	const MAX_WIFI = 6;
	const MAX_SOCIAL = 4;
	const DEFAULT_ICON = 'ti-brand-instagram';
	const SOCIAL_ICONS = [
		{ value: DEFAULT_ICON, label: text.instagram },
		{ value: 'ti-brand-tiktok', label: 'TikTok' },
		{ value: 'ti-brand-facebook', label: text.facebook },
		{ value: 'ti-brand-whatsapp', label: 'WhatsApp' },
		{ value: 'ti-brand-youtube', label: 'YouTube' },
		{ value: 'ti-brand-x', label: 'X' }
	];

	let name = $state('');
	let address = $state('');
	let phone = $state('');
	let complaint = $state('');
	let greeting = $state('');
	let wifi = $state<WifiEntry[]>([]);
	let wifiPassword = $state('');
	let social = $state<SocialEntry[]>([]);
	let problem = $state('');

	// Isian mengikuti pengaturan tersimpan: cabang lain atau simpanan baru mengisinya ulang.
	$effect(() => {
		const row = cafe.settings;
		name = row?.name ?? '';
		address = row?.address ?? '';
		phone = row?.phone ?? '';
		complaint = row?.complaint_number ?? '';
		greeting = row?.receipt_greeting ?? '';
		wifi = (row?.wifi ?? []).map((entry) => ({ ...entry }));
		wifiPassword = row?.wifi_password ?? '';
		social = (row?.social ?? []).map((entry) => ({ ...entry }));
	});

	function submit(): void {
		if (!name.trim()) return void (problem = text.nameRequired);
		if (wifi.some((entry) => !entry.area.trim() || !entry.ssid.trim())) return void (problem = text.wifiRequired);
		if (social.some((entry) => !entry.handle.trim())) return void (problem = text.socialRequired);
		problem = '';
		void cafe.save(
			{
				name: name.trim(),
				address: address.trim(),
				phone: phone.trim(),
				complaint_number: complaint.trim(),
				receipt_greeting: greeting.trim(),
				wifi: wifi.map((entry) => ({ area: entry.area.trim(), ssid: entry.ssid.trim() })),
				wifi_password: wifiPassword.trim(),
				social: social.map((entry) => ({ icon: entry.icon, handle: entry.handle.trim() }))
			},
			text.receiptSaved,
			text.receiptSaveFailed
		);
	}
</script>

{#if cafe.notice}
	<Banner tone="success" icon="circle-check">{cafe.notice}</Banner>
{/if}

{#if cafe.settings}
	{#if !cafe.settings.exists}
		<Banner tone="warning" icon="alert-triangle" title={text.noSettingsTitle}>{text.noSettingsHint}</Banner>
	{/if}
	{#if cafe.actionError}
		<Banner tone="danger" icon="alert-triangle">{cafe.actionError}</Banner>
	{/if}

	<Card>
		<CardHeader title={text.receiptIdentity} description={text.receiptIdentityDescription} />
		<div class="mt-4 grid gap-4 tablet:grid-cols-2">
			<TextField label={text.cafeName} bind:value={name} maxlength={120} required />
			<TextField label={text.phone} inputmode="tel" bind:value={phone} maxlength={40} />
			<TextField label={text.complaintNumber} inputmode="tel" bind:value={complaint} maxlength={40} />
			<TextField label={text.receiptGreeting} bind:value={greeting} maxlength={200} />
			<div class="tablet:col-span-2"><TextArea label={text.address} bind:value={address} rows={3} maxlength={300} /></div>
		</div>
	</Card>

	<Card>
		<CardHeader title={text.wifi} description={text.wifiDescription} />
		<div class="mt-4 flex flex-col gap-3">
			{#each wifi as entry, index (index)}
				<div class="grid items-end gap-3 tablet:grid-cols-[1fr_1fr_auto]">
					<TextField label={text.area} bind:value={entry.area} maxlength={60} />
					<TextField label={text.wifiName} bind:value={entry.ssid} maxlength={60} />
					<Button label={actionText.remove} icon="trash" variant="danger" compact onclick={() => (wifi = wifi.filter((_, i) => i !== index))} />
				</div>
			{/each}
			{#if wifi.length < MAX_WIFI}
				<div><Button label={text.addWifi} icon="plus" compact onclick={() => (wifi = [...wifi, { area: '', ssid: '' }])} /></div>
			{/if}
			<div class="tablet:max-w-sm"><TextField label={text.wifiPassword} bind:value={wifiPassword} maxlength={120} /></div>
		</div>
	</Card>

	<Card>
		<CardHeader title={text.socialMedia} description={text.socialMediaDescription} />
		<div class="mt-4 flex flex-col gap-3">
			{#each social as entry, index (index)}
				<div class="grid items-end gap-3 tablet:grid-cols-[1fr_1fr_auto]">
					<SelectField label={text.platform} bind:value={entry.icon} options={SOCIAL_ICONS} />
					<TextField label={text.account} bind:value={entry.handle} maxlength={60} placeholder={text.accountExample} />
					<Button label={actionText.remove} icon="trash" variant="danger" compact onclick={() => (social = social.filter((_, i) => i !== index))} />
				</div>
			{/each}
			{#if social.length < MAX_SOCIAL}
				<div><Button label={text.addAccount} icon="plus" compact onclick={() => (social = [...social, { icon: DEFAULT_ICON, handle: '' }])} /></div>
			{/if}
		</div>
	</Card>

	{#if problem}<Banner tone="danger" icon="alert-triangle">{problem}</Banner>{/if}
	<div><Button label={cafe.busy ? actionText.saving : text.saveReceipt} icon="device-floppy" variant="primary" disabled={cafe.busy} onclick={submit} /></div>
{/if}
