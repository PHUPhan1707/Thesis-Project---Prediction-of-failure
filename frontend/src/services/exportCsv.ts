import type { Student } from '../types';

function escapeCsv(value: unknown): string {
  if (value === null || value === undefined) return '';
  const s = String(value);
  // Escape quotes and wrap in quotes if needed
  const needsQuotes = /[",\n\r]/.test(s);
  const escaped = s.replace(/"/g, '""');
  return needsQuotes ? `"${escaped}"` : escaped;
}

function downloadTextFile(filename: string, content: string, mime = 'text/csv;charset=utf-8') {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function exportStudentsToCSV(students: Student[], opts?: { courseId?: string; filename?: string }) {
  const headers = [
    'user_id',
    'full_name',
    'email',
    'risk_level',
    'fail_risk_score',
    'mooc_grade_percentage',
    'mooc_completion_rate',
    'days_since_last_activity',
  ] as const;

  const rows = students.map((s) => [
    s.user_id,
    s.full_name ?? '',
    s.email ?? '',
    s.risk_level,
    s.fail_risk_score,
    s.mooc_grade_percentage,
    s.mooc_completion_rate,
    s.days_since_last_activity,
  ]);

  const csv = [
    headers.join(','),
    ...rows.map((row) => row.map(escapeCsv).join(',')),
  ].join('\n');

  const date = new Date();
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');

  const safeCourse = (opts?.courseId || 'course')
    .replace(/[:+\/\\]/g, '_')
    .slice(0, 80);
  const filename = opts?.filename || `early_warning_${safeCourse}_${yyyy}${mm}${dd}.csv`;

  downloadTextFile(filename, csv);
}


