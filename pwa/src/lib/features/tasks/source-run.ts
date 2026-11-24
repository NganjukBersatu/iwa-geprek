import { current } from '$lib/auth/current.svelte';
import type { ApiResult } from '$lib/api/http';
import { stamp, type WibStamp } from '$lib/format/datetime';

/** Satu jawaban di pengisian asal; [value] kosong berarti isian opsional yang dilewati. */
export type SourceAnswer = { label: string; kind: string; value: string | null; photoUrl: string | null };

/** Pengisian tugas rutin atau outlet yang ditindaklanjuti sebuah tugas, lengkap dengan jawaban dan fotonya. */
export type SourceRun = { name: string; day: string; outletName: string; filler: string | null; doneAt: WibStamp | null; problems: number; answers: SourceAnswer[] };

type SourceRunResponse = {
	batch_name: string;
	day: string;
	outlet_name: string;
	completed_by?: string | null;
	completed_at?: string | null;
	problems?: number;
	answers?: { label: string; kind: string; value?: string | null; photo_url?: string | null }[];
};

export async function taskSourceRun(taskId: string): Promise<ApiResult<SourceRun>> {
	const result = await current.api().read<SourceRunResponse>(`/v2/tasks/${taskId}/source-run`);
	if (result.kind !== 'success') return result;
	const dto = result.value;
	return {
		kind: 'success',
		value: {
			name: dto.batch_name,
			day: dto.day,
			outletName: dto.outlet_name,
			filler: dto.completed_by ?? null,
			doneAt: stamp(dto.completed_at),
			problems: dto.problems ?? 0,
			answers: (dto.answers ?? []).map((answer) => ({ label: answer.label, kind: answer.kind, value: answer.value ?? null, photoUrl: answer.photo_url ?? null }))
		}
	};
}
