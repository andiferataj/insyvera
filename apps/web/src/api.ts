export type Json = Record<string, any>;
export async function api<T = any>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch('/api' + url, { credentials: 'same-origin', ...options,
    headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers } });
  if (!response.ok) {
    let error = await response.json().catch(() => ({ detail: response.statusText }));
    if (Array.isArray(error.detail)) error = {detail: error.detail.map((e: Json) => e.msg).join('. ')};
    throw new Error(error.detail || 'The request could not be completed.');
  }
  return response.json() as Promise<T>;
}
export function post<T = any>(url: string, body: unknown = {}) { return api<T>(url,{ method:'POST', body: JSON.stringify(body) }); }
export function money(value: unknown) { const n = Number(value); return Number.isFinite(n) ? new Intl.NumberFormat('en',{maximumFractionDigits:2}).format(n) : '—'; }
export function bytes(value: number) { return value >= 1024 * 1024 ? (value/1024/1024).toFixed(1)+' MB' : Math.max(1,Math.round(value/1024))+' KB'; }
export function relative(value: string) { const mins = Math.max(0, Math.floor((Date.now()-new Date(value.endsWith('Z') || value.includes('+') ? value : value+'Z').getTime())/60000)); return mins < 1 ? 'Just now' : mins < 60 ? mins+'m ago' : mins < 1440 ? Math.floor(mins/60)+'h ago' : Math.floor(mins/1440)+'d ago'; }
