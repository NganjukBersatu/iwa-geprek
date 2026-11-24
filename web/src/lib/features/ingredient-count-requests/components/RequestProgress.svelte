<script lang="ts">
	import type { IngredientCountRequest } from '$lib/api/types';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { ingredientCountRequestText as text } from '$lib/text/ingredient-count-requests';
	import { format } from '$lib/text/format';

	let { request }: { request: IngredientCountRequest } = $props();

	type Step = { icon: string; label: string; detail: string; tone: 'done' | 'waiting' | 'danger' };

	const by = (name: string | null, at: string | null): string => `${name ?? EMPTY_VALUE}${at ? ` · ${formatDateTime(at)}` : ''}`;

	/** Tiga tahap pengajuan: diajukan, dilihat admin, lalu ditutup atau ditolak. */
	const steps = $derived<Step[]>([
		{ icon: 'send', label: text.stepRequested, detail: by(request.requested_by, request.created_at), tone: 'done' },
		request.seen_at
			? { icon: 'eye', label: text.stepSeen, detail: by(request.seen_by, request.seen_at), tone: 'done' }
			: { icon: 'eye-off', label: request.status === 'pending' ? text.stepNotSeen : text.stepNeverOpened, detail: '', tone: 'waiting' },
		request.status === 'closed'
			? { icon: 'lock', label: text.stepClosed, detail: by(request.decided_by, request.decided_at), tone: 'done' }
			: request.status === 'rejected'
				? { icon: 'x', label: text.stepRejected, detail: by(request.decided_by, request.decided_at), tone: 'danger' }
				: { icon: 'hourglass', label: text.stepWaiting, detail: '', tone: 'waiting' }
	]);

	const TONES = { done: 'bg-brand-soft text-brand', waiting: 'bg-slate-100 text-slate-500', danger: 'bg-danger-50 text-danger-700' } as const;
</script>

<ol class="flex w-full flex-col gap-2" aria-label={text.progressLabel}>
	{#each steps as step (step.label)}
		<li class="flex items-center gap-3">
			<span class="flex size-8 shrink-0 items-center justify-center rounded-full {TONES[step.tone]}"><i class="ti ti-{step.icon}" aria-hidden="true"></i></span>
			<span class="flex flex-col">
				<span class="text-sm font-medium text-slate-800">{step.label}</span>
				{#if step.detail}<span class="text-xs text-slate-500">{step.detail}</span>{/if}
			</span>
		</li>
	{/each}
	{#if request.note}
		<li class="pl-11 text-xs text-slate-500">{format(text.progressNote, { note: request.note })}</li>
	{/if}
</ol>
