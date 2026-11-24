<script lang="ts">
	import { updated } from '$app/state';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import { updateRequired } from '$lib/platform/update-required.svelte';
	import { t } from '$lib/text/t';

	/** Versi baru biasa bisa ditunda; versi di bawah minimum dikunci sampai versi terbaru termuat, dengan satu tombol muat ulang. */
	let postponed = $state(false);
	let applying = $state(false);

	const required = $derived(updateRequired.required);
	const visible = $derived(required || (updated.current && !postponed));
	const message = $derived(applying ? t('web_update_applying_message') : required ? t('web_update_required_message') : t('web_update_message'));

	// Cache dan service worker lama dibuang dulu supaya muat ulang pasti mengambil versi terbaru, termasuk di iPhone.
	async function apply(): Promise<void> {
		applying = true;
		try {
			const registrations = 'serviceWorker' in navigator ? await navigator.serviceWorker.getRegistrations() : [];
			await Promise.all(registrations.map((registration) => registration.update().catch(() => undefined)));
			if ('caches' in window) await Promise.all((await caches.keys()).map((key) => caches.delete(key)));
		} finally {
			location.reload();
		}
	}
</script>

{#if visible}
	<BottomSheet title={required ? t('web_update_required_title') : t('web_update_title')} onDismiss={() => (postponed = true)} dismissible={!required && !applying}>
		<div class="flex w-full flex-col gap-3">
			<p class="text-body m-0 text-content">{message}</p>
			{#if required && updateRequired.minimum}
				<div class="grid grid-cols-2 gap-2">
					<div class="flex flex-col justify-between gap-1 rounded-field bg-surface p-3">
						<span class="text-caption whitespace-nowrap text-content-muted">{t('web_update_installed')}</span>
						<span class="text-title text-danger">{__APP_VERSION__}</span>
					</div>
					<div class="flex flex-col justify-between gap-1 rounded-field bg-surface p-3">
						<span class="text-caption whitespace-nowrap text-content-muted">{t('web_update_minimum')}</span>
						<span class="text-title text-content">{updateRequired.minimum}</span>
					</div>
				</div>
			{/if}
			<PrimaryButton text={applying ? t('web_update_applying') : t('web_update_action')} onclick={() => void apply()} enabled={!applying} />
			{#if required}
				<p class="text-caption m-0 text-content-muted">{t('web_update_required_hint')}</p>
			{/if}
		</div>
	</BottomSheet>
{/if}
