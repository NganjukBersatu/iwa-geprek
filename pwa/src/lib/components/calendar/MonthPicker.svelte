<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { t } from '$lib/text/t';

	let { label, onPrevious, onNext, nextEnabled }: { label: string; onPrevious: () => void; onNext: () => void; nextEnabled: boolean } = $props();
</script>

<div class="flex w-full items-center rounded-field border border-divider bg-surface">
	<button type="button" onclick={onPrevious} aria-label={t('month_picker_previous')} class="flex size-[var(--space-touch)] shrink-0 items-center justify-center">
		<AppIcon icon="ChevronLeft" tint="primary" />
	</button>
	<p class="text-button m-0 flex-1 text-center text-content">{label}</p>
	<button
		type="button"
		disabled={!nextEnabled}
		onclick={onNext}
		aria-label={t('month_picker_next')}
		class="flex size-[var(--space-touch)] shrink-0 items-center justify-center {nextEnabled ? '' : 'disabled-look'}"
	>
		<AppIcon icon="ChevronRight" tint="primary" />
	</button>
</div>
