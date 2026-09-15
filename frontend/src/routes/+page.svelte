<script lang="ts">
	import { onMount } from 'svelte';
	import type { AuthUser, Note } from './types';

	const TOKEN_KEY = 'tablero.token';
	const USER_KEY = 'tablero.user';

	const COLUMNS: { status: Note['status']; label: string }[] = [
		{ status: 'PENDING', label: 'Pendiente' },
		{ status: 'IN_PROGRESS', label: 'En Progreso' },
		{ status: 'DONE', label: 'Hecha' }
	];

	let token = $state<string | null>(null);
	let user = $state<AuthUser | null>(null);
	let email = $state('');
	let password = $state('');
	let authError = $state<string | null>(null);
	let notes = $state<Note[]>([]);
	let loading = $state(false);
	let error = $state<string | null>(null);

	onMount(() => {
		token = localStorage.getItem(TOKEN_KEY);
		const rawUser = localStorage.getItem(USER_KEY);
		if (rawUser) user = JSON.parse(rawUser);
		if (token) void loadNotes();
	});

	function authHeaders(): Record<string, string> {
		return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
	}

	async function login(event: SubmitEvent) {
		event.preventDefault();
		authError = null;
		const res = await fetch('/api/auth/login/', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password })
		});
		if (!res.ok) {
			authError =
				res.status === 401
					? 'Credenciales inválidas o usuario inactivo.'
					: `Error ${res.status}`;
			return;
		}
		const data = await res.json();
		token = data.access;
		user = data.user;
		localStorage.setItem(TOKEN_KEY, data.access);
		localStorage.setItem(USER_KEY, JSON.stringify(data.user));
		password = '';
		await loadNotes();
	}

	async function logout() {
		if (token) {
			await fetch('/api/auth/logout/', { method: 'POST', headers: authHeaders() }).catch(
				() => undefined
			);
		}
		token = null;
		user = null;
		notes = [];
		localStorage.removeItem(TOKEN_KEY);
		localStorage.removeItem(USER_KEY);
	}

	async function loadNotes() {
		loading = true;
		error = null;
		const res = await fetch('/api/notes/', { headers: authHeaders() });
		loading = false;
		if (res.status === 401) {
			await logout();
			authError = 'La sesión expiró. Inicia sesión de nuevo.';
			return;
		}
		if (!res.ok) {
			error = `Error ${res.status}`;
			return;
		}
		const data = await res.json();
		notes = data.results ?? data;
	}
</script>

{#if !token}
	<div class="mx-auto mt-24 max-w-sm rounded-lg bg-white p-6 shadow">
		<h1 class="mb-4 text-lg font-semibold">Iniciar sesión</h1>
		<form class="flex flex-col gap-3" onsubmit={login}>
			<input
				class="rounded border border-slate-300 px-3 py-2"
				type="email"
				placeholder="Email"
				bind:value={email}
				required
			/>
			<input
				class="rounded border border-slate-300 px-3 py-2"
				type="password"
				placeholder="Contraseña"
				bind:value={password}
				required
			/>
			{#if authError}
				<p class="text-sm text-red-600">{authError}</p>
			{/if}
			<button
				class="rounded bg-slate-900 px-3 py-2 font-medium text-white hover:bg-slate-700"
				type="submit"
			>
				Entrar
			</button>
		</form>
		<p class="mt-4 text-xs text-slate-500">Demo: admin@ejemplo.com / Admin123!</p>
	</div>
{:else}
	<div class="flex items-center justify-between bg-white px-6 py-3 shadow">
		<span class="text-sm text-slate-600">
			{user?.name ?? user?.email} · rol {user?.role ?? '—'}
		</span>
		<div class="flex items-center gap-4">
			<button class="text-sm font-medium text-slate-600 hover:text-slate-900" onclick={loadNotes}>
				Recargar
			</button>
			<button class="text-sm font-medium text-red-600 hover:text-red-800" onclick={logout}>
				Cerrar sesión
			</button>
		</div>
	</div>

	<div class="grid grid-cols-3 gap-4 p-6">
		{#each COLUMNS as col (col.status)}
			<section class="rounded-lg bg-slate-200 p-3">
				<h2 class="mb-3 text-sm font-bold uppercase tracking-wide text-slate-600">
					{col.label}
				</h2>

				{#if loading}
					<p class="text-sm text-slate-500">Cargando…</p>
				{:else if error}
					<p class="text-sm text-red-600">Error al cargar: {error}</p>
				{:else}
					<div class="flex flex-col gap-2">
						{#each notes.filter((n) => n.status === col.status) as note (note.id)}
							<article class="rounded-md border border-slate-300 bg-amber-100 p-3 shadow-sm">
								<h3 class="font-medium">{note.title}</h3>
								{#if note.text}
									<p class="mt-1 text-sm text-slate-700">{note.text}</p>
								{/if}
								<p class="mt-2 text-xs text-slate-500">
									x: {note.pos_x} · y: {note.pos_y}
								</p>
							</article>
						{/each}
					</div>
				{/if}
			</section>
		{/each}
	</div>
{/if}
