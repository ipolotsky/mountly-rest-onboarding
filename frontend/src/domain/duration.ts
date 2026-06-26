export function formatDuration(ms: number | null): string {
  if (ms == null) {
    return "—";
  }
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) {
    return `${seconds} s`;
  }
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest > 0 ? `${minutes} m ${rest} s` : `${minutes} m`;
}
