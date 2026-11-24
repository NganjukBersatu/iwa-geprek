export const REGISTERED = 'terdaftar';

/** Isi QR pemasangan yang dipindai tablet; awalannya disepakati dengan aplikasi tablet. */
export const pairingQr = (code: string): string => `camera-pair:${code}`;
