<script lang="ts">
	/** The browser's own colour picker, with the chosen code written beside it. */
	let { label, value = $bindable() }: { label: string; value: string } = $props();

	const id = $props.id();
</script>

<div class="flex flex-col gap-1">
	<label for={id} class="text-xs font-semibold text-slate-600">{label}</label>
	<div class="flex items-center gap-2">
		<input {id} type="color" bind:value class="h-10 w-14 cursor-pointer rounded-lg border border-slate-200 bg-white p-1" />
		<span class="font-mono text-xs text-slate-500">{value}</span>
	</div>
</div>
