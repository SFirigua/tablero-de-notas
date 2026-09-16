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

	function replace(saved: ManagedUser) {
		users = users.map((u) => (u.id === saved.id ? saved : u));
	}

	async function toggleActive(user: ManagedUser) {
		error = null;
		try {
			replace(await updateUser(user.id, { is_active: !user.is_active }));
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'No se pudo cambiar el estado.';
		}
	}

	async function changeRole(user: ManagedUser, role: UserRole) {
		if (role === user.role) return;
		error = null;
		try {
			replace(await updateUser(user.id, { role }));
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

	<div class="overflow-hidden rounded-lg bg-white shadow">
		<table class="w-full text-left text-sm">
			<thead class="bg-slate-100 text-xs uppercase tracking-wide text-slate-500">
				<tr>
					<th class="px-4 py-3">Email</th>
					<th class="px-4 py-3">Nombre</th>
					<th class="px-4 py-3">Rol</th>
					<th class="px-4 py-3">Activo</th>
				</tr>
			</thead>
			<tbody>
				{#if loading}
					<tr>
						<td class="px-4 py-4 text-slate-500" colspan="4">Cargando usuarios…</td>
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
