<script lang="ts" module>
	/** A column of the matrix; `head` styles its heading, `pin` keeps it on screen at the right edge (offset and width classes). */
	export type MatrixColumn = { key: string; label: string; head?: string; pin?: string; strong?: boolean };
	/** A heading spanning several columns above them, such as Pemasukan over Tunai, Non Tunai and Total. */
	export type MatrixGroup = { key: string; label: string; span: number; head: string; pin?: string };
</script>

<script lang="ts" generics="T">
	import type { Snippet } from 'svelte';

	/**
	 * The one table that may scroll sideways: a grid whose two axes are both data (days by money parts, people by dates), where
	 * squeezing columns into a list would hide the comparison it exists for. Lists use DataTable.
	 */
	let {
		leadLabel,
		columns,
		groups,
		rows,
		rowKey,
		lead,
		cell,
		rowClass = () => 'bg-white',
		leadClass = () => '',
		onrowclick,
		minWidth = ''
	}: {
		leadLabel: string;
		columns: MatrixColumn[];
		groups?: MatrixGroup[];
		rows: T[];
		rowKey: (row: T) => string;
		/** The first, pinned column of a row. */
		lead: Snippet<[T]>;
		cell: Snippet<[T, MatrixColumn]>;
		/** The row's background and ink; pinned cells take the same background, so it must not be transparent. */
		rowClass?: (row: T) => string;
		/** Extra classes for a row's first cell, such as a status stripe. */
		leadClass?: (row: T) => string;
		/** Rows that open something on click; the others stay plain. */
		onrowclick?: (row: T) => (() => void) | undefined;
		/** A minimum width class when the columns need more room than the screen gives. */
		minWidth?: string;
	} = $props();
</script>

<div class="overflow-x-auto">
	<table class="w-full border-collapse text-right text-xs {minWidth}">
		<thead>
			{#if groups}
				<tr class="text-brand-on">
					<th rowspan="2" class="sticky left-0 z-10 border-r border-white/20 bg-brand px-3 py-2 text-left align-bottom">{leadLabel}</th>
					{#each groups as group (group.key)}
						<th colspan={group.span} class="px-3 py-1.5 text-center {group.head} {group.pin ?? ''}">{group.label}</th>
					{/each}
				</tr>
			{/if}
			<tr class={groups ? 'bg-slate-50 text-slate-500' : 'bg-brand text-brand-on'}>
				{#if !groups}
					<th class="sticky left-0 z-10 min-w-32 bg-brand px-3 py-2 text-left font-medium">{leadLabel}</th>
				{/if}
				{#each columns as column (column.key)}
					<th class="px-3 py-1.5 {column.strong ? 'font-semibold' : 'font-medium'} {column.pin ? `sticky z-10 ${groups ? 'bg-slate-50' : 'bg-brand'} ${column.pin}` : ''} {column.head ?? ''}">{column.label}</th>
				{/each}
			</tr>
		</thead>
		<tbody class="divide-y divide-slate-100">
			{#each rows as row (rowKey(row))}
				{@const open = onrowclick?.(row)}
				<tr class="group/row hover:bg-brand-page {open ? 'cursor-pointer' : ''} {rowClass(row)}" onclick={open}>
					<th class="sticky left-0 z-10 bg-inherit px-3 py-1.5 text-left font-medium group-hover/row:bg-brand-page {leadClass(row)}">{@render lead(row)}</th>
					{#each columns as column (column.key)}
						<td class="px-3 py-1.5 {column.strong ? 'font-semibold' : ''} {column.pin ? `sticky z-10 bg-inherit ${column.pin} group-hover/row:bg-brand-page` : ''}">{@render cell(row, column)}</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>
