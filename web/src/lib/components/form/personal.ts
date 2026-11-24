import { controlText } from '$lib/text/controls';
/** The personal details every account keeps, as the form edits them: all text, empty meaning not filled in. */
export type PersonalData = {
	phone: string;
	email: string;
	birthDate: string;
	gender: string;
	address: string;
	emergencyName: string;
	emergencyPhone: string;
	emergencyRelation: string;
};

type PersonalSource = {
	phone: string | null;
	email: string | null;
	birth_date: string | null;
	gender: string | null;
	address: string | null;
	emergency_name: string | null;
	emergency_phone: string | null;
	emergency_relation: string | null;
};

export function personalFrom(source: PersonalSource | null): PersonalData {
	return {
		phone: source?.phone ?? '',
		email: source?.email ?? '',
		birthDate: source?.birth_date ?? '',
		gender: source?.gender ?? '',
		address: source?.address ?? '',
		emergencyName: source?.emergency_name ?? '',
		emergencyPhone: source?.emergency_phone ?? '',
		emergencyRelation: source?.emergency_relation ?? ''
	};
}

const blank = (text: string) => text.trim() || null;

/** What the server receives: an empty field is sent as null, which clears it. */
export function personalBody(data: PersonalData) {
	return {
		phone: blank(data.phone),
		email: blank(data.email),
		birth_date: blank(data.birthDate),
		gender: blank(data.gender),
		address: blank(data.address),
		emergency_name: blank(data.emergencyName),
		emergency_phone: blank(data.emergencyPhone),
		emergency_relation: blank(data.emergencyRelation)
	};
}

/** The personal fields by the name the server knows them by, in the order they stand on the form: what a summary of refused fields calls each one. */
export const PERSONAL_LABELS = {
	phone: controlText.phoneNumber,
	email: controlText.email,
	birth_date: controlText.birthDate,
	gender: controlText.gender,
	address: controlText.address,
	emergency_name: controlText.emergencyName,
	emergency_phone: controlText.emergencyPhone,
	emergency_relation: controlText.emergencyRelation
} as const;
