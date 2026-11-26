<script lang="ts">
	import type { DeviceCode } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import QrCodeImage from '$lib/components/media/QrCodeImage.svelte';
	import { actionText } from '$lib/text/actions';
	import { deviceText } from '$lib/text/devices';
	import { format } from '$lib/text/format';
	import { pairingQr } from '../sections';

	let { issued, onclose }: { issued: DeviceCode; onclose: () => void } = $props();

	let copied = $state(false);
	let copyFailed = $state(false);

	async function copy(): Promise<void> {
		try {
			await navigator.clipboard.writeText(issued.code);
			copied = true;
			copyFailed = false;
		} catch {
			copied = false;
			copyFailed = true;
		}
	}
</script>

<Modal open title={format(deviceText.pairTitle, { name: issued.name })} size="sm" {onclose}>
	<div class="flex flex-col items-center gap-4 tablet:flex-row tablet:items-start">
		<QrCodeImage value={pairingQr(issued.code)} label={format(deviceText.pairQrLabel, { name: issued.name })} />
		<div class="flex min-w-0 flex-col gap-2">
			<p class="text-sm leading-6 text-slate-600">{deviceText.pairSteps}</p>
			<p class="text-xs text-slate-500">{deviceText.pairTypeCode}</p>
			<p class="select-all font-mono text-2xl font-bold tracking-widest text-slate-800">{issued.code}</p>
			{#if copyFailed}
				<p class="text-xs text-danger-700" role="alert">{deviceText.copyFailed}</p>
			{/if}
			<p class="text-xs text-slate-500">{deviceText.codeKeptNote}</p>
		</div>
	</div>
	{#snippet footer()}
		<Button label={copied ? deviceText.copied : deviceText.copyCode} icon="copy" onclick={() => void copy()} />
		<Button label={actionText.close} variant="primary" onclick={onclose} />
	{/snippet}
</Modal>
