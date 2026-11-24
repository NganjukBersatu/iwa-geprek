<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import { t } from '$lib/text/t';

	const NOT_FOUND_STATUS = 404;

	/** Halaman galat yang tidak tertangani halaman mana pun: kalimat untuk pengguna dan jalan kembali, tanpa kode atau pesan teknis. */
	const text = $derived(page.status === NOT_FOUND_STATUS ? t('web_error_not_found') : t('web_error_generic'));
</script>

<div class="flex h-full w-full justify-center overflow-y-auto">
	<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-3" use:dynamicStyle={{ padding: '16px var(--page-padding)' }}>
		<Notice {text} />
		<PrimaryButton text={t('web_error_home')} onclick={() => void goto('/')} />
	</div>
</div>
