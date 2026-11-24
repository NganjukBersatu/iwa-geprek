/** A recipe belongs to one menu at one branch, so its page address carries both, joined by a colon. */
export const recipeKey = {
	join: (menuId: string, outletId: string): string => `${menuId}:${outletId}`,
	split: (key: string): { menuId: string; outletId: string } => {
		const [menuId = '', outletId = ''] = key.split(':');
		return { menuId, outletId };
	}
};
