type Props = {
  visible: boolean;
  pendingCount: number;
  onClick: () => void;
  className?: string;
  badgeClassName?: string;
};

export default function TicketChatScrollDown({
  visible,
  pendingCount,
  onClick,
  className = "tk-scroll-down",
  badgeClassName = "tk-scroll-down__badge",
}: Props) {
  if (!visible) return null;

  const label =
    pendingCount > 0
      ? pendingCount === 1
        ? "Новое сообщение"
        : `Новых сообщений: ${pendingCount > 99 ? "99+" : pendingCount}`
      : "В конец переписки";

  return (
    <button
      type="button"
      className={className}
      onClick={onClick}
      title={label}
      aria-label={label}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M12 6v12M12 18l-5-5M12 18l5-5"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {pendingCount > 0 ? (
        <span className={badgeClassName} aria-hidden>
          {pendingCount > 99 ? "99+" : pendingCount}
        </span>
      ) : null}
    </button>
  );
}
