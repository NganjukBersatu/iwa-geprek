<script lang="ts">
	let { id, error, hint, large = false }: { id: string; error?: string; hint?: string; large?: boolean } = $props();
</script>

{#if error}
	<p {id} role="alert" class="flex items-start gap-1 text-danger-700 {large ? 'text-sm' : 'text-xs'}">
		<i class="ti ti-alert-circle shrink-0 leading-4 {large ? 'text-base' : 'text-sm'}" aria-hidden="true"></i>
		<span>{error}</span>
	</p>
{:else if hint}
	<p {id} class="text-slate-500 {large ? 'text-sm' : 'text-xs'}">{hint}</p>
{/if}
