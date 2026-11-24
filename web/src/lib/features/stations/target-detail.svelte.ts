import { toast } from '$lib/components/feedback/toast.svelte';
import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { MenuTargetDetail } from '$lib/api/types';
import { STATION_TABLES } from '$lib/live/tables';
import { stationText } from '$lib/text/stations';

const SECONDS_PER_MINUTE = 60;
const MINUTES_PER_HOUR = 60;
const SECONDS_PER_HOUR = SECONDS_PER_MINUTE * MINUTES_PER_HOUR;
const MAX_SECONDS = 24 * SECONDS_PER_HOUR;

export type Duration = { hours: string; minutes: string };

export const durationOf = (seconds: number | null): Duration =>
	seconds === null ? { hours: '', minutes: '' } : { hours: String(Math.floor(seconds / SECONDS_PER_HOUR)), minutes: String(Math.floor((seconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE)) };

// Kosong di kedua isian berarti target dihapus; selain itu harus menghasilkan 1 menit sampai 24 jam.
export function secondsOf(duration: Duration): { seconds: number | null; error: string } {
	const hours = duration.hours.trim();
	const minutes = duration.minutes.trim();
	if (!hours && !minutes) return { seconds: null, error: '' };
	const hourValue = hours ? Number(hours) : 0;
	const minuteValue = minutes ? Number(minutes) : 0;
	if (!Number.isInteger(hourValue) || !Number.isInteger(minuteValue) || hourValue < 0 || minuteValue < 0 || minuteValue >= MINUTES_PER_HOUR) {
		return { seconds: null, error: stationText.targetFormatInvalid };
	}
	const seconds = (hourValue * MINUTES_PER_HOUR + minuteValue) * SECONDS_PER_MINUTE;
	if (seconds < SECONDS_PER_MINUTE || seconds > MAX_SECONDS) return { seconds: null, error: stationText.targetRangeInvalid };
	return { seconds, error: '' };
}

export class TargetDetailState {
	readonly tables = [...STATION_TABLES, 'menu_targets', 'menu_branch_targets'];

	loading = $state(true);
	error = $state('');
	data = $state<MenuTargetDetail | null>(null);
	fallback = $state<Duration>({ hours: '', minutes: '' });
	branchId = $state('');
	branch = $state<Duration>({ hours: '', minutes: '' });
	saving = $state(false);
	saveError = $state('');

	constructor(readonly menuId: string) {}

	async load(quiet = false): Promise<void> {
		if (!quiet) {
			this.loading = true;
			this.error = '';
		}
		try {
			const data = await api.stations.target(this.menuId, {});
			this.data = data;
			if (!quiet) this.fallback = durationOf(data.target_seconds);
			const first = data.branches.at(0);
			if (!this.branchId && first) this.pickBranch(first.outlet_id);
		} catch (error) {
			if (quiet) return;
			this.data = null;
			this.error = userMessage(error, stationText.targetLoadFailed);
		} finally {
			this.loading = false;
		}
	}

	pickBranch(outletId: string): void {
		this.branchId = outletId;
		const row = this.data?.branches.find((entry) => entry.outlet_id === outletId);
		this.branch = durationOf(row?.target_seconds ?? null);
	}

	saveFallback(): Promise<void> {
		return this.save(this.fallback, (seconds) => api.stations.setTarget(this.menuId, { target_seconds: seconds }), stationText.defaultTargetSaved);
	}

	saveBranch(): Promise<void> {
		return this.save(this.branch, (seconds) => api.stations.setBranchTarget(this.menuId, this.branchId, { target_seconds: seconds }), stationText.branchTargetSaved);
	}

	private async save(duration: Duration, write: (seconds: number | null) => Promise<void>, done: string): Promise<void> {
		if (this.saving) return;
		const parsed = secondsOf(duration);
		this.saveError = parsed.error;
		if (parsed.error) return;
		this.saving = true;
		try {
			await write(parsed.seconds);
			toast.show(done);
			await this.load(true);
		} catch (error) {
			this.saveError = userMessage(error, stationText.targetSaveFailed);
		} finally {
			this.saving = false;
		}
	}
}
