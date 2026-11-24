<script lang="ts">
	import SecondaryButton from '$lib/components/button/SecondaryButton.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import LoadingState from '$lib/components/feedback/LoadingState.svelte';
	import SuccessState from '$lib/components/feedback/SuccessState.svelte';
	import QrScanner from '$lib/components/media/QrScanner.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import { failureText } from '$lib/failure/failure';
	import { t } from '$lib/text/t';
	import { PairingState } from './pairing.svelte';

	/** Bagian halaman Absen untuk menautkan karyawan ke perangkat operasional lewat pindai QR. */
	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const pairing = new PairingState(() => onSessionExpired());
</script>

{#if pairing.sending}
	<div class="pt-6"><LoadingState rows={2} /></div>
{:else if pairing.linked}
	<SuccessState title={t('pairing_success_title')} message={t('pairing_success_message', pairing.linked.name)} icon="Checklist" class="pt-6" />
{:else}
	<div class="pt-6">
		<ListCard><ListRow title={t('pairing_title')} caption={t('pairing_description')} /></ListCard>
	</div>
{/if}

{#if pairing.failure}
	<div class="pt-3"><InlineMessage text={failureText(pairing.failure)} /></div>
{/if}

{#if !pairing.linked}
	<div class="pt-3"><SecondaryButton text={t('pairing_action')} onclick={() => pairing.startScan()} enabled={!pairing.sending} /></div>
{/if}

{#if pairing.scanning}
	<BottomSheet title={t('pairing_sheet_title')} onDismiss={() => pairing.stopScan()}>
		<QrScanner onScanned={(value) => void pairing.onScanned(value)} />
		<div class="h-3"></div>
		<Notice text={t('pairing_sheet_hint')} />
	</BottomSheet>
{/if}
