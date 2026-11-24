<script lang="ts">
	import { employeeDetailText } from '$lib/text/employee-detail';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { todayIso } from '$lib/date/range';
	import type { PersonalData } from './personal';
	import { controlText } from '$lib/text/controls';

	let { data = $bindable(), error }: { data: PersonalData; /** What is wrong with a field, by the name the server knows it by. */ error?: (field: string) => string | undefined } = $props();
</script>

<div class="grid gap-2 tablet:grid-cols-2">
	<TextField label={controlText.phoneNumber} type="tel" inputmode="tel" bind:value={data.phone} maxlength={30} error={error?.('phone')} />
	<TextField label={controlText.email} type="email" inputmode="email" bind:value={data.email} maxlength={255} error={error?.('email')} />
	<TextField label={controlText.birthDate} type="date" max={todayIso()} bind:value={data.birthDate} error={error?.('birth_date')} />
	<SelectField label={controlText.gender} bind:value={data.gender} error={error?.('gender')} empty="—" options={[{ value: 'L', label: employeeDetailText.male }, { value: 'P', label: employeeDetailText.female }]} />
	<div class="tablet:col-span-2"><TextField label={controlText.address} bind:value={data.address} maxlength={500} error={error?.('address')} /></div>
	<TextField label={controlText.emergencyName} bind:value={data.emergencyName} maxlength={255} error={error?.('emergency_name')} />
	<TextField label={controlText.emergencyPhone} type="tel" inputmode="tel" bind:value={data.emergencyPhone} maxlength={30} error={error?.('emergency_phone')} />
	<TextField label={controlText.emergencyRelation} bind:value={data.emergencyRelation} maxlength={100} error={error?.('emergency_relation')} />
</div>
