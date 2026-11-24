import { version } from '../../../../version.json';
import { RELEASE_NOTES } from './release-notes';

export type ReleaseNote = { icon: string; text: string };

export type Release = { version: string; notes: readonly ReleaseNote[] };

// Versi baru membuat ringkasan ini tampil sekali lagi untuk setiap akun; versi dan ringkasannya milik klien.
export const WEB_RELEASE: Release = { version, notes: RELEASE_NOTES };
