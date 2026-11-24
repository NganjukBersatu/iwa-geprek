<script lang="ts" generics="T">
	import type { Snippet } from 'svelte';
	import { reorder } from '$lib/motion/transitions';
	import { tones, type Tone } from '../card/tone';
	import Skeleton from '../skeleton/Skeleton.svelte';
	import PickBox from './PickBox.svelte';
	import type { Column } from './types';
	import type { Selection } from './selection.svelte';
	import type { ListSort } from './list-sort.svelte';
	import SelectField from '../form/SelectField.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		columns,
		rows,
		rowKey,
		rowClass = () => '',
		highlight = () => false,
		first,
		cell,
		detail,
		onopen,
		onunfold,
		selection,
		selectable = () => true,
		actions,
		trailing,
		loading = false,
		sort
	}: {
		columns: Column<T>[];
		rows: T[];
		rowKey: (row: T) => string;
		rowClass?: (row: T) => string;
		highlight?: (row: T) => Tone | boolean;
		first?: Snippet<[T]>;
		cell?: Snippet<[T, Column<T>]>;
		detail?: Snippet<[T]>;
		/** Opens the row somewhere else (a page of its own) instead of unfolding it here. */
		onopen?: (row: T) => void;
		/** Called when a row's detail unfolds, to fetch what it shows. */
		onunfold?: (row: T) => void;
		selection?: Selection;
		selectable?: (row: T) => boolean;
		actions?: Snippet<[T]>;
		trailing?: string;
		loading?: boolean;
		/** The order the server applies; a column with a `sort` key gets a button in its header. */
		sort?: ListSort;
	} = $props();

	const SORT_ICONS = { none: 'ti-arrows-sort', ascending: 'ti-sort-ascending', descending: 'ti-sort-descending' } as const;
	const ARIA_SORT = { none: 'none', ascending: 'ascending', descending: 'descending' } as const;
	const DEFAULT_ORDER = '';
	const sortOptions = $derived(
		sort
			? columns.flatMap((column) =>
					column.sort
						? [
								{ value: column.sort, label: format(controlText.sortAscending, { name: column.label }) },
								{ value: `-${column.sort}`, label: format(controlText.sortDescending, { name: column.label }) }
							]
						: []
				)
			: []
	);
	const chooseOrder = (value: string) => {
		if (!sort) return;
		sort.set(value === DEFAULT_ORDER ? { kind: 'default' } : { kind: 'column', key: value.replace(/^-/, ''), descending: value.startsWith('-') });
	};

	const SKELETON_ROWS = 6;
	// Different widths so the placeholder reads as text, not as a block.
	const WIDTHS = ['w-3/4', 'w-1/2', 'w-2/3', 'w-5/6', 'w-1/3'];
	const bar = (row: number, column: number) => WIDTHS[(row * 2 + column) % WIDTHS.length];

	let open = $state<string | null>(null);

	const lead = $derived(columns[0]!);
	const side = $derived(columns.find((column) => column.key === trailing));
	const meta = $derived(columns.slice(1).filter((column) => column.key !== trailing));
	const align = (column: Column<T>) => (column.align === 'left' ? 'text-left' : '');
	const surface = (row: T, fallback: string) => {
		const mark = highlight(row);
		return mark === false ? fallback : tones[mark === true ? 'success' : mark].surface;
	};
	const picking = $derived(selection?.enabled ?? false);
	const pickable = $derived(rows.filter(selectable).map(rowKey));
	const picked = (row: T) => selection?.has(rowKey(row)) ?? false;
	const interactive = $derived(!!detail || !!onopen);
	const toggle = (row: T) => {
		if (onopen) return onopen(row);
		if (!detail) return;
		open = open === rowKey(row) ? null : rowKey(row);
		if (open !== null) onunfold?.(row);
	};
</script>

<div class="hidden tablet:block" aria-busy={loading}>
	<table class="w-full border-collapse text-right text-xs wrap-anywhere">
		<thead>
			<tr class="bg-brand text-brand-on">
				{#each columns as column, index (column.key)}
					<th
						class="wrap-normal px-3 py-2 font-semibold {align(column)} {index === 0 ? 'sticky left-0 z-10 bg-brand text-left' : ''}"
						aria-sort={sort && column.sort ? ARIA_SORT[sort.direction(column.sort)] : undefined}
					>
						{#if index === 0 && selection && picking}
							<span class="flex items-center gap-2">
								<PickBox label={controlText.selectAllRows} checked={selection.allIn(pickable)} disabled={pickable.length === 0} onchange={() => selection.setAll(pickable, !selection.allIn(pickable))} />
								{@render heading(column)}
							</span>
						{:else}
							{@render heading(column)}
						{/if}
					</th>
				{/each}
				{#if actions}<th class="w-px px-3 py-2"><span class="sr-only">{controlText.actions}</span></th>{/if}
			</tr>
		</thead>
		{#if loading}
		<tbody class="divide-y divide-slate-100">
				{#each { length: SKELETON_ROWS } as _, line (line)}
					<tr class="bg-white">
						{#each columns as column, index (column.key)}
							<td class="px-3 py-2.5 {index === 0 ? 'sticky left-0 z-10 bg-white' : ''}"><Skeleton class="h-3.5 {bar(line, index)} {index === 0 ? '' : 'ml-auto'}" /></td>
						{/each}
						{#if actions}<td class="px-3 py-2.5"><Skeleton class="h-6 w-16" /></td>{/if}
					</tr>
				{/each}
		</tbody>
		{:else}
			<!-- One body per row, so a row and its unfolded detail slide together when the order changes. -->
			{#each rows as row (rowKey(row))}
				{@const expanded = open === rowKey(row)}
				<tbody animate:reorder class="divide-y divide-slate-100 border-t border-slate-100 first-of-type:border-t-0">
				<tr
					onclick={() => toggle(row)}
					class="text-slate-700 hover:bg-brand-page {picked(row) ? 'bg-brand-page' : surface(row, 'bg-white')} {rowClass(row)} {interactive ? 'cursor-pointer' : ''}"
					aria-expanded={detail ? expanded : undefined}
				>
					{#each columns as column, index (column.key)}
						<td class="px-3 py-1.5 {align(column)} {column.class?.(row) ?? ''} {index === 0 ? 'sticky left-0 z-10 bg-inherit text-left font-medium' : ''}">
							{#if index === 0 && interactive}
								<span class="flex items-center gap-2">
									<i class="ti {expanded && detail ? 'ti-chevron-down' : 'ti-chevron-right'} text-slate-400" aria-hidden="true"></i>
									<span class="min-w-0">{#if first}{@render first(row)}{:else}{column.value(row)}{/if}</span>
								</span>
							{:else if index === 0 && selection && picking}
								<span class="flex items-center gap-2">
									{@render pick(row)}
									<span class="min-w-0">{#if first}{@render first(row)}{:else}{column.value(row)}{/if}</span>
								</span>
							{:else if index === 0 && first}
								{@render first(row)}
							{:else if cell}
								{@render cell(row, column)}
							{:else}
								{column.value(row)}
							{/if}
						</td>
					{/each}
					{#if actions}
						<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
						<td class="whitespace-nowrap px-3 py-1.5 text-right" onclick={(event) => event.stopPropagation()}>{@render actions(row)}</td>
					{/if}
				</tr>
				{#if detail && expanded}
					<tr class="bg-slate-50">
						<td colspan={columns.length + (actions ? 1 : 0)} class="px-3 pb-3 pt-1 text-left">{@render detail(row)}</td>
					</tr>
				{/if}
				</tbody>
			{/each}
		{/if}
	</table>
</div>

{#if sort && sortOptions.length > 0}
	<div class="border-b border-slate-100 px-4 py-2 tablet:hidden">
		<SelectField label={controlText.sort} compact value={sort.param ?? DEFAULT_ORDER} options={[{ value: DEFAULT_ORDER, label: controlText.defaultOrder }, ...sortOptions]} onchange={chooseOrder} />
	</div>
{/if}

<ul class="divide-y divide-slate-100 tablet:hidden" aria-busy={loading}>
	{#if loading}
		{#each { length: SKELETON_ROWS } as _, line (line)}
			<li class="flex flex-col gap-2 px-4 py-3">
				<span class="flex justify-between gap-3"><Skeleton class="h-4 w-1/2" /><Skeleton class="h-4 w-1/5" /></span>
				<Skeleton class="h-3 w-3/4" />
			</li>
		{/each}
	{:else}
	{#each rows as row (rowKey(row))}
		{@const expanded = open === rowKey(row)}
		<li animate:reorder class="{picked(row) ? 'bg-brand-page' : surface(row, '')} {rowClass(row)}">
			<svelte:element
				this={interactive ? 'button' : 'div'}
				role={interactive ? 'button' : undefined}
				type={interactive ? 'button' : undefined}
				onclick={interactive ? () => toggle(row) : undefined}
				aria-expanded={detail ? expanded : undefined}
				class="block w-full px-4 py-3 text-left"
			>
				<span class="flex items-start justify-between gap-3">
					<span class="flex min-w-0 items-start gap-2 text-sm font-semibold text-slate-800">
						{#if picking}{@render pick(row)}{/if}
						{#if interactive}<i class="ti {expanded && detail ? 'ti-chevron-down' : 'ti-chevron-right'} mt-0.5 shrink-0 text-slate-400" aria-hidden="true"></i>{/if}
						<span class="min-w-0">{#if first}{@render first(row)}{:else}{lead.value(row)}{/if}</span>
					</span>
					{#if side}
						<span class="shrink-0 text-sm font-semibold text-slate-800">{side.value(row)}</span>
					{/if}
				</span>
				<dl class="mt-2 grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
					{#each meta as column (column.key)}
						<div>
							<dt class="text-slate-500">{column.label}</dt>
							<dd class="font-semibold text-slate-700 {column.class?.(row) ?? ''}">
								{#if cell}{@render cell(row, column)}{:else}{column.value(row)}{/if}
							</dd>
						</div>
					{/each}
				</dl>
			</svelte:element>
			{#if actions}
				<div class="flex justify-end gap-2 px-4 pb-3">{@render actions(row)}</div>
			{/if}
			{#if detail && expanded}
				<div class="border-t border-slate-100 bg-slate-50 px-4 py-3">{@render detail(row)}</div>
			{/if}
		</li>
	{/each}
	{/if}
</ul>

{#snippet heading(column: Column<T>)}
	{#if sort && column.sort}
		{@const key = column.sort}
		<button type="button" class="inline-flex items-center gap-1 font-medium hover:text-brand-line" onclick={() => sort.toggle(key)}>
			{column.label}
			<i class="ti {SORT_ICONS[sort.direction(key)]} {sort.direction(key) === 'none' ? 'opacity-50' : ''}" aria-hidden="true"></i>
		</button>
	{:else}
		{column.label}
	{/if}
{/snippet}

{#snippet pick(row: T)}
	{#if selectable(row)}
		<span class="mt-0.5 flex"><PickBox label={controlText.selectRow} checked={picked(row)} onchange={() => selection?.toggle(rowKey(row))} /></span>
	{:else}
		<span class="size-4 shrink-0"></span>
	{/if}
{/snippet}
