<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { Action } from '../button/types';
	import BulkChangeDialog from '../dialog/BulkChangeDialog.svelte';
	import ConfirmDialog from '../dialog/ConfirmDialog.svelte';
	import type { Field } from '../form/types';
	import BulkBar from './BulkBar.svelte';
	import type { Selection } from './selection.svelte';
	import { actionText } from '$lib/text/actions';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	/** Everything done to the rows a person picked: the bar, the delete confirmation and the change dialog. [removing] and [changing] are the screen's own flags, so closing every dialog at once keeps working. */
	let {
		selection,
		noun,
		removing = $bindable(false),
		changing = $bindable(false),
		fields,
		busy = false,
		error = '',
		onremove,
		onchange,
		oncancel,
		children
	}: {
		selection: Selection;
		noun: string;
		removing?: boolean;
		changing?: boolean;
		fields?: Field[];
		busy?: boolean;
		error?: string;
		onremove: () => void;
		onchange?: (changes: Record<string, string | number | boolean>) => void;
		oncancel: () => void;
		children?: Snippet;
	} = $props();

	const actions = $derived<Action[]>([
		...(onchange && fields ? [{ label: actionText.edit, icon: 'pencil', onclick: () => (changing = true) }] : []),
		{ label: actionText.remove, icon: 'trash', danger: true, onclick: () => (removing = true) }
	]);
</script>

<BulkBar {selection} {actions} />

<ConfirmDialog open={removing} title={format(controlText.removeSelectedTitle, { count: selection.count, noun: noun })} confirmLabel="Hapus" danger {busy} {error} onconfirm={onremove} {oncancel}>
	{@render children?.()}
</ConfirmDialog>

{#if changing && onchange && fields}
	<BulkChangeDialog count={selection.count} {fields} {busy} {error} onsubmit={onchange} onclose={oncancel} />
{/if}
