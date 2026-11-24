import { del, inBranch, post, put, request, toQuery, type SortParam } from './http';
import type { Batch, BatchCopyResult, BatchInput, BatchPage, BatchRunDetail, BatchRunPage, BatchShiftCode, BatchUserPage, StoredRun } from './types';

const BASE = '/web/management/batches';
// Memperbaiki, membatalkan, dan menghapus pengisian memakai rute yang sama dengan aplikasi karyawan; server memeriksa izin pengelolanya.
const RUNS = '/v2/batches/runs';

/** Satu jawaban perbaikan: [file] foto baru, atau [keepPhoto] untuk mempertahankan foto yang sudah tersimpan. */
export type RunAnswerInput = { item_id: string; value: string | null; file: File | null; keepPhoto: boolean };

export type BatchRunParams = SortParam & {
	date_from?: string;
	date_to?: string;
	outlet_id?: string;
	kind?: string;
	q?: string;
	problems?: boolean;
	batch_id?: string;
	follow_up?: string;
	page?: number;
	size?: number;
};

export type BatchListParams = SortParam & {
	kind: string;
	q?: string;
	active?: boolean;
	repeat?: string;
	fill_mode?: string;
	outlet_id?: string;
	page?: number;
	size?: number;
};

export const batchesApi = {
	detail: (id: string): Promise<Batch> => request(`${BASE}/${id}`),
	list: (params: BatchListParams): Promise<BatchPage> => request(`${BASE}?${toQuery(params)}`),
	/** Kode shift satu cabang yang bisa dipasangi tugas rutin, tanpa kode libur. */
	shiftCodeOptions: async (outletId: string): Promise<BatchShiftCode[]> => (await request<{ items: BatchShiftCode[] }>(inBranch(`${BASE}/shift-code-options`, outletId))).items,
	create: (outletId: string, body: BatchInput): Promise<Batch> => post(inBranch(BASE, outletId), body),
	update: (id: string, body: BatchInput): Promise<Batch> => put(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	/** Karyawan aktif satu cabang yang bisa ditunjuk sebagai penerima tugas rutin; dicari dan dihalamankan di server. */
	userOptions: (params: { outlet_id: string; q?: string; page?: number; size?: number }): Promise<BatchUserPage> => request(`${BASE}/user-options?${toQuery(params)}`),
	/** Membuat satu salinan tugas per cabang tujuan; cabang yang dilewati dilaporkan beserta alasannya. */
	copy: (batchId: string, outletIds: string[]): Promise<BatchCopyResult> => post(`${BASE}/copies`, { batch_id: batchId, outlet_ids: outletIds }),
	/** Riwayat pengisian; tanpa tanggal server memakai bulan ini. */
	runs: (params: BatchRunParams): Promise<BatchRunPage> => request(`${BASE}/runs?${toQuery(params)}`),
	run: (id: string): Promise<BatchRunDetail> => request(`${BASE}/runs/${id}`),
	/** Templat dan jawaban tersimpan satu pengisian, sebagai isi awal form perbaikan. */
	storedRun: (id: string): Promise<StoredRun> => request(`${RUNS}/${id}`),
	/** Mengganti isi pengisian; isi lamanya disimpan server sebagai versi. */
	fixRun: (id: string, answers: RunAnswerInput[]): Promise<unknown> => {
		const files = answers.flatMap((answer) => (answer.file ? [answer.file] : []));
		const body = new FormData();
		body.append(
			'answers',
			JSON.stringify(answers.map((answer) => ({ item_id: answer.item_id, value: answer.value, photo_index: answer.file ? files.indexOf(answer.file) : null, keep_photo: answer.keepPhoto && !answer.file })))
		);
		for (const file of files) body.append('files', file);
		return request(`${RUNS}/${id}`, { method: 'PUT', body });
	},
	/** Tugas kembali belum diisi; isi lamanya tetap tercatat. */
	cancelRun: (id: string): Promise<void> => request(`${RUNS}/${id}/cancel`, { method: 'POST' }),
	/** Jawaban, foto, dan versi lamanya dibuang permanen; yang tersisa hanya catatan penghapusannya. */
	deleteRun: (id: string): Promise<void> => del(`${RUNS}/${id}`)
};
