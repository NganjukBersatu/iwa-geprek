<script lang="ts">
	import DropdownField from '$lib/components/field/DropdownField.svelte';
	import type { DropdownOption } from '$lib/components/field/types';
	import ChoiceFlow from '$lib/components/choice/ChoiceFlow.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import ConfirmSheet from '$lib/components/sheet/ConfirmSheet.svelte';
	import FormSheet from '$lib/components/sheet/FormSheet.svelte';
	import { timeRange } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import type { SelfScheduleChoice, SelfScheduleState, ShiftSuggestion } from './selfschedule.svelte';

	/** Lembar absen mandiri sesuai langkahnya; tidak tampil bila tidak ada langkah yang terbuka. */
	let { state, onCreated }: { state: SelfScheduleState; onCreated: (scheduleId: string) => void } = $props();

	const options = $derived(state.options);
	const suggestions = $derived(state.outletId === null ? [] : (options?.suggestions ?? []));

	/** Pilihan pertama tanpa kunci menjadi ajakan memilih, karena isian ini belum punya nilai di awal. */
	const choices = (placeholder: string, items: readonly SelfScheduleChoice[]): DropdownOption[] => [{ key: null, label: placeholder }, ...items.map((item) => ({ key: item.id, label: item.name }))];

	function shiftLabel(suggestion: ShiftSuggestion): string {
		const start = suggestion.startsAt?.time;
		const end = suggestion.endsAt?.time;
		if (!start || !end) return suggestion.code;
		return t('self_schedule_shift_label', suggestion.code, timeRange(start, end));
	}
</script>

{#if state.step === 'intro'}
	<ConfirmSheet
		title={t('self_schedule_intro_title')}
		message={t('self_schedule_intro_message')}
		confirmLabel={t('self_schedule_intro_confirm')}
		onConfirm={() => state.openForm()}
		onDismiss={() => state.close()}
	/>
{:else if state.step === 'form'}
	<FormSheet
		title={t('self_schedule_title')}
		submitLabel={t('self_schedule_submit')}
		onSubmit={() => void state.submit(onCreated)}
		onDismiss={() => state.close()}
		submitting={state.submitting}
		canSubmit={state.canSubmit}
		error={state.error}
		loadingOnSubmit
	>
		<DropdownField
			label={t('self_schedule_outlet')}
			options={choices(t('self_schedule_outlet_pick'), options?.outlets ?? [])}
			selectedKey={state.outletId}
			onSelect={(key) => state.selectOutlet(key)}
		/>
		<DropdownField
			label={t('self_schedule_role')}
			options={choices(t('self_schedule_role_pick'), options?.roles ?? [])}
			selectedKey={state.roleId}
			onSelect={(key) => state.selectRole(key)}
		/>
		{#if state.outletId === null}
			<Notice text={t('self_schedule_shift_pick_outlet')} />
		{:else if state.loading}
			<!-- Daftar kode shift menunggu bacaan selesai. -->
		{:else if suggestions.length === 0}
			<Notice text={t('self_schedule_shift_empty')} />
		{:else}
			{@const selected = suggestions.findIndex((item) => item.shiftCodeId === state.shiftCodeId)}
			<ChoiceFlow
				label={t('self_schedule_shift')}
				options={suggestions.map(shiftLabel)}
				selectedIndex={selected >= 0 ? selected : null}
				onselect={(index) => {
					const picked = suggestions[index];
					if (picked) state.selectShift(picked.shiftCodeId);
				}}
			/>
		{/if}
		<TextField bind:value={state.reason} label={t('self_schedule_reason')} enabled={!state.submitting} />
	</FormSheet>
{/if}
