import FastCheckPanel from "@/components/FastCheckPanel";
import type { FastCheckResponse } from "@/api/userProfile";

type Props = {
  userId: number;
  open: boolean;
  subscriberSidebarOpen: boolean;
  cachedData: FastCheckResponse | null;
  onCachedData: (data: FastCheckResponse) => void;
  onClose: () => void;
  onLoadingChange?: (loading: boolean) => void;
  onDisconnect?: () => void;
};

export default function TicketFastCheckDrawer({
  userId,
  open,
  subscriberSidebarOpen,
  cachedData,
  onCachedData,
  onClose,
  onLoadingChange,
  onDisconnect,
}: Props) {
  if (!open) return null;

  return (
    <aside
      className={`tk-fc-drawer open${subscriberSidebarOpen ? " tk-fc-drawer--with-sidebar" : ""}`}
      aria-label="Проверка абонента"
    >
      <div className="tk-fc-drawer__head">
        <span className="tk-fc-drawer__title">Проверка</span>
        <button type="button" className="tk-fc-drawer__close" onClick={onClose} aria-label="Закрыть">
          ×
        </button>
      </div>
      <div className="tk-fc-drawer__body">
        <FastCheckPanel
          userId={userId}
          layout="stacked"
          hideIdleUI
          initialData={cachedData}
          onResult={onCachedData}
          autoRun={!cachedData}
          repeatLabel="Новая проверка"
          onPhaseChange={(p) => onLoadingChange?.(p === "loading")}
          onDisconnect={onDisconnect}
        />
      </div>
    </aside>
  );
}
