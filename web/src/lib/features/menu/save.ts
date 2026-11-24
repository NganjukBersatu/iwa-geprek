import { api } from '$lib/api';
import type { MenuCreate, MenuItem, MenuUpdate } from '$lib/api/types';

/** The one way a new or changed menu is saved, with its photo when one was picked. */
export async function saveMenu(item: MenuItem | null, body: MenuCreate | MenuUpdate, photo: File | null): Promise<MenuItem> {
	const saved = item ? await api.menu.update(item.id, body as MenuUpdate) : await api.menu.create(body as MenuCreate);
	return photo ? api.menu.uploadPhoto(saved.id, photo) : saved;
}
