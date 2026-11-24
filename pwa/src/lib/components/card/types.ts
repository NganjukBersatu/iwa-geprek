import type { Snippet } from 'svelte';

/** Warna latar kartu fitur; semuanya dari palet tema. */
export type CardTone = 'primary' | 'accent' | 'soft' | 'deep';

/** Satu baris kartu rincian: nilai berupa teks atau konten bebas (misalnya lencana). */
export type DetailListRow = { label: string; value?: string | null; valueContent?: Snippet };
