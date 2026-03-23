const SERVER_TIMESTAMP_WITH_TIMEZONE_REGEX = /(Z|[+-]\d{2}:\d{2})$/i;

export function parseServerTimestamp(value: string | null): number | null {
  if (!value) {
    return null;
  }

  const normalizedValue = SERVER_TIMESTAMP_WITH_TIMEZONE_REGEX.test(value) ? value : value + "Z";
  const parsed = Date.parse(normalizedValue);
  return Number.isNaN(parsed) ? null : parsed;
}

export function formatElapsed(elapsedMs: number | null): string {
  if (elapsedMs === null) {
    return "00:00";
  }

  const totalSeconds = Math.max(0, Math.floor(elapsedMs / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
