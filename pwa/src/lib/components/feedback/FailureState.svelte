<script lang="ts">
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import { failureText, type AppFailure } from '$lib/failure/failure';
	import { t } from '$lib/text/t';
	import Notice from './Notice.svelte';

	/** Keadaan gagal memuat: teks dari sebab sebenarnya dan tombol coba lagi bila [onRetry] diberi, kecuali sesi berakhir. */
	let { failure, onRetry }: { failure: AppFailure; onRetry?: () => void } = $props();
</script>

<div class="flex w-full flex-col gap-3">
	<Notice text={failureText(failure)} />
	{#if onRetry && failure.kind !== 'unauthorized'}
		<PrimaryButton text={t('common_retry')} onclick={onRetry} />
	{/if}
</div>
