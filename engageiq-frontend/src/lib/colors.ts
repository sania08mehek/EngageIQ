// Theme-aware color palettes. Charts and SVGs need real values, not CSS var().

export type ThemeMode = 'light' | 'dark';

export interface ThemePalette {
  paper: string;
  panel: string;
  wash: string;
  ink: string;
  muted: string;
  rule: string;
  ruleSoft: string;
  ehs: string;
  ehsWash: string;
  opi: string;
  opiWash: string;
  healthy: string;
  healthyWash: string;
  healthyText: string;
  moderate: string;
  moderateWash: string;
  moderateText: string;
  atRisk: string;
  atRiskWash: string;
  atRiskText: string;
  gridLine: string;
  tooltipBg: string;
  tooltipBorder: string;
}

export const LIGHT_COLORS: ThemePalette = {
  paper: '#F3F5F5',
  panel: '#FFFFFF',
  wash: '#E6ECEC',
  ink: '#182830',
  muted: '#586A74',
  rule: '#D5DCDE',
  ruleSoft: '#E3E8E9',
  ehs: '#6A4BC4',
  ehsWash: '#EEEAFA',
  opi: '#0E7490',
  opiWash: '#E2F1F5',
  healthy: '#2E8B57',
  healthyWash: '#E2F2E9',
  healthyText: '#1F6B41',
  moderate: '#A96C0B',
  moderateWash: '#F7ECD6',
  moderateText: '#7F5108',
  atRisk: '#C2364A',
  atRiskWash: '#F8E2E6',
  atRiskText: '#9A2437',
  gridLine: '#D5DCDE',
  tooltipBg: '#FFFFFF',
  tooltipBorder: '#D5DCDE',
};

export const DARK_COLORS: ThemePalette = {
  paper: '#0C1317',
  panel: '#131E24',
  wash: '#1B2A32',
  ink: '#E8EFF2',
  muted: '#8CA1AD',
  rule: '#243742',
  ruleSoft: '#1A2931',
  ehs: '#A78BFA',
  ehsWash: 'rgba(167, 139, 250, 0.16)',
  opi: '#22D3EE',
  opiWash: 'rgba(34, 211, 238, 0.16)',
  healthy: '#34D399',
  healthyWash: 'rgba(52, 211, 153, 0.16)',
  healthyText: '#4ADE80',
  moderate: '#FBBF24',
  moderateWash: 'rgba(251, 191, 36, 0.16)',
  moderateText: '#FCD34D',
  atRisk: '#F87171',
  atRiskWash: 'rgba(248, 113, 113, 0.18)',
  atRiskText: '#FCA5A5',
  gridLine: '#243742',
  tooltipBg: '#16232B',
  tooltipBorder: '#2E434F',
};

export function getThemeColors(theme: ThemeMode): ThemePalette {
  return theme === 'dark' ? DARK_COLORS : LIGHT_COLORS;
}

export function getRiskColors(theme: ThemeMode) {
  const p = getThemeColors(theme);
  return {
    healthy: p.healthy,
    moderate: p.moderate,
    'at-risk': p.atRisk,
  } as const;
}

// Fallback constant for backwards compatibility
export const COLORS = LIGHT_COLORS;

export const RISK_COLOR = {
  healthy: LIGHT_COLORS.healthy,
  moderate: LIGHT_COLORS.moderate,
  'at-risk': LIGHT_COLORS.atRisk,
} as const;
