import { derived, get, writable } from 'svelte/store';
import type { AuthUser } from '$lib/types';

const TOKEN_KEY = 'tablero.token';
const USER_KEY = 'tablero.user';

function readStorage(key: string): string | null {
	if (typeof sessionStorage === 'undefined') return null;
	return sessionStorage.getItem(key);
}

function readUser(): AuthUser | null {
	const raw = readStorage(USER_KEY);
	if (!raw) return null;
	try {
		return JSON.parse(raw) as AuthUser;
	} catch {
		return null;
	}
}

/** Token en memoria (espejo de sessionStorage). */
export const accessToken = writable<string | null>(readStorage(TOKEN_KEY));
export const currentUser = writable<AuthUser | null>(readUser());
export const isAuthenticated = derived(accessToken, ($token) => Boolean($token));
export const isAdmin = derived(currentUser, ($user) => $user?.role === 'ADMIN');

export function setSession(token: string, user: AuthUser): void {
	accessToken.set(token);
	currentUser.set(user);
	sessionStorage.setItem(TOKEN_KEY, token);
	sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
	accessToken.set(null);
	currentUser.set(null);
	sessionStorage.removeItem(TOKEN_KEY);
	sessionStorage.removeItem(USER_KEY);
}

export function getToken(): string | null {
	return get(accessToken);
}
