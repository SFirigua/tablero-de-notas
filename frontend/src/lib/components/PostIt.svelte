<script lang="ts">
	import { untrack } from 'svelte';
	import type { Note, NoteStatus } from '$lib/types';

	interface Props {
		note: Note;
		onmove: (note: Note, x: number, y: number) => Promise<void>;
		onsave: (
			note: Note,
			fields: { title: string; text: string; status: NoteStatus }
		) => Promise<void>;
		ondelete: (note: Note) => Promise<void>;
	}

	let { note, onmove, onsave, ondelete }: Props = $props();

	// Captura intencional de los valores iniciales: las ediciones locales no
	// deben pisarse cuando el padre reemplaza `note` tras persistir.
	let pos = $state(untrack(() => ({ x: note.pos_x, y: note.pos_y })));
	let title = $state(untrack(() => note.title));
	let text = $state(untrack(() => note.text));
	let status = $state<NoteStatus>(untrack(() => note.status));

	let dragging = $state(false);
	let busy = $state(false);
	let error = $state<string | null>(null);

	let grab = { x: 0, y: 0 };

	function pointerdown(event: PointerEvent) {
		if (busy) return;
		dragging = true;
		grab = { x: event.clientX - pos.x, y: event.clientY - pos.y };
		(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
	}

	function pointermove(event: PointerEvent) {
		if (!dragging) return;
		pos = { x: event.clientX - grab.x, y: event.clientY - grab.y };
	}

	async function pointerup(event: PointerEvent) {
		if (!dragging) return;
		dragging = false;
		(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);

		const x = Math.round(pos.x);
		const y = Math.round(pos.y);
		if (x === note.pos_x && y === note.pos_y) return;

		busy = true;
		error = null;
		try {
			await onmove(note, x, y);
		} catch {
			error = 'No se pudo guardar la posición.';
			pos = { x: note.pos_x, y: note.pos_y };
		} finally {
			busy = false;
		}
	}

	async function save() {
		busy = true;
		error = null;
		try {
			await onsave(note, { title, text, status });
		} catch (e) {
			error = e instanceof Error ? e.message : 'No se pudo guardar la nota.';
		} finally {
			busy = false;
		}
	}

	async function remove() {
		busy = true;
		error = null;
		try {
			await ondelete(note);
		} catch (e) {
			error = e instanceof Error ? e.message : 'No se pudo eliminar la nota.';
			busy = false;
		}
	}
</script>

<div
	class="anim-pop-in w-56 rounded-md border border-amber-300 bg-amber-100 shadow-lg {dragging
		? 'z-50 shadow-2xl'
		: 'z-10'}"
	style="position: absolute; left: {pos.x}px; top: {pos.y}px;"
>
	<button
		type="button"
		class="flex w-full cursor-grab items-center justify-center rounded-t-md border-b border-amber-300 bg-amber-200 py-1 text-xs text-amber-700 active:cursor-grabbing"
		style="touch-action: none;"
		aria-label="Arrastrar nota"
		onpointerdown={pointerdown}
		onpointermove={pointermove}
		onpointerup={pointerup}
	>
		⠿
	</button>

	<div class="flex flex-col gap-2 p-3">
		<input
			class="w-full rounded border border-amber-300 bg-amber-50 px-2 py-1 text-sm font-semibold"
			bind:value={title}
			aria-label="Título"
		/>
		<textarea
			class="h-20 w-full resize-none rounded border border-amber-300 bg-amber-50 px-2 py-1 text-sm"
			bind:value={text}
			aria-label="Texto"
		></textarea>
		<select
			class="w-full rounded border border-amber-300 bg-amber-50 px-2 py-1 text-sm"
			bind:value={status}
			aria-label="Estado"
		>
			<option value="PENDING">Pendiente</option>
			<option value="IN_PROGRESS">En curso</option>
			<option value="DONE">Hecho</option>
		</select>

		<div class="flex items-center justify-between gap-2">
			<button
				type="button"
				class="rounded bg-slate-800 px-2 py-1 text-xs font-medium text-white hover:bg-slate-600 disabled:opacity-50"
				disabled={busy}
				onclick={save}
			>
				Guardar
			</button>
			<button
				type="button"
				class="rounded border border-red-300 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
				disabled={busy}
				onclick={remove}
			>
				Eliminar
			</button>
		</div>

		{#if error}
			<p class="text-xs text-red-700">{error}</p>
		{/if}
	</div>
</div>
