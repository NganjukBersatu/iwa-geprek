<script lang="ts">
	/** The tick that selects a row for a bulk action; a click on it never also opens the row. */
	let { label, checked, disabled = false, onchange }: { label: string; checked: boolean; disabled?: boolean; onchange: () => void } = $props();
</script>

<input type="checkbox" {checked} {disabled} {onchange} onclick={(event) => event.stopPropagation()} aria-label={label} class="size-4 shrink-0 accent-brand" />
