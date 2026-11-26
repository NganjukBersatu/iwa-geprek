<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import type { StockCountState } from '../stock-count.svelte';
	import { termText } from '$lib/text/terms';
	import { stockItemText } from '$lib/text/stock-items';
	import { format } from '$lib/text/format';

	let { count }: { count: StockCountState } = $props();

	const trail = [{ label: PAGES.stockItems.label, href: PAGES.stockItems.path }, { label: stockItemText.count }];

	async function save(): Promise<void> {
		if (await count.submit()) void goto(PAGES.stockItems.path);
	}

	function differenceOf(typed: string, balance: string): number {
		return Number(typed.replace(',', '.')) - Number(balance);
	}
</script>

<FormPage title={stockItemText.count} description={stockItemText.countDescription} stacked wide {trail} busy={count.busy} onclose={() => void goto(PAGES.stockItems.path)}>
	<FormSection icon="clipboard-check" title={termText.branch} description={stockItemText.countBranchNote}>
		<div class="max-w-sm">
			<BranchField bind:value={count.branch} onchange={() => void count.changeBranch()} />
		</div>
	</FormSection>

	<FormSection icon="package" title={termText.physicalCount} description={stockItemText.countSystemBalanceNote}>
		{#if !count.branch}
			<Notice text={stockItemText.countChooseBranchFirst} />
		{:else if count.loading}
			<Notice loading text={stockItemText.itemsLoading} />
		{:else if count.items.length === 0}
			<Notice text={stockItemText.noManagedItems} />
		{:else}
			<ul class="flex flex-col divide-y divide-slate-100">
				{#each count.items as item (item.id)}
					{@const typed = count.counted[item.menu_item_id]?.trim()}
					<li class="flex items-center justify-between gap-3 py-2">
						<span class="min-w-0">
							<span class="block text-sm text-slate-800 wrap-break-word">{item.menu_item_name}</span>
							<span class="block text-xs text-slate-500">{format(stockItemText.systemBalance, { amount: formatNumber(item.balance), unit: item.unit ?? '' })}</span>
						</span>
						<div class="w-28 shrink-0">
							<TextField
								compact
								label={format(controlText.countedOf, { name: item.menu_item_name })}
								inputmode="decimal"
								placeholder={EMPTY_VALUE}
								bind:value={() => count.counted[item.menu_item_id] ?? '', (value) => (count.counted[item.menu_item_id] = value)}
							/>
						</div>
						{#if typed}
							{@const difference = differenceOf(typed, item.balance)}
							<span class="w-16 shrink-0 text-right text-xs font-semibold {Number.isNaN(difference) || difference === 0 ? 'text-slate-500' : difference < 0 ? 'text-danger-700' : 'text-info-700'}">
								{Number.isNaN(difference) ? EMPTY_VALUE : difference === 0 ? stockItemText.matches : `${difference > 0 ? '+' : ''}${formatNumber(difference)}`}
							</span>
						{:else}
							<span class="w-16 shrink-0"></span>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}
	</FormSection>

	<FormSection icon="notes" title={termText.note}>
		<div class="max-w-xl">
			<TextField label={termText.note} bind:value={count.note} maxlength={255} placeholder={stockItemText.count} />
		</div>
	</FormSection>

	{#if count.problem || count.error}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{count.problem || count.error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton label={stockItemText.saveCount} busy={count.busy} disabled={count.filled === 0} onclick={() => void save()} />
		<CancelButton disabled={count.busy} onclick={() => void goto(PAGES.stockItems.path)} />
	{/snippet}
</FormPage>
