import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { StationTask } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { STATION_TABLES } from '$lib/live/tables';
import { stationText } from '$lib/text/stations';

export type InterveneAction = 'start' | 'finish' | 'undo';

export class TaskState {
	readonly tables = STATION_TABLES;

	loading = $state(true);
	error = $state('');
	data = $state<StationTask | null>(null);
	action = $state<InterveneAction | null>(null);
	reason = $state('');
	saving = $state(false);
	saveError = $state('');

	constructor(readonly id: string) {}

	get canIntervene(): boolean {
		return access.allows('intervene_stations');
	}

	// Langkah yang masuk akal dari tahap sekarang; item batal, dihapus, atau terkunci tidak bisa diintervensi.
	get actions(): InterveneAction[] {
		const task = this.data;
		if (!task || task.removed || task.voided || task.locked) return [];
		if (task.stage === 'waiting') return task.arrived_at ? ['start'] : [];
		if (task.stage === 'started') return ['finish', 'undo'];
		return ['undo'];
	}

	async load(quiet = false): Promise<void> {
		if (!quiet) {
			this.loading = true;
			this.error = '';
		}
		try {
			this.data = await api.stations.task(this.id, {});
		} catch (error) {
			if (quiet) return;
			this.data = null;
			this.error = userMessage(error, stationText.itemLoadFailed);
		} finally {
			this.loading = false;
		}
	}

	choose(action: InterveneAction): void {
		this.action = action;
		this.saveError = '';
	}

	async submit(): Promise<void> {
		const task = this.data;
		const action = this.action;
		if (!task || !action || this.saving) return;
		if (!this.reason.trim()) {
			this.saveError = stationText.reasonRequired;
			return;
		}
		this.saving = true;
		this.saveError = '';
		try {
			this.data = await api.stations.intervene(task.task_id, { action, seen: task.stage, reason: this.reason.trim() }, {});
			this.action = null;
			this.reason = '';
		} catch (error) {
			this.saveError = userMessage(error, stationText.interventionSaveFailed);
			void this.load(true);
		} finally {
			this.saving = false;
		}
	}
}
