/** Градация оценок: 1–2 красный, 3 жёлтый, 4 синий, 5 зелёный. */

export type RatingTone = "bad" | "warn" | "mid" | "good";

export function ratingTone(value: number | null | undefined, discrete = false): RatingTone | null {
  if (value == null || !Number.isFinite(value)) return null;

  if (discrete) {
    const v = Math.round(value);
    if (v <= 2) return "bad";
    if (v === 3) return "warn";
    if (v === 4) return "mid";
    if (v >= 5) return "good";
    return "bad";
  }

  if (value < 2.5) return "bad";
  if (value < 3.5) return "warn";
  if (value < 4.5) return "mid";
  return "good";
}

export function ratingToneClass(value: number | null | undefined, discrete = false): string {
  const tone = ratingTone(value, discrete);
  return tone ? `rating-tone rating-tone--${tone}` : "";
}
