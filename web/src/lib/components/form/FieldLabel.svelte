<script lang="ts">
	/** The one label of every field: one line above the box, no colon, with a red mark when the field is required. */
	let {
		for: target,
		label,
		required = false,
		compact = false,
		large = false
	}: {
		for: string;
		label: string;
		required?: boolean;
		/** Inside a list row the label stays for screen readers only. */
		compact?: boolean;
		large?: boolean;
	} = $props();
</script>

<label for={target} class={compact ? 'sr-only' : large ? 'text-base font-semibold text-brand-muted' : 'text-xs font-semibold text-slate-600'}>
	{label}{#if required}<span class="text-danger-500" aria-hidden="true"> *</span>{/if}
</label>
