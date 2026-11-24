<script lang="ts">
	import { shiftCodeBulkPath, shiftCodeNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import ShiftCodesView from '$lib/features/shift-codes/components/ShiftCodesView.svelte';
	import { ShiftCodesState } from '$lib/features/shift-codes/shift-codes.svelte';
	import { shiftCodeColumns } from '$lib/features/shift-codes/columns';
	import { pageText } from '$lib/text/pages';
	import { shiftCodeText } from '$lib/text/shift-codes';

	const shiftCodes = new ShiftCodesState();
</script>

<ManageShell
	manage={shiftCodes}
	filters={shiftCodes.filters}
	title={pageText.shiftCodesTitle}
	description={pageText.shiftCodesDescription}
	loadingText={pageText.loadingShiftCodes}
>
	{#snippet actions()}
		<Button label={shiftCodeText.categorySettings} icon="adjustments" variant="tertiary" onclick={() => (shiftCodes.categoriesOpen = true)} />
		<AddButton label={pageText.addCode} onone={() => void goto(shiftCodeNewPath())} onmany={() => void goto(shiftCodeBulkPath())} />
		<MoreButton selection={shiftCodes.selection} exporter={{ title: pageText.exportTitles.shiftCodes, columns: shiftCodeColumns, rows: () => shiftCodes.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<ShiftCodesView {shiftCodes} />
	{/snippet}
</ManageShell>
