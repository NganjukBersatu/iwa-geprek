<script lang="ts">
	import TextButton from '$lib/components/button/TextButton.svelte';
	import type { Role, RoleCreate, RoleStation, RoleUpdate } from '$lib/api/types';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { roleText } from '$lib/text/roles';
	import { PAGES, rolePath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import type { PermissionGroup } from '../roles.svelte';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';

	let {
		role,
		groups,
		stations,
		total,
		busy,
		error,
		fieldErrors = {},
		defaultKeys,
		canMarkProtected,
		onsave,
		onclose
	}: {
		role: Role | null;
		groups: PermissionGroup[];
		stations: RoleStation[];
		total: number;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		defaultKeys: string[];
		canMarkProtected: boolean;
		onsave: (body: RoleCreate | RoleUpdate) => void;
		onclose: () => void;
	} = $props();

	const initial = untrack(() => ({ role, keys: role ? role.permissions : defaultKeys }));
	const trail = [
		{ label: PAGES.roles.label, href: PAGES.roles.path },
		...(initial.role ? [{ label: initial.role.name, href: rolePath(initial.role.id) }, { label: actionText.edit }] : [{ label: roleText.addRole }])
	];
	const locked = initial.role?.full_access ?? false;
	const readonly = initial.role?.locked ?? false;
	let guarded = $state(initial.role?.is_protected ?? false);
	let name = $state(initial.role?.name ?? '');
	let description = $state(initial.role?.description ?? '');
	let station = $state(initial.role?.station_id ?? '');
	const chosen = new SvelteSet<string>(initial.keys);
	const errors = new FieldErrors({ name: roleText.roleName, station_id: roleText.tabletStation }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const allIn = (keys: string[]) => keys.every((key) => chosen.has(key));

	function toggle(key: string): void {
		if (chosen.has(key)) chosen.delete(key);
		else chosen.add(key);
	}

	function toggleGroup(keys: string[]): void {
		const everything = allIn(keys);
		for (const key of keys) {
			if (everything) chosen.delete(key);
			else chosen.add(key);
		}
	}

	function submit(): void {
		const found: Record<string, string> = {};
		if (!name.trim()) found.name = roleText.nameRequired;
		if (!errors.check(found)) return;
		const body = { name: name.trim(), description: description.trim() || (initial.role ? '' : null), station_id: station || null };
		const marked = canMarkProtected ? { ...body, is_protected: guarded } : body;
		onsave(locked ? marked : { ...marked, permissions: [...chosen] });
	}
</script>

<FormPage title={role ? (locked ? format(roleText.roleTitle, { name: role.name }) : format(roleText.arrangeRoleTitle, { name: role.name })) : roleText.addRole} description={roleText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="id-badge-2" title={roleText.role} description={roleText.roleSectionDescription}>
		{#if locked}
			<Banner tone="info" icon="info-circle">{roleText.fullAccessBanner}</Banner>
		{/if}
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={roleText.roleName} bind:value={name} placeholder={roleText.roleNameExample} maxlength={100} required disabled={readonly} error={errors.get('name')} />
			<TextField label={roleText.descriptionOptional} bind:value={description} placeholder={roleText.descriptionExample} maxlength={255} disabled={readonly} />
		</div>
		<SelectField
			label={roleText.tabletStation}
			bind:value={station}
			options={stations.map((item) => ({ value: item.id, label: item.name }))}
			empty={roleText.noStation}
			hint={roleText.tabletStationHint}
			disabled={readonly}
			error={errors.get('station_id')}
		/>
		{#if canMarkProtected}
			<CheckRow label={roleText.protectedRole} hint={roleText.protectedHint} checked={guarded} onchange={() => (guarded = !guarded)} />
			{#if guarded && !initial.role?.is_protected}
				<Banner tone="warning" icon="lock">{roleText.protectedWarning}</Banner>
			{/if}
		{/if}
	</FormSection>
	<FormSection icon="shield-check" title={roleText.permissions} description={locked ? roleText.fullAccessSummary : format(roleText.paidOfDue, { paid: chosen.size, due: total })}>
		{#each groups as group (group.name)}
			{@const groupKeys = group.sections.flatMap((section) => section.items.map((item) => item.key))}
			<section class="rounded-lg border border-slate-200 p-3 tablet:p-4">
				<div class="flex items-center justify-between gap-2">
					<h3 class="text-sm font-semibold text-slate-800">{group.name}</h3>
					{#if !locked && !readonly}
						<span class="text-xs"><TextButton label={allIn(groupKeys) ? roleText.clearAll : roleText.selectAll} onclick={() => toggleGroup(groupKeys)} /></span>
					{/if}
				</div>
				<div class="mt-2 flex flex-col gap-3">
					{#each group.sections as section (section.name)}
						{@const keys = section.items.map((item) => item.key)}
						<div>
							<div class="flex items-center justify-between gap-2 border-b border-slate-100 pb-1">
								<h4 class="text-xs font-semibold text-slate-500">{section.name}</h4>
								{#if !locked && !readonly}
									<span class="text-xs"><TextButton label={allIn(keys) ? roleText.clearSection : roleText.selectSection} onclick={() => toggleGroup(keys)} /></span>
								{/if}
							</div>
							<div class="mt-1 grid gap-1 tablet:grid-cols-2">
								{#each section.items as permission (permission.key)}
									<CheckRow label={permission.label} hint={permission.description} checked={locked || chosen.has(permission.key)} disabled={locked || readonly} onchange={() => toggle(permission.key)} />
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</section>
		{/each}
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-3"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		{#if !readonly}
			<SaveButton busy={busy} onclick={submit} />
		{/if}
		<Button label={locked || readonly ? actionText.close : actionText.cancel} variant="secondary" disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
