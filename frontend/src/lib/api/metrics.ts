import { PUBLIC_METRICS_URL } from '$env/static/public';
import type { Metrics } from '$lib/types';
import { apiFetch } from './client';

/**
 * Métricas del dashboard.
 *
 * La URL sale SIEMPRE de `PUBLIC_METRICS_URL` (local: p. ej.
 * http://localhost:3001/metrics; AWS: <API_GATEWAY>/metrics); el código
 * nunca contiene URLs de infraestructura hardcodeadas.
 */
export function fetchMetrics(): Promise<Metrics> {
	return apiFetch<Metrics>(PUBLIC_METRICS_URL);
}

export function totalNotes(metrics: Metrics): number {
	return metrics.pending + metrics.in_progress + metrics.done;
}
