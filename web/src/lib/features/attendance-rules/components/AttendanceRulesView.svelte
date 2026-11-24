<script lang="ts">
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import type { AttendanceRulesState, RulesRow } from '../attendance-rules.svelte';
	import { attendanceRulesText } from '$lib/text/attendance-rules';
	import { format } from '$lib/text/format';

	let { rules }: { rules: AttendanceRulesState } = $props();


	const MAX_TOLERANCE = 180;
	const MAX_PENALTY = 1_000_000;
	const MIN_HOURS = 1;
	const MAX_HOURS = 72;

	let tolerance = $state('');
	let penalty = $state('');
	let hours = $state('');
	const errors = new FieldErrors(
		{ late_tolerance_minutes: attendanceRulesText.lateTolerance, late_penalty_per_minute: attendanceRulesText.deductionPerMinute, auto_close_after_hours: attendanceRulesText.autoClose },
		() => rules.fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(rules.fieldErrors).length > 0) void focusRefused();
	});

	// The fields follow the rules in force: a new branch, or a save, refills them.
	$effect(() => {
		const row: RulesRow | null = rules.rules;
		tolerance = row ? String(row.late_tolerance_minutes) : '';
		penalty = row ? String(row.late_penalty_per_minute) : '';
		hours = row ? String(row.auto_close_after_hours) : '';
	});

	const integer = (text: string) => (/^\d+$/.test(text.trim()) ? Number(text.trim()) : null);

	function submit(): void {
		const values = { late_tolerance_minutes: integer(tolerance), late_penalty_per_minute: integer(penalty), auto_close_after_hours: integer(hours) };
		const found: Record<string, string> = {};
		if (values.late_tolerance_minutes === null || values.late_tolerance_minutes > MAX_TOLERANCE) found.late_tolerance_minutes = format(attendanceRulesText.lateToleranceInvalid, { max: MAX_TOLERANCE });
		if (values.late_penalty_per_minute === null || values.late_penalty_per_minute > MAX_PENALTY) found.late_penalty_per_minute = attendanceRulesText.deductionInvalid;
		if (values.auto_close_after_hours === null || values.auto_close_after_hours < MIN_HOURS || values.auto_close_after_hours > MAX_HOURS) found.auto_close_after_hours = format(attendanceRulesText.autoCloseInvalid, { min: MIN_HOURS, max: MAX_HOURS });
		if (!errors.check(found)) return;
		void rules.save({ late_tolerance_minutes: values.late_tolerance_minutes as number, late_penalty_per_minute: values.late_penalty_per_minute as number, auto_close_after_hours: values.auto_close_after_hours as number });
	}

	const example = $derived.by(() => {
		const minutes = integer(tolerance);
		const rate = integer(penalty);
		if (minutes === null || rate === null) return '';
		return format(attendanceRulesText.deductionExample, { minutes: minutes + 10, amount: formatRupiah(10 * rate) });
	});
</script>

{#if rules.rules}
	<Card>
		<CardHeader title={attendanceRulesText.latenessRules} description={attendanceRulesText.latenessRulesDescription} />
		<div class="mt-4 grid gap-4 tablet:grid-cols-3">
			<TextField label={attendanceRulesText.lateToleranceMinutes} inputmode="numeric" bind:value={tolerance} hint={attendanceRulesText.lateToleranceHint} error={errors.get('late_tolerance_minutes')} />
			<MoneyField label={attendanceRulesText.deductionPerMinuteRupiah} bind:value={penalty} hint={attendanceRulesText.deductionHint} error={errors.get('late_penalty_per_minute')} />
			<TextField label={attendanceRulesText.autoCloseHours} inputmode="numeric" bind:value={hours} hint={attendanceRulesText.autoCloseHint} error={errors.get('auto_close_after_hours')} />
		</div>
		{#if example}<p class="mt-3 rounded-lg bg-brand-page px-3 py-2 text-xs text-slate-600">{example}</p>{/if}
		{#if rules.actionError && errors.count === 0}<div class="mt-3"><Banner tone="danger" icon="alert-triangle">{rules.actionError}</Banner></div>{/if}
		<div class="mt-4">
			<SaveButton label={attendanceRulesText.saveRules} icon="device-floppy" busy={rules.busy} onclick={submit} />
		</div>
	</Card>
{/if}
