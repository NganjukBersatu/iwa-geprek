<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import type { PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { PAGES, paymentMethodPath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import { PAYMENT_ICONS } from '../payment-methods.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { paymentMethodText } from '$lib/text/payment-methods';
	import { format } from '$lib/text/format';

	let {
		method,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onupload,
		onremoveimage,
		onclose
	}: {
		method: PaymentMethod | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: PaymentMethodCreate | PaymentMethodUpdate, outletId: string) => void;
		onupload: (file: File) => void;
		onremoveimage: () => void;
		onclose: () => void;
	} = $props();

	const CODE_PATTERN = /^[a-z0-9_]{2,16}$/;
	const current = untrack(() => method);
	const trail = [
		{ label: PAGES.paymentMethods.label, href: PAGES.paymentMethods.path },
		...(current ? [{ label: current.label, href: paymentMethodPath(current.id) }, { label: actionText.edit }] : [{ label: paymentMethodText.addMethod }])
	];

	let code = $state('');
	let outletId = $state(current?.outlet_id ?? '');
	let label = $state(current?.label ?? '');
	let icon = $state(current?.icon ?? 'ti-cash');
	let needsChange = $state(current?.needs_change ?? false);
	let position = $state(String(current?.position ?? 0));
	let fee = $state(String(current?.fee_percent ?? 0));
	let note = $state(current?.note ?? '');
	const errors = new FieldErrors(
		{ outlet_id: termText.branch, code: termText.code, label: paymentMethodText.displayName, icon: paymentMethodText.icon, position: paymentMethodText.sortOrder, fee_percent: paymentMethodText.fee, note: termText.note },
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		const tidy = code.trim().toLowerCase();
		if (!current && !outletId) found.outlet_id = paymentMethodText.branchRequired;
		if (!current && !CODE_PATTERN.test(tidy)) found.code = paymentMethodText.codeInvalid;
		if (!label.trim()) found.label = paymentMethodText.displayNameRequired;
		const feeValue = Number(fee.replace(',', '.'));
		if (current && (!Number.isFinite(feeValue) || feeValue < 0 || feeValue > 100)) found.fee_percent = paymentMethodText.feeInvalid;
		if (!errors.check(found)) return;
		if (!current) return onsave({ code: tidy, label: label.trim(), icon, needs_change: needsChange }, outletId);
		onsave({
			label: label.trim(),
			icon,
			needs_change: needsChange,
			position: Math.max(0, Math.trunc(Number(position) || 0)),
			fee_percent: String(feeValue),
			note: note.trim()
		}, outletId);
	}
</script>

<FormPage title={method ? format(controlText.editName, { name: method.label }) : paymentMethodText.addMethod} description={method ? paymentMethodText.formDescription : paymentMethodText.imageAfterSave} stacked {trail} {busy} {onclose}>
	<FormSection icon="credit-card" title={termText.method} description={paymentMethodText.nameSectionDescription}>
		{#if !method}
			<BranchField bind:value={outletId} error={errors.get('outlet_id')} />
		{/if}
		<div class="grid gap-2 tablet:grid-cols-2">
			{#if method}
				<TextField label={termText.code} value={method.code} disabled hint={paymentMethodText.codeLockedHint} />
			{:else}
				<TextField label={termText.code} bind:value={code} maxlength={16} required hint={paymentMethodText.codeFormatHint} error={errors.get('code')} />
			{/if}
			<TextField label={paymentMethodText.displayName} bind:value={label} maxlength={40} required error={errors.get('label')} />
			<SelectField label={paymentMethodText.icon} bind:value={icon} options={PAYMENT_ICONS} error={errors.get('icon')} />
			{#if method}
				<TextField label={paymentMethodText.sortOrder} type="number" inputmode="numeric" bind:value={position} error={errors.get('position')} />
			{/if}
		</div>
		<CheckRow label={paymentMethodText.needsChange} hint={paymentMethodText.needsChangeHint} checked={needsChange} onchange={() => (needsChange = !needsChange)} />
	</FormSection>
	{#if method}
		<FormSection icon="percentage" title={paymentMethodText.feeAndNote} description={paymentMethodText.feeAndNoteDescription}>
			<TextField label={paymentMethodText.feePercent} type="text" inputmode="decimal" bind:value={fee} hint={paymentMethodText.feeHint} error={errors.get('fee_percent')} />
			<TextArea label={termText.note} bind:value={note} rows={3} maxlength={500} error={errors.get('note')} />
		</FormSection>
		<FormSection icon="photo" title={paymentMethodText.image} description={paymentMethodText.imageSectionDescription}>
			<PhotoField label={paymentMethodText.imageLabel} current={method.image_url} alt={format(paymentMethodText.imageOf, { name: method.label })} disabled={busy} onpick={onupload}>
				{#snippet actions()}
					{#if method.image_url}
						<DeleteButton label={paymentMethodText.removeImage} small disabled={busy} onclick={onremoveimage} />
					{/if}
				{/snippet}
			</PhotoField>
			{#if method.missing.length > 0}
				<Banner tone="warning" icon="alert-triangle">{format(paymentMethodText.missingFieldsHint, { fields: method.missing.join(' dan ') })}</Banner>
			{/if}
		</FormSection>
	{/if}
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
