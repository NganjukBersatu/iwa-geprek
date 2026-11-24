import type { UserRecap } from '$lib/api/types';

export const userName = (user: UserRecap) => user.name?.trim() || user.username;
