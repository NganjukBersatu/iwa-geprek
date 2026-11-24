export type BarTone = 'primary' | 'accent';

/** Satu bagian bilah: [weight] menentukan lebar relatif dan [progress] 0..1 mengisi dari kiri. */
export type BarSegment = { weight: number; progress: number; tone: BarTone };

/** Satu irisan donat: [value] menentukan lebarnya dan [color] dipakai juga oleh keterangannya. */
export type DonutSlice = { label: string; value: number; color: string };
