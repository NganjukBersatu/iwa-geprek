<script lang="ts">
	import { MIN_PASSWORD_LENGTH } from '$lib/auth/password-rules';
	import { controlText } from '$lib/text/controls';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import type { Employee, EmployeeCreate, EmployeeUpdate, Role } from '$lib/api/types';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import PersonalFields from '$lib/components/form/PersonalFields.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { PERSONAL_LABELS, personalBody, personalFrom } from '$lib/components/form/personal';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import { PAGES, employeePath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { employeeText } from '$lib/text/employees';
	import { format } from '$lib/text/format';

	let {
		employee,
		roles,
		outlets,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		employee: Employee | null;
		roles: Role[];
		outlets: { id: string; name: string }[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: EmployeeCreate | EmployeeUpdate) => void;
		onclose: () => void;
	} = $props();

	const initial = untrack(() => ({ employee, firstRole: roles[0]?.id ?? '', soleOutlet: outlets.length === 1 ? (outlets[0]?.id ?? '') : '' }));
	const current = initial.employee;
	const trail = [
		{ label: PAGES.user.label, href: PAGES.user.path },
		...(current ? [{ label: current.name || current.username, href: employeePath(current.id) }, { label: actionText.edit }] : [{ label: employeeText.addEmployee }])
	];
	let name = $state(current?.name ?? '');
	let username = $state(current?.username ?? '');
	let password = $state('');
	let joined = $state(current?.joined_date ?? '');
	let personal = $state(personalFrom(current));
	let roleId = $state(current?.role_id ?? initial.firstRole);
	let outletId = $state(current?.outlet_id ?? initial.soleOutlet);
	let active = $state(current?.is_active ?? true);
	const role = $derived(roles.find((item) => item.id === roleId));
	const blank = (text: string) => text.trim() || null;

	const errors = new FieldErrors(
		{ name: termText.name, username: employeeText.username, password: employeeText.password, ...PERSONAL_LABELS, role_id: termText.role, outlet_id: termText.branch, joined_date: employeeText.joinedDate },
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		if (!name.trim()) found.name = employeeText.nameRequired;
		if (!username.trim()) found.username = employeeText.usernameRequired;
		if (!current && !password.trim()) found.password = employeeText.passwordRequired;
		else if (password.trim() && password.trim().length < MIN_PASSWORD_LENGTH) found.password = format(employeeText.passwordMinimum, { count: MIN_PASSWORD_LENGTH });
		if (!errors.check(found)) return;
		const body = {
			name: name.trim(),
			username: username.trim(),
			role_id: roleId,
			outlet_id: role?.full_access ? null : blank(outletId),
			joined_date: blank(joined),
			...personalBody(personal)
		};
		const withPassword = password.trim() ? { ...body, password: password.trim() } : body;
		onsave(current ? { ...withPassword, is_active: active } : (withPassword as EmployeeCreate));
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.name || current.username }) : employeeText.addEmployee} description={employeeText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="user-circle" title={termText.account} description={employeeText.accountDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={termText.name} bind:value={name} maxlength={255} required error={errors.get('name')} />
			<TextField label={employeeText.username} bind:value={username} maxlength={100} autocomplete="off" required error={errors.get('username')} />
			<TextField label={current ? employeeText.passwordKeep : employeeText.password} type="password" bind:value={password} autocomplete="new-password" required={!current} hint={format(employeeText.passwordHint, { count: MIN_PASSWORD_LENGTH })} error={errors.get('password')} />
		</div>
	</FormSection>
	<FormSection icon="id" title={employeeText.personalData} description={employeeText.personalDataDescription}>
		<PersonalFields bind:data={personal} error={(field) => errors.get(field)} />
	</FormSection>
	<FormSection icon="building-store" title={employeeText.placement} description={employeeText.placementDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<SelectField label={termText.role} bind:value={roleId} options={roles.map((item) => ({ value: item.id, label: item.name }))} hint={role?.description ?? undefined} error={errors.get('role_id')} />
			{#if role?.full_access}
				<p class="self-center text-xs text-slate-500">{employeeText.crossBranchRole}</p>
			{:else}
				<SelectField label={termText.branch} bind:value={outletId} empty={employeeText.chooseBranch} options={outlets.map((item) => ({ value: item.id, label: item.name }))} hint={employeeText.branchHint} error={errors.get('outlet_id')} />
			{/if}
			<TextField label={employeeText.joinedDate} type="date" bind:value={joined} error={errors.get('joined_date')} />
		</div>
		{#if current}
			<CheckRow
				label={employeeText.accountActive}
				hint={active ? undefined : employeeText.accountActiveHint}
				checked={active}
				onchange={() => (active = !active)}
			/>
		{/if}
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
