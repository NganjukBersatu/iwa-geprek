import { post, request } from './http';
import type { LoginResponse, User } from './types';

export const authApi = {
	// The server puts the token in a cookie the page cannot read; only the account comes back.
	login: (username: string, password: string): Promise<LoginResponse> => post('/v2/auth/session', { username, password }),
	logout: (): Promise<void> => request('/v2/auth/logout', { method: 'POST' }),
	me: (): Promise<User> => request('/v2/auth/me')
};
