import type { Role } from '$lib/api/types';

export const assignableRoles = (roles: Role[]): Role[] => roles.filter((role) => role.assignable);
