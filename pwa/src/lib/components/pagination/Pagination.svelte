<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { viewport } from '$lib/platform/viewport.svelte';
	import { t } from '$lib/text/t';

	const MIN_SLOTS_FOR_NUMBERS = 6;
	const COMPACT_TARGET = 36;
	const JUMP_WIDTH = 48 * 1.75;
	const STEP_WIDTH = COMPACT_TARGET;
	const SLOT_WIDTH = COMPACT_TARGET + 4;
	const MD = 12;

	/** Pengatur halaman satu baris: kolom lompat di kiri dan nomor di kanan yang menyesuaikan lebar (jatuh ke "n / total" bila sempit), dengan [page] berbasis nol. */
	let { page, pageCount, onPageChange }: { page: number; pageCount: number; onPageChange: (page: number) => void } = $props();

	let width = $state(390);
	let jump = $state('');

	const slots = $derived(Math.floor((width - 16 - JUMP_WIDTH - STEP_WIDTH * 2 - MD) / SLOT_WIDTH));
	const numbered = $derived(slots >= MIN_SLOTS_FOR_NUMBERS || pageCount <= slots);

	/** Indeks halaman yang tampil, dengan null menandai celah dan selalu memuat pertama, terakhir, dan sekitar [current]. */
	function pageItems(current: number, count: number): (number | null)[] {
		if (count <= 6) return Array.from({ length: count }, (_, index) => index);
		const shown = new Set([0, count - 1, current - 1, current, current + 1]);
		if (current <= 1) shown.add(2);
		if (current >= count - 2) shown.add(count - 3);
		const result: (number | null)[] = [];
		let previous = -1;
		for (const index of [...shown].filter((item) => item >= 0 && item < count).sort((a, b) => a - b)) {
			if (previous !== -1 && index - previous > 1) result.push(null);
			result.push(index);
			previous = index;
		}
		return result;
	}

	function doJump(): void {
		const value = Number.parseInt(jump, 10);
		if (!Number.isNaN(value)) onPageChange(Math.min(pageCount, Math.max(1, value)) - 1);
		jump = '';
	}
</script>

{#snippet step(leading: boolean, enabled: boolean)}
	<button
		type="button"
		disabled={!enabled}
		onclick={() => onPageChange(leading ? page - 1 : page + 1)}
		aria-label={leading ? t('pagination_previous_description') : t('pagination_next_description')}
		class="flex min-h-[var(--space-compact)] items-center justify-center rounded-field px-1 {enabled ? '' : 'disabled-look'}"
	>
		{#if !leading && viewport.isWide}<span class="text-label text-primary">{t('pagination_next')}</span>{/if}
		<AppIcon icon={leading ? 'ChevronLeft' : 'ChevronRight'} tint="primary" size={COMPACT_TARGET / 2} />
		{#if leading && viewport.isWide}<span class="text-label text-primary">{t('pagination_back')}</span>{/if}
	</button>
{/snippet}

<div class="flex w-full items-center justify-between p-2" bind:clientWidth={width}>
	<input
		type="text"
		inputmode="numeric"
		enterkeyhint="go"
		bind:value={jump}
		oninput={() => (jump = jump.replace(/\D/g, '').slice(0, 4))}
		onkeydown={(event) => event.key === 'Enter' && doJump()}
		placeholder={t('pagination_jump')}
		class="text-body min-h-[var(--space-compact)] rounded-field border border-outline bg-surface px-2 text-center text-content outline-none placeholder:text-caption placeholder:text-content-muted"
		use:dynamicStyle={{ width: `${JUMP_WIDTH}px` }}
	/>
	<div class="flex items-center">
		{@render step(true, page > 0)}
		{#if numbered}
			{#each pageItems(page, pageCount) as item, index (index)}
				{#if item === null}
					<span class="text-body px-1 text-content-muted">…</span>
				{:else}
					<button
						type="button"
						onclick={() => onPageChange(item)}
						class="text-label mx-[2px] flex size-[var(--space-compact)] items-center justify-center rounded-field {item === page ? 'bg-primary text-on-primary' : 'bg-selected text-content'}"
					>
						{item + 1}
					</button>
				{/if}
			{/each}
		{:else}
			<span class="text-label px-2 text-content">{page + 1} / {pageCount}</span>
		{/if}
		{@render step(false, page < pageCount - 1)}
	</div>
</div>
