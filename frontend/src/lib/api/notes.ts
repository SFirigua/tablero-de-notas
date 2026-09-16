import type { Note } from '$lib/types';
import { apiFetch } from './client';

export type NotePayload = Partial<Pick<Note, 'title' | 'text' | 'status' | 'pos_x' | 'pos_y'>>;

/** La API pagina (PAGE_SIZE=50); se tolera `results` o array plano. */
export async function listNotes(): Promise<Note[]> {
	const data = await apiFetch<Note[] | { results: Note[] }>('/api/notes/');
	return Array.isArray(data) ? data : data.results;
}

export function createNote(payload: NotePayload): Promise<Note> {
	return apiFetch<Note>('/api/notes/', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function updateNote(id: number, payload: NotePayload): Promise<Note> {
	return apiFetch<Note>(`/api/notes/${id}/`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteNote(id: number): Promise<void> {
	return apiFetch<void>(`/api/notes/${id}/`, { method: 'DELETE' });
}
