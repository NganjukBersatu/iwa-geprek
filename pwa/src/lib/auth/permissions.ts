/** The single place for permission keys in the PWA; values are frozen copies of the backend registry app/core/permissions and only shape what is shown. */
export const Permission = {
	OvertimeSelf: 'lembur.mandiri'
} as const;

export type Permission = (typeof Permission)[keyof typeof Permission];
