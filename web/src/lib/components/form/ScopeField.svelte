<script lang="ts">
	import SelectField from './SelectField.svelte';
	import { ALL_BRANCHES_TEXT, type BranchOption } from './branch-prices.svelte';
	import { termText } from '$lib/text/terms';

	/** Item yang dimiliki satu cabang atau semua cabang; kosong berarti semua cabang. */
	let { value = $bindable(''), outlets, label = termText.appliesAt, hint }: { value?: string; outlets: BranchOption[]; label?: string; hint?: string } = $props();

	const options = $derived([{ value: '', label: ALL_BRANCHES_TEXT }, ...outlets.map((outlet) => ({ value: outlet.id, label: outlet.name }))]);
</script>

<SelectField {label} bind:value {options} {hint} />
