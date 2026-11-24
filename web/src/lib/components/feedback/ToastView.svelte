<script lang="ts">
	import { enter } from '$lib/motion/transitions';
	import { toast } from './toast.svelte';
	import { controlText } from '$lib/text/controls';

	const SURFACES = {
		ok: 'border-success-200 bg-success-50/90 text-success-700',
		error: 'border-danger-200 bg-danger-50/90 text-danger-700',
		busy: 'border-brand-tint bg-brand-page/90 text-brand-ink'
	} as const;
	const ICONS = { ok: 'circle-check', error: 'alert-triangle', busy: 'loader-2' } as const;
</script>

{#if toast.message}
	<div class="pointer-events-none fixed inset-x-0 bottom-4 z-60 flex justify-center px-4" role={toast.message.kind === 'error' ? 'alert' : 'status'} transition:enter={{ y: 16 }}>
		<div class="pointer-events-auto max-w-sm overflow-hidden rounded-lg border text-xs font-medium shadow-md backdrop-blur-sm {SURFACES[toast.message.kind]}">
			<div class="flex items-center gap-2 py-2 pr-1.5 pl-3">
				<i class="ti ti-{ICONS[toast.message.kind]} shrink-0 text-base {toast.message.kind === 'busy' ? 'animate-spin motion-reduce:animate-none' : ''}" aria-hidden="true"></i>
				<p class="min-w-0 flex-1">{toast.message.text}</p>
				{#if toast.message.kind !== 'busy'}
					<button type="button" onclick={() => toast.dismiss()} aria-label={controlText.closeMessage} class="flex size-6 shrink-0 items-center justify-center rounded-md hover:bg-black/5 focus-visible:outline-2 focus-visible:outline-current">
						<i class="ti ti-x text-sm" aria-hidden="true"></i>
					</button>
				{/if}
			</div>
			{#if toast.message.kind === 'busy'}
				<div class="toast-progress" aria-hidden="true"></div>
			{/if}
		</div>
	</div>
{/if}
