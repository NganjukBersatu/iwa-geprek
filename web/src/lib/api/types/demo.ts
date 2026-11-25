/** Langkah penyiapan mode demo, urut seperti yang dijalankan server. */
export type DemoStage = 'idle' | 'preparing' | 'loading' | 'linking' | 'ready' | 'failed';

/**
 * Keadaan mode demo dari GET/POST /v2/demo.
 * shortcut: ditulis tangan karena skema backend demo belum dibangkitkan, ganti dengan Schemas['…'] begitu schema.d.ts memuatnya.
 */
export type DemoStatus = {
	available: boolean;
	active: boolean;
	stage: DemoStage;
	percent: number;
	error_code: string | null;
};
