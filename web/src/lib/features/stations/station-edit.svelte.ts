import { toast } from '$lib/components/feedback/toast.svelte';
import { userMessage } from '$lib/api/user-message';
import { goto } from '$app/navigation';
import { api } from '$lib/api';
import type { ManagedStation, Role, StationKind } from '$lib/api/types';
import { PAGES, stationPath } from '$lib/nav/pages';
import { durationOf, secondsOf, type Duration } from './target-detail.svelte';
import { stationText } from '$lib/text/stations';

export const NEW_STATION_ID = 'new';

/** Satu cabang di kartu Per cabang; aktif berarti ada tablet di cabang itu yang memegang stasiun ini, jadi hanya dibaca. */
export type BranchRow = { outletId: string; name: string; used: boolean; target: Duration; reminder: string; roleIds: string[] };

const REMINDER_MIN = 15;
const REMINDER_MAX = 600;

/** Jeda pengingat dalam detik: 0 mematikan pengingat, selain itu 15 detik sampai 10 menit. */
function reminderOf(text: string): { seconds: number; error: string } {
	const clean = text.trim();
	if (!/^\d+$/.test(clean)) return { seconds: 0, error: stationText.reminderNotNumber };
	const seconds = Number(clean);
	if (seconds !== 0 && (seconds < REMINDER_MIN || seconds > REMINDER_MAX)) return { seconds, error: stationText.reminderOutOfRange };
	return { seconds, error: '' };
}

export class StationEditState {
	loading = $state(true);
	error = $state('');
	station = $state<ManagedStation | null>(null);
	name = $state('');
	kind = $state<StationKind>('make');
	target = $state<Duration>({ hours: '', minutes: '' });
	/** Peran jadwal yang bisa dipilih sebagai pelaku; peran akses penuh tidak ikut. */
	roles = $state<Role[]>([]);
	/** Peran bawaan stasiun untuk semua cabang; cabang yang punya peran sendiri memakai miliknya. */
	defaultRoleIds = $state<string[]>([]);
	branches = $state<BranchRow[]>([]);
	branchError = $state('');
	saving = $state(false);
	saveError = $state('');
	confirmingDelete = $state(false);
	/** Cabang yang pengaturannya akan disalin ke cabang lain; terisi selama dialog konfirmasinya terbuka. */
	copyFrom = $state<BranchRow | null>(null);

	constructor(readonly id: string) {}

	get creating(): boolean {
		return this.id === NEW_STATION_ID;
	}

	get activeCount(): number {
		return this.branches.filter((branch) => branch.used).length;
	}

	async load(): Promise<void> {
		this.loading = true;
		this.error = '';
		try {
			if (!this.creating) {
				const setup = await api.stations.setup({});
				const found = setup.stations.find((station) => station.id === this.id) ?? null;
				if (!found) throw new Error(stationText.stationNotFound);
				this.station = found;
				this.name = found.name;
				this.kind = found.kind;
				this.target = durationOf(found.target_seconds);
				const [roles, defaults] = await Promise.all([api.roles.list(), api.stations.roles(this.id)]);
				this.roles = roles.filter((role) => !role.full_access);
				this.defaultRoleIds = [...defaults.role_ids];
				await this.loadBranches();
			}
		} catch (error) {
			this.error = userMessage(error, stationText.stationLoadFailed);
		} finally {
			this.loading = false;
		}
	}

	toggleRole(branch: BranchRow, roleId: string): void {
		branch.roleIds = branch.roleIds.includes(roleId) ? branch.roleIds.filter((id) => id !== roleId) : [...branch.roleIds, roleId];
	}

	toggleDefaultRole(roleId: string): void {
		this.defaultRoleIds = this.defaultRoleIds.includes(roleId) ? this.defaultRoleIds.filter((id) => id !== roleId) : [...this.defaultRoleIds, roleId];
	}

	async saveRoles(): Promise<void> {
		if (this.saving) return;
		await this.attempt(async () => {
			await api.stations.setRoles(this.id, this.defaultRoleIds);
			toast.show(stationText.defaultRolesSaved);
		});
	}

	private async loadBranches(): Promise<void> {
		const rows = await api.stations.branches(this.id);
		this.branches = rows.map((row) => ({
			outletId: row.outlet_id,
			name: row.outlet_name,
			used: row.used,
			target: durationOf(row.target_seconds),
			reminder: String(row.reminder_seconds),
			roleIds: [...row.role_ids]
		}));
	}

	async save(): Promise<void> {
		if (this.saving) return;
		const parsed = secondsOf(this.target);
		this.saveError = this.name.trim() ? parsed.error : stationText.nameRequired;
		if (this.saveError) return;
		const targetSeconds = this.kind === 'deliver' ? parsed.seconds : null;
		await this.attempt(async () => {
			if (this.creating) {
				const created = await api.stations.create({ name: this.name.trim(), kind: this.kind, target_seconds: targetSeconds });
				toast.show(stationText.stationSaved);
				await goto(stationPath(created.id));
				return;
			}
			await api.stations.update(this.id, { name: this.name.trim(), kind: this.kind, target_seconds: targetSeconds });
			toast.show(stationText.stationSaved);
		});
	}

	async saveBranches(): Promise<void> {
		if (this.saving || this.branches.length === 0) return;
		this.branchError = '';
		const parsed = this.branches.map((branch) => ({ branch, ...secondsOf(branch.target), reminder: reminderOf(branch.reminder) }));
		const wrong = parsed.find((entry) => entry.error || entry.reminder.error);
		if (wrong) {
			this.branchError = `${wrong.branch.name}: ${wrong.error || wrong.reminder.error}`;
			return;
		}
		await this.attempt(async () => {
			await api.stations.setBranches(this.id, {
				branches: parsed.map(({ branch, seconds, reminder }) => ({
					outlet_id: branch.outletId,
					target_seconds: this.kind === 'deliver' ? seconds : null,
					reminder_seconds: reminder.seconds,
					role_ids: branch.roleIds
				}))
			});
			toast.show(stationText.branchSettingsSaved);
		}, (message) => (this.branchError = message));
	}

	async copyToOthers(): Promise<void> {
		const from = this.copyFrom;
		if (!from || this.saving) return;
		const targets = this.branches.filter((branch) => branch.outletId !== from.outletId).map((branch) => branch.outletId);
		this.branchError = '';
		await this.attempt(
			async () => {
				await api.stations.copyBranches(this.id, { from_outlet_id: from.outletId, to_outlet_ids: targets });
				await this.loadBranches();
				toast.show(stationText.branchSettingsCopied);
			},
			(message) => (this.branchError = message)
		);
		this.copyFrom = null;
	}

	async remove(): Promise<void> {
		await this.attempt(async () => {
			await api.stations.remove(this.id);
			this.confirmingDelete = false;
			await goto(PAGES.stationSetup.path);
		});
	}

	private async attempt(work: () => Promise<void>, fail: (message: string) => void = (message) => (this.saveError = message)): Promise<void> {
		this.saving = true;
		this.saveError = '';
		try {
			await work();
		} catch (error) {
			fail(userMessage(error, stationText.changesSaveFailed));
		} finally {
			this.saving = false;
		}
	}
}
