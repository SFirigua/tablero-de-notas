import { goto } from '$app/navigation';
import { clearSession, getToken } from '$lib/stores/auth';

export class ApiError extends Error {
	constructor(
		public readonly status: number,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

interface FetchOptions {
	/** Evita el redirect a /login en 401 (p. ej. login/logout). */
	skipAuthRedirect?: boolean;
}

async function extractMessage(response: Response): Promise<string> {
	try {
		const data = await response.json();
		if (typeof data === 'string') return data;
		if (Array.isArray(data)) return data.join(' ');
		if (data && typeof data === 'object') {
			return Object.entries(data)
				.map(([key, value]) =>
					key === 'detail'
						? Array.isArray(value)
							? value.join(' ')
							: String(value)
						: `${key}: ${Array.isArray(value) ? value.join(' ') : String(value)}`
				)
				.join(' | ');
		}
	} catch {
		// el cuerpo no era JSON
	}
	return `Error HTTP ${response.status}`;
}

/**
 * Fetch wrapper de la API:
 * - adjunta `Authorization: Bearer <token>` si hay sesión;
 * - en HTTP 401 limpia la sesión y redirige a /login (usuario inactivo/token vencido);
 * - lanza ApiError con el mensaje de detalle del backend.
 */
export async function apiFetch<T>(
	url: string,
	init: RequestInit = {},
	options: FetchOptions = {}
): Promise<T> {
	const token = getToken();
	const headers = new Headers(init.headers);
	if (init.body && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}
	if (token) {
		headers.set('Authorization', `Bearer ${token}`);
	}

	const response = await fetch(url, { ...init, headers });

	if (response.status === 401 && !options.skipAuthRedirect) {
		clearSession();
		await goto('/login');
		throw new ApiError(401, 'Sesión expirada o usuario inactivo.');
	}
	if (!response.ok) {
		throw new ApiError(response.status, await extractMessage(response));
	}
	if (response.status === 204) {
		return undefined as T;
	}
	const text = await response.text();
	return (text ? JSON.parse(text) : undefined) as T;
}
