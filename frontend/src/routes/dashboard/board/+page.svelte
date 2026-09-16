<script lang="ts">
	import { onMount } from 'svelte';
	import PostIt from '$lib/components/PostIt.svelte';
	import { createNote, deleteNote, listNotes, updateNote } from '$lib/api/notes';
	import { ApiError } from '$lib/api/client';
	import type { Note, NoteStatus } from '$lib/types';

	let notes = $state<Note[]>([]);
	let loading = $state(true);
	let creating = $state(false);
	let error = $state<string | null>(null);

	onMount(load);

	async function load() {
		loading = true;
		error = null;
		try {
			notes = await listNotes();
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'No se pudieron cargar las notas.';
		} finally {
			loading = false;
		}
	}

	function replace(saved: Note) {
		notes = notes.map((n) => (n.id === saved.id ? saved : n));
	}

	async function handleMove(note: Note, x: number, y: number) {
		const saved = await updateNote(note.id, { pos_x: x, pos_y: y });
		replace(saved);
	}

	async function handleSave(
		note: Note,
		fields: { title: string; text: string; status: NoteStatus }
	) {
		const saved = await updateNote(note.id, fields);
		replace(saved);
	}

	async function handleDelete(note: Note) {
		await deleteNote(note.id);
		notes = notes.filter((n) => n.id !== note.id);
	}

	async function newNote() {
		creating = true;
		error = null;
		try {
			const offset = (notes.length * 28) % 420;
			const created = await createNote({
				title: 'Nueva nota',
				text: '',
				status: 'PENDING',
				pos_x: 24 + offset,
				pos_y: 24 + offset
			});
			notes = [...notes, created];
		} catch (e) {
			error = e instanceof ApiError ? e.message : 'No se pudo crear la nota.';
		} finally {
			creating = false;
		}
	}
</script>

<div class="p-6">
	<div class="mb-4 flex items-center justify-between">
		<h1 class="text-xl font-semibold">Tablero compartido</h1>
		<button
			type="button"
			class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50 disabled:opacity-50"
			disabled={loading}
			onclick={load}
		>
			{loading ? 'Cargando…' : 'Recargar'}
		</button>
	</div>

	{#if error}
		<p class="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
			{error}
		</p>
	{/if}

	<div
		class="relative min-h-[75vh] overflow-auto rounded-xl border border-slate-300 bg-slate-50 bg-[radial-gradient(circle,#cbd5e1_1px,transparent_1px)] [background-size:24px_24px]"
	>
		{#if loading}
			<p class="p-6 text-sm text-slate-500">Cargando notas…</p>
		{:else if notes.length === 0}
			<p class="p-6 text-sm text-slate-500">
				No hay notas todavía. Crea la primera con el botón «Nueva nota».
			</p>
		{/if}

		{#each notes as note (note.id)}
			<PostIt {note} onmove={handleMove} onsave={handleSave} ondelete={handleDelete} />
		{/each}
	</div>
</div>

<button
	type="button"
	class="fixed bottom-6 right-6 z-40 rounded-full bg-slate-900 px-5 py-3 font-medium text-white shadow-lg hover:bg-slate-700 disabled:opacity-50"
	disabled={creating}
	onclick={newNote}
>
	{creating ? 'Creando…' : '+ Nueva nota'}
</button>
