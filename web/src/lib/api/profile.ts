import { del, patch, post, request, upload } from './http';
import type { Profile, ProfileUpdate } from './types';

const BASE = '/v2/profile';

/** The signed-in person's own account; the server takes who it is from the token. */
export const profileApi = {
	read: (): Promise<Profile> => request(BASE),
	update: (body: ProfileUpdate): Promise<Profile> => patch(BASE, body),
	changePassword: (currentPassword: string, newPassword: string): Promise<void> => post(`${BASE}/password`, { current_password: currentPassword, new_password: newPassword }),
	uploadPhoto: (file: Blob): Promise<Profile> => upload(`${BASE}/photo`, 'file', file, 'PUT'),
	removePhoto: (): Promise<void> => del(`${BASE}/photo`)
};
