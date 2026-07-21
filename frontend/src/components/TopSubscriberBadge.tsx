type Props = {
  rank: number | null | undefined;
  /** В панели абонента — подпись «ТОП 50», в списке — только число (место) */
  labeled?: boolean;
  className?: string;
};

/** Бейдж места в ТОП-50 абонентов по платежам. */
export default function TopSubscriberBadge({ rank, labeled = false, className = "" }: Props) {
  if (rank == null || !Number.isFinite(rank) || rank < 1) return null;
  const n = Math.trunc(rank);
  return (
    <span
      className={`top-rank-badge${labeled ? " top-rank-badge--labeled" : ""}${className ? ` ${className}` : ""}`}
      title={`ТОП-50 абонентов по платежам · место ${n}`}
    >
      {labeled ? "ТОП 50" : n}
    </span>
  );
}
