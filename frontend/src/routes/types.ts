export interface Note {
	id: number;
	title: string;
	text: string;
	status: 'PENDING' | 'IN_PROGRESS' | 'DONE';
	pos_x: number;
	pos_y: number;
	created_at: string;
	updated_at: string;
}

export interface AuthUser {
	id: number;
	email: string;
	name: string;
	role: 'ADMIN' | 'USER';
}
