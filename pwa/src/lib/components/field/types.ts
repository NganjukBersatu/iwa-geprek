/** Satu pilihan dropdown; [key] null berarti "semua" atau "tanpa pilihan". */
export type DropdownOption = { key: string | null; label: string };

/** Tanggal dan jam waktu setempat (WIB); dikirim ke server lewat wibIso. */
export type DateTimeValue = { date: string; time: string };
