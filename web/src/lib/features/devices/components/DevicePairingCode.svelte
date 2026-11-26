<script lang="ts">
	import IconButton from '$lib/components/button/IconButton.svelte';
	import QrCodeImage from '$lib/components/media/QrCodeImage.svelte';
	import { deviceText } from '$lib/text/devices';
	import { format } from '$lib/text/format';
	import { pairingQr } from '../sections';

	/** Kode pasang perangkat: tersembunyi sampai dilihat; mata membuka kode dan QR-nya sekaligus, dan salin aktif setelah itu. */
	let { code, deviceName }: { code: string | null; deviceName: string } = $props();

	const HIDDEN = '********';

	let shown = $state(false);
	let copied = $state(false);
	let copyFailed = $state(false);

	// Kode baru atau perangkat lain mulai lagi dari keadaan tersembunyi.
	$effect(() => {
		void code;
		shown = false;
		copied = false;
		copyFailed = false;
	});

	async function copy(): Promise<void> {
		if (!code) return;
		try {
			await navigator.clipboard.writeText(code);
			copied = true;
			copyFailed = false;
		} catch {
			// Peramban bisa menolak akses papan klip; pengguna diberi jalan menyalin manual, bukan dibiarkan tanpa kabar.
			copied = false;
			copyFailed = true;
		}
	}
</script>

<div class="flex min-w-0 flex-col gap-1">
	<span class="text-xs font-semibold text-slate-600">{deviceText.pairingCode}</span>
	{#if code}
		<div class="flex items-center gap-1">
			<span class="font-mono text-sm font-bold tracking-widest text-slate-800 {shown ? 'select-all' : 'select-none'}">{shown ? code : HIDDEN}</span>
			<IconButton icon={shown ? 'eye-off' : 'eye'} label={shown ? deviceText.hideCode : deviceText.showCode} size="sm" onclick={() => (shown = !shown)} />
			<IconButton icon={copied ? 'check' : 'copy'} label={shown ? deviceText.copyCode : deviceText.copyHiddenHint} size="sm" disabled={!shown} onclick={() => void copy()} />
		</div>
		{#if copyFailed}
			<p class="text-xs text-danger-700" role="alert">{deviceText.copyFailed}</p>
		{/if}
		{#if shown}
			<div class="mt-1 flex flex-col gap-2">
				<QrCodeImage value={pairingQr(code)} label={format(deviceText.pairQrLabel, { name: deviceName })} />
				<p class="text-xs text-slate-500">{deviceText.pairSteps}</p>
			</div>
		{/if}
		<p class="text-xs text-slate-500">{deviceText.pairingCodeNote}</p>
	{:else}
		<p class="text-sm text-slate-600">{deviceText.noPairingCode}</p>
	{/if}
</div>
