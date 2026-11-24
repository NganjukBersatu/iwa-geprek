import { current } from '$lib/auth/current.svelte';
import type { ApiResult } from '$lib/api/http';
import type { StringKey } from '$lib/text/strings';
import type { IconName } from '$lib/theme/icons';

export const TOGGLE_OK = 'ok';
export const TOGGLE_PROBLEM = 'problem';
const BATCHES = '/v2/batches';

/** Jenis isian satu item tugas outlet; nilainya sama dengan yang dipakai server. */
export type BatchItemKind = 'text' | 'number' | 'photo' | 'toggle';
export type BatchItem = { id: string; label: string; kind: BatchItemKind; required: boolean };

/** Tugas outlet berlaku untuk satu cabang; tugas rutin hanya untuk yang dijadwalkan di kode shiftnya. */
export type BatchKind = 'outlet' | 'routine';
/** [each] berarti tiap orang mengisi sendiri, sehingga [completed] adalah pengisian orang ini. */
export type BatchFillMode = 'one' | 'each';

/** Tugas rutin yang rentang waktunya ditentukan admin; [completed] berarti sudah diisi hari ini. */
export type Batch = { id: string; kind: BatchKind; fillMode: BatchFillMode; name: string; startClock: string; endClock: string; completed: boolean; items: BatchItem[]; runId: string | null; canFix: boolean; canCancel: boolean; canDelete: boolean };

/** Jawaban satu item; [value] untuk teks, angka, dan pilihan Oke atau Bermasalah, [photo] untuk foto; [keepPhoto] mempertahankan foto kiriman sebelumnya saat memperbaiki. */
export type BatchAnswer = { itemId: string; value: string | null; photo: Blob | null; keepPhoto?: boolean };

/** Jawaban yang sudah dikirim untuk satu item, sebagai isi awal form perbaikan. */
export type SentAnswer = { itemId: string; value: string | null; photoUrl: string | null };

type BatchResponse = { id: string; kind?: string; fill_mode?: string; name: string; start_clock: string; end_clock: string; completed?: boolean; run_id?: string | null; can_fix?: boolean; can_cancel?: boolean; can_delete?: boolean; items?: { id: string; label: string; kind: string; required?: boolean }[] };

const KINDS: BatchItemKind[] = ['text', 'number', 'photo', 'toggle'];

const batchOf = (dto: BatchResponse): Batch => ({
	id: dto.id,
	kind: dto.kind === 'routine' ? 'routine' : 'outlet',
	fillMode: dto.fill_mode === 'each' ? 'each' : 'one',
	name: dto.name,
	startClock: dto.start_clock,
	endClock: dto.end_clock,
	completed: dto.completed ?? false,
	runId: dto.run_id ?? null,
	canFix: dto.can_fix ?? false,
	canCancel: dto.can_cancel ?? false,
	canDelete: dto.can_delete ?? false,
	items: (dto.items ?? []).map((item) => ({ id: item.id, label: item.label, kind: KINDS.find((kind) => kind === item.kind) ?? 'text', required: item.required ?? true }))
});

export const rangeLabel = (batch: Batch): string => `${batch.startClock}–${batch.endClock}`;

/** Kata-kata kartu satu tugas rutin, sama dengan app Android. */
export function batchCardText(batch: Batch): { tag: StringKey; done: StringKey; icon: IconName; tone: 'green' | 'tan'; fill: StringKey | null } {
	if (batch.kind === 'outlet') return { tag: 'batch_tag', done: 'batch_done', icon: 'UsersGroup', tone: 'tan', fill: null };
	const each = batch.fillMode === 'each';
	return { tag: 'batch_routine_tag', done: each ? 'batch_each_done' : 'batch_routine_done', icon: 'CalendarCheck', tone: 'green', fill: each ? 'batch_fill_each' : 'batch_fill_one' };
}

/** Tugas outlet hari ini yang boleh dilihat orang ini, yaitu yang sudah absen dalam rentang waktunya. */
export async function todayBatches(): Promise<ApiResult<Batch[]>> {
	const result = await current.api().read<{ items?: BatchResponse[] }>(`${BATCHES}/today`);
	return result.kind === 'success' ? { kind: 'success', value: (result.value.items ?? []).map(batchOf) } : result;
}

/** Bentuk kiriman jawaban yang sama untuk mengisi dan memperbaiki; [photo_index] menunjuk urutan foto di antara berkas yang diunggah. */
function answersForm(answers: readonly BatchAnswer[]): FormData {
	const photos = answers.flatMap((answer) => (answer.photo ? [answer.photo] : []));
	const body = new FormData();
	body.append(
		'answers',
		JSON.stringify(
			answers.map((answer) => ({ item_id: answer.itemId, value: answer.value, photo_index: answer.photo ? photos.indexOf(answer.photo) : null, keep_photo: answer.keepPhoto === true && !answer.photo }))
		)
	);
	photos.forEach((photo) => body.append('files', photo, 'foto.jpg'));
	return body;
}

const settled = (result: ApiResult<unknown>): ApiResult<null> => (result.kind === 'success' ? { kind: 'success', value: null } : result);

/** Menyelesaikan satu tugas outlet atau rutin sekaligus; server menolak dengan keterangan bila ada item wajib yang kosong. */
export async function completeBatch(batchId: string, answers: readonly BatchAnswer[]): Promise<ApiResult<null>> {
	return settled(await current.api().write<unknown>('POST', `${BATCHES}/${batchId}/complete`, answersForm(answers)));
}

/** Jawaban yang sudah dikirim pada satu pengisian, untuk dibenahi pengirimnya. */
export async function sentAnswers(runId: string): Promise<ApiResult<SentAnswer[]>> {
	const result = await current.api().read<{ answers?: { item_id: string; value?: string | null; photo_url?: string | null }[] }>(`${BATCHES}/runs/${runId}`);
	if (result.kind !== 'success') return result;
	return { kind: 'success', value: (result.value.answers ?? []).map((answer) => ({ itemId: answer.item_id, value: answer.value ?? null, photoUrl: answer.photo_url ?? null })) };
}

/** Mengganti isi pengisian yang sudah dikirim; isi lamanya tetap tercatat di server. */
export async function fixRun(runId: string, answers: readonly BatchAnswer[]): Promise<ApiResult<null>> {
	return settled(await current.api().write<unknown>('PUT', `${BATCHES}/runs/${runId}`, answersForm(answers)));
}

/** Membatalkan pengisian: tugas kembali belum diisi, isi lamanya tetap tercatat. */
export async function cancelRun(runId: string): Promise<ApiResult<null>> {
	return settled(await current.api().write<unknown>('POST', `${BATCHES}/runs/${runId}/cancel`));
}

/** Menghapus pengisian secara permanen beserta foto dan riwayat perbaikannya. */
export async function deleteRun(runId: string): Promise<ApiResult<null>> {
	return settled(await current.api().write<unknown>('DELETE', `${BATCHES}/runs/${runId}`));
}
