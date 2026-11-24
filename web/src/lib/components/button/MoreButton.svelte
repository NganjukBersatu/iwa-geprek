<script lang="ts" generics="T">
	import { userMessage } from '$lib/api/user-message';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { EXPORT_FORMATS, exportTable, type Exporter } from '$lib/export/table';
	import type { Selection } from '../table/selection.svelte';
	import MenuButton from './MenuButton.svelte';
	import type { Action } from './types';
	import { controlText } from '$lib/text/controls';
	import { format as fillText } from '$lib/text/format';

	/** The three-dot menu of a list screen: downloads of the list and the switch for picking several rows. */
	let { selection, extra = [], exporter }: { selection?: Selection | Selection[]; extra?: Action[]; exporter?: Exporter<T> } = $props();

	/** A screen with two lists passes both selections; they switch together. */
	const picks = $derived(selection === undefined ? [] : Array.isArray(selection) ? selection : [selection]);
	const picking = $derived(picks[0]?.enabled ?? false);
	const ticked = $derived(picks[0]?.count ?? 0);

	let busy = $state(false);

	async function download(format: (typeof EXPORT_FORMATS)[number]['format']): Promise<void> {
		if (!exporter || busy) return;
		busy = true;
		toast.busy(fillText(controlText.preparingDownload, { kind: EXPORT_FORMATS.find((item) => item.format === format)?.label ?? 'unduhan', title: exporter.title }));
		try {
			const count = await exportTable(format, exporter);
			toast.show(count === 0 ? controlText.nothingToDownload : fillText(controlText.rowsDownloaded, { count: count }), count === 0 ? 'error' : 'ok');
		} catch (error) {
			toast.show(userMessage(error, controlText.downloadFailed), 'error');
		} finally {
			busy = false;
		}
	}

	const items = $derived<Action[]>([
		...(exporter ? EXPORT_FORMATS.map((item) => ({ label: fillText(controlText.downloadKind, { kind: item.label }), icon: item.icon, description: ticked > 0 ? fillText(controlText.rowsSelected, { count: ticked }) : controlText.allRowsMatchingFilter, disabled: busy, onclick: () => void download(item.format) })) : []),
		...extra,
		...(picks.length > 0 ? [{ label: picking ? controlText.doneSelecting : controlText.selectSeveral, icon: picking ? 'x' : 'checkbox', onclick: () => picks.forEach((pick) => pick.setMode(!picking)) }] : [])
	]);
</script>

<MenuButton label={controlText.otherActions} icon="dots" iconOnly {items} />
