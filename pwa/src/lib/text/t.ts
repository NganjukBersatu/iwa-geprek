import { stringArrays, strings, type ArrayKey, type StringKey } from './strings';

/** Teks tampilan dari strings.xml app; `%1$s` dan `%1$d` diisi berurutan dari [args]. */
export function t(key: StringKey, ...args: (string | number)[]): string {
	return strings[key].replace(/%(\d+)\$[sd]/g, (_, index: string) => String(args[Number(index) - 1] ?? ''));
}

export function tArray(key: ArrayKey): readonly string[] {
	return stringArrays[key];
}
