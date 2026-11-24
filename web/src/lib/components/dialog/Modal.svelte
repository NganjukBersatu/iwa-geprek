<script lang="ts">
	import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';
	import type { Snippet } from 'svelte';
	import { scrollShadow } from '$lib/motion/actions';
	import { actionText } from '$lib/text/actions';

	let {
		open,
		title,
		description,
		size = 'md',
		busy = false,
		onclose,
		children,
		footer
	}: {
		open: boolean;
		title: string;
		description?: string;
		size?: 'sm' | 'md' | 'lg';
		busy?: boolean;
		onclose: () => void;
		children: Snippet;
		footer?: Snippet;
	} = $props();

	let head = $state<HTMLElement | null>(null);

	const width = { sm: 'tablet:max-w-md', md: 'tablet:max-w-2xl', lg: 'tablet:max-w-4xl' };
</script>

{#if open}
<Dialog open onOpenChange={(details) => !details.open && !busy && onclose()}>
	<Portal>
		<Dialog.Backdrop class="backdrop-in fixed inset-0 z-50 bg-slate-700/40" />
		<Dialog.Positioner class="fixed inset-0 z-50 flex items-stretch justify-center tablet:items-center tablet:p-6">
			<Dialog.Content class="modal-in flex h-dvh w-full flex-col bg-white outline-none tablet:h-auto tablet:max-h-[90dvh] tablet:rounded-xl tablet:shadow-xl {width[size]}">
				<header bind:this={head} data-scroll-head class="flex items-start justify-between gap-3 border-b border-slate-100 bg-white px-4 py-3 tablet:rounded-t-xl tablet:px-6 tablet:py-4">
					<div class="min-w-0">
						<Dialog.Title class="text-base font-semibold text-brand-ink">{title}</Dialog.Title>
						{#if description}
							<Dialog.Description class="mt-0.5 text-xs leading-5 text-slate-500">{description}</Dialog.Description>
						{/if}
					</div>
					<Dialog.CloseTrigger disabled={busy} aria-label={actionText.close} class="-mr-2 shrink-0 rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-600 disabled:opacity-50">
						<i class="ti ti-x text-xl" aria-hidden="true"></i>
					</Dialog.CloseTrigger>
				</header>
				<div use:scrollShadow={head} class="min-h-0 flex-1 overflow-y-auto px-4 py-4 tablet:px-6">
					{@render children()}
				</div>
				{#if footer}
					<footer class="flex flex-col-reverse gap-2 border-t border-slate-100 px-4 py-3 tablet:flex-row tablet:items-center tablet:justify-end tablet:px-6">
						{@render footer()}
					</footer>
				{/if}
			</Dialog.Content>
		</Dialog.Positioner>
	</Portal>
</Dialog>
{/if}
