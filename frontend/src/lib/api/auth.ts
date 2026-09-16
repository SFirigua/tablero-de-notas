import type { AuthUser } from '$lib/types';
import { apiFetch } from './client';

export interface LoginResponse {
	access: string;
	refresh: string;
	user: AuthUser;
}

export function login(email: string, password: string): Promise<LoginResponse> {
	return apiFetch<LoginResponse>(
		'/api/auth/login/',
		{ method: 'POST', body: JSON.stringify({ email, password }) },
		{ skipAuthRedirect: true }
	);
}

/** Logout: JWT sin estado -> el servidor solo confirma; el cliente borra los tokens. */
export function logout(): Promise<{ detail: string }> {
	return apiFetch<{ detail: string }>(
		'/api/auth/logout/',
		{ method: 'POST' },
		{ skipAuthRedirect: true }
	);
}
