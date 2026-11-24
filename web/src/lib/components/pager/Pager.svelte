<script lang="ts">
	import { page as route } from '$app/state';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import { rememberPage, savedPage } from './page-memory';
	import { PAGE_SIZE_OPTIONS, pageSize } from './size.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		page,
		total,
		unit = 'data',
		list,
		disabled = false,
		onchange
	}: {
		page: number;
		total: number;
		unit?: string;
		/** Names the list for remembering its page when one screen has several lists of the same unit. */
		list?: string;
		disabled?: boolean;
		onchange: (page: number) => void;
	} = $props();

	const size = $derived(pageSize.value);
	const pages = $derived(Math.max(1, Math.ceil(total / size)));
	const from = $derived(total === 0 ? 0 : (page - 1) * size + 1);
	const to = $derived(Math.min(page * size, total));
	// With one page there is nothing to turn; the size choice stays while the list is longer than the smallest size.
	const paged = $derived(pages > 1);
	const sizable = $derived(total > Math.min(...PAGE_SIZE_OPTIONS));
	const sizeOptions = PAGE_SIZE_OPTIONS.map((option) => ({ value: String(option), label: format(controlText.rowsOption, { count: option }) }));

	const jumpId = $props.id();
	let jump = $state('');

	// Coming back to a screen, the list returns to the page it was left on once its first data has arrived.
	let settled = $state(false);

	$effect(() => {
		if (settled || total <= 0) return;
		settled = true;
		const saved = savedPage(route.url.pathname, list ?? unit);
		const target = saved === null ? page : Math.min(saved, pages);
		if (target !== page) onchange(target);
	});

	$effect(() => {
		if (settled) rememberPage(route.url.pathname, list ?? unit, page);
	});

	// A new size changes what every page holds, so the list starts again from the first page.
	function resize(value: string): void {
		pageSize.set(Number(value));
		onchange(1);
	}

	function go(): void {
		const target = Number(jump);
		jump = '';
		if (!Number.isInteger(target) || target < 1) return;
		const next = Math.min(target, pages);
		if (next !== page) onchange(next);
	}

	const navClass =
		'flex size-8 min-h-0 min-w-0 items-center justify-center rounded-lg border border-brand-line bg-white text-sm text-brand-ink hover:border-brand hover:bg-brand-soft disabled:opacity-40 disabled:hover:border-brand-line disabled:hover:bg-white';
</script>

<div class="flex flex-wrap items-center justify-between gap-3 pt-3">
	<p class="text-xs text-slate-500">{format(controlText.pagerRange, { from: from, to: to, total: total, unit: unit })}</p>
	<div class="flex flex-wrap items-center gap-2">
		{#if sizable}
			<SelectField label={controlText.rowsPerPage} compact {disabled} value={String(size)} options={sizeOptions} onchange={(value) => resize(value)} />
		{/if}
		{#if paged}
			<button type="button" class={navClass} disabled={disabled || page <= 1} onclick={() => onchange(page - 1)} aria-label={controlText.previousPage}>
				<i class="ti ti-chevron-left" aria-hidden="true"></i>
			</button>
			<span class="text-xs text-brand-muted">{format(controlText.pagerPage, { page: page, pages: pages })}</span>
			<button type="button" class={navClass} disabled={disabled || page >= pages} onclick={() => onchange(page + 1)} aria-label={controlText.nextPage}>
				<i class="ti ti-chevron-right" aria-hidden="true"></i>
			</button>
			<label class="sr-only" for={jumpId}>{controlText.jumpToPage}</label>
			<input
				id={jumpId}
				type="text"
				inputmode="numeric"
				placeholder={controlText.goToPage}
				{disabled}
				bind:value={jump}
				onkeydown={(event) => event.key === 'Enter' && go()}
				onblur={go}
				class="h-8 w-20 rounded-lg border border-brand-line bg-white px-2 text-center text-xs text-brand-ink placeholder:text-brand-muted focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand-line disabled:bg-slate-50"
			/>
		{/if}
	</div>
</div>
