<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { IngredientMovement, IngredientMovementUpdate } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { STOCK_TABLES } from '$lib/live/tables';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { WASTE } from '../kinds';
	import LossForm from './LossForm.svelte';
	import { ingredientLossText } from '$lib/text/ingredient-losses';
	import { format } from '$lib/text/format';

	type LossSave = { body: IngredientMovementUpdate; proof: File | null };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<IngredientMovement, LossSave>(untrack(() => id), {
		load: (movementId) => api.ingredientMovements.detail(movementId),
		update: async (movement, { body, proof }) => {
			const saved = await api.ingredientMovements.update(movement.id, body);
			return proof ? api.ingredientMovements.uploadProof(saved.id, proof) : saved;
		},
		remove: (movement) => api.ingredientMovements.remove(movement.id),
		name: (movement) => movement.ingredient_name,
		text: recordText('catatan bahan', PAGES.ingredientWaste.label)
	});

	const quantity = (movement: IngredientMovement) => `${formatNumber(Math.abs(Number(movement.qty)))} ${movement.unit}`;
</script>

<RecordDetailView
	{detail}
	back={PAGES.ingredientWaste}
	trail={(movement) => [{ label: PAGES.ingredientWaste.label, href: PAGES.ingredientWaste.path }, { label: movement.ingredient_name }]}
	tables={STOCK_TABLES}
	title={(movement) => movement.ingredient_name}
	description={(movement) => `${movement.kind === WASTE ? ingredientLossText.damagedIngredients : ingredientLossText.rndIngredients} · ${quantity(movement)} · ${formatDate(movement.business_day)}`}
>
	{#snippet badge(movement)}
		{#if movement.cause_label}<Badge tone={movement.human_error ? 'danger' : 'neutral'}>{movement.cause_label}</Badge>{/if}
	{/snippet}
	{#snippet body(movement)}
		<div class="grid items-stretch gap-4 tablet:gap-6 laptop:grid-cols-[20rem_minmax(0,1fr)]">
			<Card flush>
				<div class="flex h-full flex-col gap-3 bg-brand-soft p-4">
					<span class="text-xs font-medium text-brand-deep">{ingredientLossText.proofPhoto}</span>
					<div class="flex aspect-4/3 items-center justify-center overflow-hidden rounded-lg bg-brand-tint laptop:aspect-auto laptop:flex-1">
						{#if movement.proof_url}
							<a href={movement.proof_url} target="_blank" rel="noopener" class="size-full" aria-label={format(ingredientLossText.openProofPhoto, { name: movement.ingredient_name })}>
								<img src={movement.proof_url} alt={format(ingredientLossText.proofOf, { name: movement.ingredient_name })} class="size-full object-cover" />
							</a>
						{:else}
							<span class="flex flex-col items-center gap-2 text-xs text-brand-deep">
								<i class="ti ti-photo text-display" aria-hidden="true"></i>
								{ingredientLossText.noProofPhoto}
							</span>
						{/if}
					</div>
				</div>
			</Card>
			<Card class="flex flex-col gap-5">
				<div class="grid gap-5 tablet:grid-cols-2">
					<FigureList
						title={movement.kind === WASTE ? ingredientLossText.damagedIngredients : ingredientLossText.rndIngredients}
						figures={[
							{ label: termText.ingredient, value: movement.ingredient_name },
							{ label: termText.quantity, value: quantity(movement) },
							...(movement.kind === WASTE ? [{ label: ingredientLossText.cause, value: movement.cause_label ?? EMPTY_VALUE }] : [])
						]}
					/>
					<FigureList
						title={termText.recording}
						figures={[
							{ label: termText.day, value: formatDate(movement.business_day) },
							{ label: termText.recordedAt, value: formatDateTime(movement.created_at) },
							{ label: termText.recordedByPerson, value: movement.user_name ?? EMPTY_VALUE }
						]}
					/>
				</div>
				<section class="flex flex-col gap-1 border-t border-slate-100 pt-4 text-xs">
					<h3 class="font-semibold text-slate-600">{movement.kind === WASTE ? termText.note : ingredientLossText.triedMenu}</h3>
					<p class="whitespace-pre-line {movement.note ? 'text-slate-700' : 'text-slate-500'}">{movement.note ?? (movement.kind === WASTE ? termText.noNote : termText.noRemark)}</p>
				</section>
			</Card>
		</div>
	{/snippet}
	{#snippet form(props)}
		<LossForm movement={props.record} kind={props.record.kind} causes={[]} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body, proof) => props.onsave({ body: body as IngredientMovementUpdate, proof })} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{ingredientLossText.removeNote}
	{/snippet}
</RecordDetailView>
