<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { PaymentMethod, PaymentMethodUpdate } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { methodStatus, missingText } from '../columns';
	import PaymentMethodForm from './PaymentMethodForm.svelte';
	import { termText } from '$lib/text/terms';
	import { paymentMethodText } from '$lib/text/payment-methods';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<PaymentMethod, PaymentMethodUpdate, null>(untrack(() => id), {
		load: (methodId) => api.paymentMethods.detail(methodId),
		update: (method, body) => api.paymentMethods.update(method, body),
		remove: (method) => api.paymentMethods.remove(method),
		name: (method) => method.label,
		text: recordText('metode pembayaran', PAGES.paymentMethods.label)
	});

	const yesNo = (value: boolean) => (value ? termText.yes : termText.no);

	// Menonaktifkan ditanyakan dulu karena kasir langsung kehilangan pilihan ini.
	let deactivating = $state<PaymentMethod | null>(null);

	function setActive(active: boolean): void {
		void detail.change((current) => api.paymentMethods.update(current, { is_active: active }), paymentMethodText.statusChangeFailed);
	}

	function confirmDeactivate(): void {
		deactivating = null;
		setActive(false);
	}
</script>

<RecordDetailView
	{detail}
	back={PAGES.paymentMethods}
	trail={(method) => [{ label: PAGES.paymentMethods.label, href: PAGES.paymentMethods.path }, { label: method.label }]}
	tables={['payment_methods']}
	title={(method) => method.label}
	description={(method) => method.outlet_name}
>
	{#snippet badge(method)}
		{@const status = methodStatus(method)}
		<Badge tone={status.tone} title={missingText(method)}><i class="ti ti-{status.icon}" aria-hidden="true"></i>{status.label}</Badge>
	{/snippet}
	{#snippet extraActions(method)}
		<Button
			label={method.is_active ? paymentMethodText.deactivate : paymentMethodText.activate}
			icon={method.is_active ? 'eye-off' : 'eye'}
			variant="tertiary"
			disabled={detail.busy || (!method.is_active && method.missing.length > 0)}
			hint={!method.is_active && method.missing.length > 0 ? paymentMethodText.activateNeedsComplete : undefined}
			onclick={() => (method.is_active ? (deactivating = method) : setActive(true))}
		/>
	{/snippet}
	{#snippet body(method)}
		{#if method.missing.length > 0}
			<Banner tone="warning" icon="alert-triangle">{format(paymentMethodText.missingFieldsHint, { fields: method.missing.join(' dan ') })}</Banner>
		{/if}
		<div class="grid items-stretch gap-4 tablet:gap-6 laptop:grid-cols-[20rem_minmax(0,1fr)]">
			<Card flush>
				<div class="flex h-full flex-col gap-3 bg-brand-soft p-4">
					<span class="text-xs font-medium text-brand-deep">{paymentMethodText.image}</span>
					<div class="flex aspect-4/3 items-center justify-center overflow-hidden rounded-lg bg-brand-tint laptop:aspect-auto laptop:flex-1">
						{#if method.image_url}
							<img src={method.image_url} alt={format(paymentMethodText.imageOf, { name: method.label })} class="size-full object-contain" />
						{:else}
							<span class="flex flex-col items-center gap-2 text-xs text-brand-deep">
								<i class="ti ti-photo text-display" aria-hidden="true"></i>
								{paymentMethodText.noImage}
							</span>
						{/if}
					</div>
					{#if method.missing.length > 0}
						<span class="text-xs text-warning-700">{format(paymentMethodText.notFilledList, { fields: method.missing.join(', ') })}</span>
					{/if}
				</div>
			</Card>
			<Card class="flex flex-col gap-5">
				<div class="grid gap-5 tablet:grid-cols-2">
					<FigureList
						title={termText.method}
						figures={[
							{ label: termText.name, value: method.label },
							{ label: termText.code, value: method.code },
							{ label: termText.branch, value: method.outlet_name },
							{ label: termText.status, value: method.is_active ? termText.active : termText.inactive }
						]}
					/>
					<FigureList
						title={termText.payment}
						figures={[
							{ label: paymentMethodText.needsChange, value: yesNo(method.needs_change) },
							{ label: paymentMethodText.fee, value: Number(method.fee_percent) > 0 ? `${formatNumber(method.fee_percent)}%` : EMPTY_VALUE },
							{ label: paymentMethodText.inUse, value: method.used_by_orders > 0 ? format(paymentMethodText.usedByOrders, { count: formatNumber(method.used_by_orders, 0) }) : EMPTY_VALUE }
						]}
					/>
				</div>
				<section class="flex flex-col gap-1 border-t border-slate-100 pt-4 text-xs">
					<h3 class="font-semibold text-slate-600">{termText.note}</h3>
					<p class="whitespace-pre-line {method.note ? 'text-slate-700' : 'text-slate-500'}">{method.note || termText.noNote}</p>
				</section>
			</Card>
		</div>
	{/snippet}
	{#snippet form(props)}
		<PaymentMethodForm
			method={props.record}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body) => props.onsave(body as PaymentMethodUpdate)}
			onupload={(file) => void detail.change((current) => api.paymentMethods.uploadImage(current, file), paymentMethodText.imageUploadFailed)}
			onremoveimage={() => void detail.change((current) => api.paymentMethods.removeImage(current), paymentMethodText.imageRemoveFailed)}
			onclose={props.onclose}
		/>
	{/snippet}
	{#snippet removeNote(method)}
		{#if method.used_by_orders > 0}
			<RichText template={paymentMethodText.methodUsageNote} values={{ count: formatNumber(method.used_by_orders, 0) }} />
		{:else}
			{paymentMethodText.noOrders}
		{/if}
	{/snippet}
</RecordDetailView>

<ConfirmDialog
	open={deactivating !== null}
	title={format(paymentMethodText.deactivateTitle, { name: deactivating?.label ?? '' })}
	confirmLabel={paymentMethodText.deactivate}
	busy={detail.busy}
	onconfirm={confirmDeactivate}
	oncancel={() => (deactivating = null)}
>
	{format(paymentMethodText.deactivateNote, { branch: deactivating?.outlet_name ?? '' })}
</ConfirmDialog>
