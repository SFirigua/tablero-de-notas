export type NoteStatus = 'PENDING' | 'IN_PROGRESS' | 'DONE';

export interface Note {
	id: number;
	title: string;
	text: string;
	status: NoteStatus;
	pos_x: number;
	pos_y: number;
	created_at: string;
	updated_at: string;
}

export type UserRole = 'ADMIN' | 'USER';

export interface AuthUser {
	id: number;
	email: string;
	name: string;
	role: UserRole;
}

export interface ManagedUser extends AuthUser {
	is_active: boolean;
	is_staff: boolean;
}

export interface Metrics {
	pending: number;
	in_progress: number;
	done: number;
}
