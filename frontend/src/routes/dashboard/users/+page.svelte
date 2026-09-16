<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import Modal from '$lib/components/Modal.svelte';
	import { createUser, listUsers, updateUser } from '$lib/api/users';
	import { ApiError } from '$lib/api/client';
	import { currentUser, isAuthenticated } from '$lib/stores/auth';
	import type { ManagedUser, UserRole } from '$lib/types';

	let users = $state<ManagedUser[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let showCreate = $state(false);
	let creating = $state(false);
	let formError = $state<string | null>(null);
	let form = $state({ email: '', name: '', role: 'USER' as UserRole, password: '' });

	let showEdit = $state(false);
	let savingEdit = $state(false);
	let editError = $state<string | null>(null);
	let editing = $state<ManagedUser | null>(null);
	let editForm = $state({ email: '', name: '' });

	onMount(async () => {
		if (!get(isAuthenticated)) {
			await goto('/login');
			return;
		}
		if (get(currentUser)?.role !== 'ADMIN') {
			await goto('/dashboard');
			return;
		}
		await load();
	});

	async function load() {
		loading = true;
		error = null;
		try {
			users = await listUsers();
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'No se pudieron cargar los usuarios.';
		} finally {
			loading = false;
		}
	}

	function replace(id: number, saved: Partial<ManagedUser>) {
		users = users.map((u) => (u.id === id ? { ...u, ...saved, id: u.id } : u));
	}

	async function toggleActive(user: ManagedUser) {
		const next = !user.is_active;
		error = null;
		users = users.map((u) => (u.id === user.id ? { ...u, is_active: next } : u));
		try {
			const updated = await updateUser(user.id, { is_active: next });
			if (typeof updated?.is_active === 'boolean') {
				replace(user.id, { is_active: updated.is_active });
			}
		} catch (e) {
			users = users.map((u) => (u.id === user.id ? { ...u, is_active: user.is_active } : u));
			error = e instanceof ApiError ? e.message : 'No se pudo cambiar el estado.';
		}
	}

	async function changeRole(user: ManagedUser, role: UserRole) {
		if (role === user.role) return;
		error = null;
		try {
			replace(user.id, await updateUser(user.id, { role }));
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'No se pudo cambiar el rol.';
			await load();
		}
	}

	async function submitCreate(event: SubmitEvent) {
		event.preventDefault();
		formError = null;
		creating = true;
		try {
			await createUser(form);
			showCreate = false;
			form = { email: '', name: '', role: 'USER', password: '' };
			await load();
		} catch (e) {
			formError = e instanceof ApiError ? e.message : 'No se pudo crear el usuario.';
		} finally {
			creating = false;
		}
	}

	function openEdit(user: ManagedUser) {
		editing = user;
		editForm = { email: user.email, name: user.name };
		editError = null;
		showEdit = true;
	}

	async function submitEdit(event: SubmitEvent) {
		event.preventDefault();
		if (!editing) return;
		editError = null;
		savingEdit = true;
		try {
			// Reutiliza PATCH /api/users/<id>/ (misma lógica de negocio del backend).
			replace(
				editing.id,
				await updateUser(editing.id, { email: editForm.email, name: editForm.name })
			);
			showEdit = false;
		} catch (e) {
			editError = e instanceof ApiError ? e.message : 'No se pudo guardar el usuario.';
		} finally {
			savingEdit = false;
		}
	}
</script>

<div class="mx-auto max-w-5xl p-6">
	<div class="mb-5 flex items-center justify-between">
		<h1 class="text-xl font-semibold">Administración de usuarios</h1>
		<button
			type="button"
			class="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
			onclick={() => {
				formError = null;
				showCreate = true;
			}}
		>
			+ Nuevo usuario
		</button>
	</div>

	{#if error}
		<p class="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
			{error}
		</p>
	{/if}

	<div class="anim-fade-in overflow-hidden rounded-lg bg-white shadow">
		<table class="w-full text-left text-sm">
			<thead class="bg-slate-100 text-xs uppercase tracking-wide text-slate-500">
				<tr>
					<th class="px-4 py-3">Email</th>
					<th class="px-4 py-3">Nombre</th>
					<th class="px-4 py-3">Rol</th>
					<th class="px-4 py-3">Activo</th>
					<th class="px-4 py-3">Acciones</th>
				</tr>
			</thead>
			<tbody>
				{#if loading}
					<tr>
						<td class="px-4 py-4 text-slate-500" colspan="5">Cargando usuarios…</td>
					</tr>
				{:else}
					{#each users as user (user.id)}
						<tr class="border-t border-slate-100">
							<td class="px-4 py-3">{user.email}</td>
							<td class="px-4 py-3">{user.name}</td>
							<td class="px-4 py-3">
								<select
									class="rounded border border-slate-300 px-2 py-1"
									value={user.role}
									aria-label="Rol de {user.email}"
									onchange={(e) => changeRole(user, e.currentTarget.value as UserRole)}
								>
									<option value="ADMIN">ADMIN</option>
									<option value="USER">USER</option>
								</select>
							</td>
							<td class="px-4 py-3">
								<button
									type="button"
									role="switch"
									aria-checked={user.is_active}
									aria-label="Activo ({user.email})"
									class="relative h-6 w-11 rounded-full transition-colors {user.is_active
										? 'bg-emerald-500'
										: 'bg-slate-300'}"
									onclick={() => toggleActive(user)}
								>
									<span
										class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all {user.is_active
											? 'left-[22px]'
											: 'left-0.5'}"
									></span>
								</button>
							</td>
							<td class="px-4 py-3">
								<button
									type="button"
									class="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50"
									onclick={() => openEdit(user)}
								>
									Editar
								</button>
							</td>
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>
</div>

<Modal title="Nuevo usuario" open={showCreate} onclose={() => (showCreate = false)}>
	<form class="flex flex-col gap-3" onsubmit={submitCreate}>
		<input
			class="rounded border border-slate-300 px-3 py-2"
			type="email"
			placeholder="Email"
			bind:value={form.email}
			required
		/>
		<input
			class="rounded border border-slate-300 px-3 py-2"
			type="text"
			placeholder="Nombre"
			bind:value={form.name}
			required
		/>
		<select class="rounded border border-slate-300 px-3 py-2" bind:value={form.role}>
			<option value="USER">USER</option>
			<option value="ADMIN">ADMIN</option>
		</select>
		<input
			class="rounded border border-slate-300 px-3 py-2"
			type="password"
			placeholder="Contraseña inicial (mín. 8 caracteres)"
			bind:value={form.password}
			minlength={8}
			required
		/>
		{#if formError}
			<p class="text-sm text-red-600">{formError}</p>
		{/if}
		<div class="mt-2 flex justify-end gap-2">
			<button
				type="button"
				class="rounded border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
				onclick={() => (showCreate = false)}
			>
				Cancelar
			</button>
			<button
				type="submit"
				class="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
				disabled={creating}
			>
				{creating ? 'Creando…' : 'Crear usuario'}
			</button>
		</div>
	</form>
</Modal>

<Modal title="Editar usuario" open={showEdit} onclose={() => (showEdit = false)}>
	<form class="flex flex-col gap-3" onsubmit={submitEdit}>
		<input
			class="rounded border border-slate-300 px-3 py-2"
			type="email"
			placeholder="Email"
			bind:value={editForm.email}
			required
		/>
		<input
			class="rounded border border-slate-300 px-3 py-2"
			type="text"
			placeholder="Nombre"
			bind:value={editForm.name}
			required
		/>
		<p class="text-xs text-slate-500">
			El rol y el estado activo se gestionan directamente en la tabla.
		</p>
		{#if editError}
			<p class="text-sm text-red-600">{editError}</p>
		{/if}
		<div class="mt-2 flex justify-end gap-2">
			<button
				type="button"
				class="rounded border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
				onclick={() => (showEdit = false)}
			>
				Cancelar
			</button>
			<button
				type="submit"
				class="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
				disabled={savingEdit}
			>
				{savingEdit ? 'Guardando…' : 'Guardar cambios'}
			</button>
		</div>
	</form>
</Modal>
