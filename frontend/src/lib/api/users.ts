import type { ManagedUser, UserRole } from '$lib/types';
import { apiFetch } from './client';

export interface CreateUserPayload {
	email: string;
	name: string;
	role: UserRole;
	password: string;
}

export type UpdateUserPayload = Partial<Pick<ManagedUser, 'email' | 'name' | 'role' | 'is_active'>>;

/** Solo ADMIN. La API pagina; se tolera `results` o array plano. */
export async function listUsers(): Promise<ManagedUser[]> {
	const data = await apiFetch<ManagedUser[] | { results: ManagedUser[] }>('/api/users/');
	return Array.isArray(data) ? data : data.results;
}

export function createUser(payload: CreateUserPayload): Promise<ManagedUser> {
	return apiFetch<ManagedUser>('/api/users/', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function updateUser(id: number, payload: UpdateUserPayload): Promise<ManagedUser> {
	return apiFetch<ManagedUser>(`/api/users/${id}/`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}
