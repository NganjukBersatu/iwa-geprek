import type { Schemas } from '$lib/api/contract';
import { current } from '$lib/auth/current.svelte';
import { stamp, type WibStamp } from '$lib/format/datetime';

type NoticeKind = 'task-assigned' | 'task-overdue' | 'due-changed';

export type NoticeItem = { id: string; kind: NoticeKind; title: string; showAt: WibStamp | null };

const KIND_TASK_OVERDUE = 'task_overdue';
const KIND_DUE_CHANGED = 'due_changed';
const BASE = '/v2/notices';

function noticeOf(dto: Schemas['NoticeOut']): NoticeItem {
	return {
		id: dto.id,
		kind: dto.kind === KIND_TASK_OVERDUE ? 'task-overdue' : dto.kind === KIND_DUE_CHANGED ? 'due-changed' : 'task-assigned',
		title: dto.title,
		showAt: stamp(dto.show_at)
	};
}

/** Pengumuman yang perlu disampaikan setelah masuk. */
export class NoticesState {
	items = $state<NoticeItem[]>([]);

	/** Jawaban masuk tidak membawa pengumuman, jadi diminta ke server begitu sesi dipakai. */
	async load(onSessionExpired: () => void): Promise<void> {
		const result = await current.api().read<Schemas['NoticeOut'][]>(BASE);
		if (result.kind === 'unauthorized') onSessionExpired();
		else if (result.kind === 'success') this.items = result.value.map(noticeOf);
	}

	/** Lembar langsung tertutup; penandaan sudah dibaca berjalan di belakang dan gagalnya hanya membuat pengumuman muncul lagi nanti. */
	close(): void {
		const ids = this.items.map((item) => item.id);
		if (ids.length === 0) return;
		this.items = [];
		void current.api().write('POST', `${BASE}/read`, { ids });
	}
}
