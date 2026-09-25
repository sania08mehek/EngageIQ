export const f2 = (n: number) => n.toFixed(2);

/** Signed number with a real minus sign. Zero (after rounding) has no sign. */
export function signed(n: number, digits = 2): string {
  const r = Number(n.toFixed(digits));
  if (r === 0) return (0).toFixed(digits);
  return `${r > 0 ? '+' : '\u2212'}${Math.abs(r).toFixed(digits)}`;
}

export function num(n: number, decimals = 0): string {
  return n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function shortDate(iso: string): string {
  const d = iso.length === 10 ? new Date(`${iso}T00:00:00Z`) : new Date(iso);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
}

export function longDate(iso: string): string {
  const d = iso.length === 10 ? new Date(`${iso}T00:00:00Z`) : new Date(iso);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
}
