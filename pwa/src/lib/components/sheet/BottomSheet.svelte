<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import { t } from '$lib/text/t';

	const ENTER_MILLIS = 280;
	const EXIT_MILLIS = 200;
	const MAX_HEIGHT_FRACTION = 0.9;

	/** Panel modal dari tepi bawah yang ditutup dengan ketuk di luar, tombol tutup, atau Esc, kecuali [dismissible] false. */
	let {
		title,
		onDismiss,
		dismissible = true,
		visible = true,
		children
	}: {
		title: string;
		onDismiss: () => void;
		dismissible?: boolean;
		visible?: boolean;
		children: Snippet;
	} = $props();

	let shown = $state(false);
	let closing = false;

	onMount(() => {
		const frame = requestAnimationFrame(() => (shown = true));
		return () => cancelAnimationFrame(frame);
	});

	function close(): void {
		if (closing) return;
		closing = true;
		shown = false;
		setTimeout(onDismiss, EXIT_MILLIS);
	}

	$effect(() => {
		if (!visible) close();
	});

	function onKeydown(event: KeyboardEvent): void {
		if (event.key === 'Escape' && dismissible) close();
	}
</script>

<svelte:window onkeydown={onKeydown} />

<div class="fixed inset-0 z-50 flex items-end justify-center" role="presentation">
	<button
		type="button"
		tabindex="-1"
		aria-label={t('sheet_close')}
		disabled={!dismissible}
		onclick={close}
		class="absolute inset-0 cursor-default bg-dim"
		use:dynamicStyle={{ opacity: shown ? 1 : 0, transition: `opacity ${shown ? ENTER_MILLIS : EXIT_MILLIS}ms linear` }}
	></button>
	<div
		role="dialog"
		aria-modal="true"
		aria-label={title}
		class="relative flex w-full max-w-[var(--size-content-max)] flex-col overflow-hidden rounded-t-sheet bg-background"
		use:dynamicStyle={{ 'max-height': `${MAX_HEIGHT_FRACTION * 100}dvh`, transform: shown ? 'translateY(0)' : 'translateY(100%)', transition: `transform ${shown ? ENTER_MILLIS : EXIT_MILLIS}ms ${shown ? 'var(--ease-standard)' : 'var(--ease-fast-out-linear-in)'}` }}
	>
		<div class="flex items-center justify-between pl-4">
			<h2 class="text-title m-0 flex-1 text-content">{title}</h2>
			{#if dismissible}
				<button type="button" onclick={close} class="flex size-[var(--space-touch)] items-center justify-center" aria-label={t('sheet_close')}>
					<AppIcon icon="Close" tint="content" />
				</button>
			{:else}
				<span class="size-[var(--space-touch)]"></span>
			{/if}
		</div>
		<Divider />
		<div class="overflow-y-auto p-4" use:dynamicStyle={{ 'padding-bottom': 'calc(16px + var(--safe-bottom))' }}>
			{@render children()}
		</div>
	</div>
</div>
