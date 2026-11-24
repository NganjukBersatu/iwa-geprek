<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Permission, Role, RoleStation, RoleUpdate } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import { roleText } from '$lib/text/roles';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { groupPermissions, type PermissionGroup } from '../roles.svelte';
	import RoleForm from './RoleForm.svelte';
	import { termText } from '$lib/text/terms';
	import RichText from '$lib/components/text/RichText.svelte';
	import { format } from '$lib/text/format';

	type RoleContext = { roles: Role[]; permissions: Permission[]; stations: RoleStation[] };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Role, RoleUpdate, RoleContext>(untrack(() => id), {
		load: (roleId) => api.roles.detail(roleId),
		context: async () => {
			const [roles, permissions, stations] = await Promise.all([api.roles.list(), api.roles.permissions(), api.roles.stations()]);
			return { roles, permissions, stations };
		},
		update: (role, body) => api.roles.update(role.id, body),
		remove: (role) => api.roles.remove(role.id),
		name: (role) => role.name,
		text: { ...recordText('peran', PAGES.roles.label), locked: roleText.lockedReason }
	});

	const granted = (role: Role, permissions: Permission[]) => (role.full_access ? permissions : permissions.filter((permission) => role.permissions.includes(permission.key)));
	const countOf = (group: PermissionGroup) => group.sections.reduce((sum, section) => sum + section.items.length, 0);
	const stationName = (role: Role, stations: RoleStation[]) => stations.find((station) => station.id === role.station_id)?.name ?? EMPTY_VALUE;
</script>

<RecordDetailView
	{detail}
	back={PAGES.roles}
	trail={(role) => [{ label: PAGES.roles.label, href: PAGES.roles.path }, { label: role.name }]}
	tables={['roles', 'stations']}
	title={(role) => role.name}
	description={(role) => role.description ?? ''}
	editable={(role) => !role.locked}
	removable={(role) => !role.is_default && !role.full_access && !role.is_protected && !role.locked}
>
	{#snippet badge(role)}
		{#if role.full_access}<Badge tone="brand">{roleText.allPermissions}</Badge>{:else if role.is_default}<Badge>{roleText.defaultBadge}</Badge>{/if}
		{#if role.is_protected}<Badge tone="warning"><i class="ti ti-lock" aria-hidden="true"></i>{roleText.protected}</Badge>{/if}
	{/snippet}
	{#snippet body(role, context)}
		{@const permissions = context?.permissions ?? []}
		{@const shown = groupPermissions(granted(role, permissions))}
		{#if role.locked}
			<Banner tone="info" icon="lock">{roleText.lockedBanner}</Banner>
		{:else if role.is_protected}
			<Banner tone="info" icon="lock">{roleText.protectedNote}</Banner>
		{:else if role.is_default || role.full_access}
			<Banner tone="info" icon="lock">{roleText.notRemovableNote}</Banner>
		{/if}
		<Card flush class="grid laptop:grid-cols-[18rem_minmax(0,1fr)]">
			<div class="border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<FigureList
					title={termText.summary}
					figures={[
						{ label: roleText.permissionCount, value: role.full_access ? format(roleText.permissionCountAll, { total: permissions.length }) : format(roleText.permissionCountPartial, { count: role.permissions.length, total: permissions.length }) },
						{ label: termText.station, value: stationName(role, context?.stations ?? []) },
						{ label: roleText.sortOrder, value: String(role.sort_order) },
						{ label: roleText.protected, value: role.is_protected ? termText.yes : termText.no }
					]}
				/>
			</div>
			<div class="flex min-w-0 flex-col p-4 tablet:p-5">
				<h2 class="text-sm font-semibold text-slate-800">{roleText.heldPermissions}</h2>
				<p class="mt-1 text-xs text-slate-500">
					{role.full_access ? roleText.fullAccessGroupHint : roleText.groupToggleHint}
				</p>
				{#if shown.length === 0}
					<p class="mt-3 text-xs text-slate-600">{roleText.noPermissions}</p>
				{:else}
					<div class="mt-3 flex flex-col gap-2">
						{#each shown as group (group.name)}
							<details class="group rounded-lg border border-slate-200" open={!role.full_access}>
								<summary class="flex cursor-pointer list-none items-center justify-between gap-3 rounded-lg px-3 py-2.5 hover:bg-brand-soft">
									<span class="text-sm font-semibold text-slate-800">{group.name}</span>
									<span class="flex items-center gap-2 text-xs text-slate-500">
										{format(roleText.permissionsCount, { count: countOf(group) })}
										<i class="ti ti-chevron-down transition-transform group-open:rotate-180" aria-hidden="true"></i>
									</span>
								</summary>
								<div class="flex flex-col gap-3 border-t border-slate-100 px-3 py-3">
									{#each group.sections as section (section.name)}
										<section class="flex flex-col gap-1.5">
											<h3 class="text-xs font-semibold text-brand-deep">{section.name}</h3>
											<ul class="grid gap-x-4 gap-y-1 text-xs text-slate-700 tablet:grid-cols-2 laptop:grid-cols-3">
												{#each section.items as item (item.key)}
													<li class="flex items-start gap-1.5">
														<i class="ti ti-check mt-px shrink-0 text-brand" aria-hidden="true"></i>
														<span>{item.label}</span>
													</li>
												{/each}
											</ul>
										</section>
									{/each}
								</div>
							</details>
						{/each}
					</div>
				{/if}
			</div>
		</Card>
	{/snippet}
	{#snippet form(props)}
		{@const permissions = props.context?.permissions ?? []}
		<RoleForm
			role={props.record}
			groups={groupPermissions(permissions)}
			stations={props.context?.stations ?? []}
			total={permissions.length}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			defaultKeys={permissions.filter((permission) => permission.default_for_new_role).map((permission) => permission.key)}
			canMarkProtected={(props.context?.roles ?? []).some((role) => role.is_protected && role.held_by_viewer)}
			onsave={(body) => props.onsave(body as RoleUpdate)}
			onclose={props.onclose}
		/>
	{/snippet}
	{#snippet removeNote(role)}
		<RichText template={roleText.roleRemoveNote} values={{ name: role.name }} />
	{/snippet}
</RecordDetailView>
