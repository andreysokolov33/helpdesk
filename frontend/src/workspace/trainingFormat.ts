import type { TrainingSessionStatus } from "@/api/training";
import { parseApiDate } from "@/utils/dateTime";

/** Таймер сессии: 04:09 или 1:04:09. */
export function formatClock(totalSec: number): string {
  const sec = Math.max(0, Math.floor(totalSec));
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

/** Длительность словами: «45 с», «12 мин», «1 ч 05 мин». */
export function formatTrainingDuration(totalSec: number | null | undefined): string {
  if (totalSec == null || !Number.isFinite(totalSec) || totalSec <= 0) return "—";
  const sec = Math.round(totalSec);
  if (sec < 60) return `${sec} с`;
  const m = Math.floor(sec / 60);
  if (m < 60) {
    const s = sec % 60;
    return s > 0 && m < 10 ? `${m} мин ${String(s).padStart(2, "0")} с` : `${m} мин`;
  }
  const h = Math.floor(m / 60);
  const rm = m % 60;
  return rm > 0 ? `${h} ч ${String(rm).padStart(2, "0")} мин` : `${h} ч`;
}

export function formatTrainingPercent(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${Math.round(value)}%`;
}

export function formatTrainingDateTime(iso: string | null | undefined): string {
  const d = parseApiDate(iso);
  if (!d) return "—";
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTrainingDay(iso: string | null | undefined): { day: string; time: string } {
  const d = parseApiDate(iso);
  if (!d) return { day: "—", time: "" };
  return {
    day: d.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" }),
    time: d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }),
  };
}

export function secondsSince(iso: string | null | undefined, nowMs: number): number {
  const d = parseApiDate(iso);
  if (!d) return 0;
  return Math.max(0, Math.floor((nowMs - d.getTime()) / 1000));
}

export function trainingStatusLabel(status: TrainingSessionStatus): string {
  if (status === "in_progress") return "Идёт";
  if (status === "abandoned") return "Прервана";
  return "Завершена";
}

export function trainingStatusKind(status: TrainingSessionStatus): "good" | "bad" | "neutral" {
  if (status === "in_progress") return "good";
  if (status === "abandoned") return "neutral";
  return "neutral";
}

/** «98/100» — счёт ответов. */
export function formatAnswerRatio(correct: number, total: number): string {
  return `${correct}/${total}`;
}

export function pluralRu(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}
