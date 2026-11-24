<script lang="ts">
	import { get } from 'svelte/store';
	import { onMount } from 'svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import { branches, loadBranchOptions, selectedBranch } from '$lib/stores/branch';
	import { termText } from '$lib/text/terms';
	import { controlText } from '$lib/text/controls';

	let {
		value = $bindable(''),
		label = termText.branch,
		disabled = false,
		everyLabel,
		error,
		onchange
	}: {
		value?: string;
		label?: string;
		disabled?: boolean;
		/** Offers "every branch" as the empty choice, for records that may belong to all branches at once. */
		everyLabel?: string;
		/** What is wrong with the choice, shown under the box. */
		error?: string;
		onchange?: (value: string) => void;
	} = $props();

	const options = $derived($branches.map((branch) => ({ value: branch.id, label: branch.name })));

	// A new row goes to the branch chosen in the filter, or to the only branch there is; otherwise the person picks.
	onMount(async () => {
		if ($branches.length === 0) await loadBranchOptions();
		if (value || everyLabel !== undefined) return;
		const [only, second] = $branches;
		value = get(selectedBranch) ?? (only && !second ? only.id : '');
		if (value) onchange?.(value);
	});
</script>

{#if options.length > 1 || (everyLabel !== undefined && options.length > 0)}
	<SelectField {label} bind:value {options} empty={everyLabel ?? controlText.chooseBranch} {disabled} {error} {onchange} />
{/if}
