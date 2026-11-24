<script lang="ts">
	let {
		label,
		hint,
		checked,
		disabled = false,
		onchange
	}: {
		label: string;
		hint?: string;
		checked: boolean;
		disabled?: boolean;
		onchange: () => void;
	} = $props();
</script>

<label class="flex items-start gap-2.5 rounded-md p-2 {disabled ? 'cursor-default opacity-70' : 'cursor-pointer hover:bg-brand-page'}">
	<input type="checkbox" {checked} {disabled} {onchange} class="mt-0.5 size-4 shrink-0 accent-brand" />
	<span class="min-w-0">
		<span class="block text-sm text-slate-800">{label}</span>
		{#if hint}
			<span class="block text-xs leading-snug text-slate-500">{hint}</span>
		{/if}
	</span>
</label>
