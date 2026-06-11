import { useCallback, useEffect, useState } from "react";
import { fetchAuthMe, type AuthMe } from "@/api/auth";
import {
  createOperator,
  fetchOperatorsManage,
  OPERATORS_MANAGE_PER_PAGE,
  resetOperatorPassword,
  updateOperator,
  type OperatorManageItem,
  type OperatorManagePagination,
  type OperatorManageStats,
} from "@/api/operatorsManage";
import OperatorCreateModal from "@/components/OperatorCreateModal";
import OperatorCreatedModal, { type OperatorCredsVariant } from "@/components/OperatorCreatedModal";
import OperatorArchiveConfirmModal from "@/components/OperatorArchiveConfirmModal";
import OperatorEditModal from "@/components/OperatorEditModal";
import { staffEditIcon } from "@/staffIcons";
import { formatDateTimeLocal } from "@/utils/dateTime";

const POLL_MS = 30_000;

function displayName(op: OperatorManageItem): string {
  return op.full_name?.trim() || op.login;
}

function canEditOperator(op: OperatorManageItem, currentUserId: number | null): boolean {
  if (currentUserId == null) return false;
  if (op.level === 2) return op.id === currentUserId;
  return true;
}

function formatLastSeenLabel(iso: string | null): string {
  if (!iso) return "Не авторизовывался";
  const when = formatDateTimeLocal(iso, { withYear: true });
  return when ? `Был(а) ${when}` : "Не авторизовывался";
}

function OnlineDot({ online }: { online: boolean }) {
  return (
    <span
      className={`op-admin-online-dot ${online ? "op-admin-online-dot--yes" : "op-admin-online-dot--no"}`}
      title={online ? "На сайте" : "Не в сети"}
      aria-label={online ? "Онлайн" : "Офлайн"}
    />
  );
}

function StaffTableColgroup() {
  return (
    <colgroup>
      <col className="op-admin-col-name" />
      <col className="op-admin-col-login" />
      <col className="op-admin-col-status" />
      <col className="op-admin-col-online" />
      <col className="op-admin-col-open" />
      <col className="op-admin-col-actions" />
    </colgroup>
  );
}

type StaffTableProps = {
  rows: OperatorManageItem[];
  loading: boolean;
  emptyLabel: string;
  currentUserId: number | null;
  showOpenTickets?: boolean;
  onEdit: (op: OperatorManageItem) => void;
};

function StaffTable({
  rows,
  loading,
  emptyLabel,
  currentUserId,
  showOpenTickets = false,
  onEdit,
}: StaffTableProps) {
  const colCount = 6;
  return (
    <div className="op-admin-table-wrap">
      <table className="dt op-admin-table">
        <StaffTableColgroup />
        <thead>
          <tr>
            <th>ФИО</th>
            <th>Логин</th>
            <th>Статус</th>
            <th>Онлайн</th>
            {showOpenTickets ? (
              <th>Открытые</th>
            ) : (
              <th className="op-admin-col-open-spacer" aria-hidden />
            )}
            <th aria-label="Действия" />
          </tr>
        </thead>
        <tbody>
          {loading && rows.length === 0 ? (
            <tr>
              <td colSpan={colCount} className="op-admin-empty">
                Загрузка…
              </td>
            </tr>
          ) : null}
          {!loading && rows.length === 0 ? (
            <tr>
              <td colSpan={colCount} className="op-admin-empty">
                {emptyLabel}
              </td>
            </tr>
          ) : null}
          {rows.map((op) => {
            const editable = canEditOperator(op, currentUserId);
            return (
              <tr key={op.id} className={!op.is_active ? "op-admin-row--archived" : ""}>
                <td className="op-admin-cell-name">{op.full_name || "—"}</td>
                <td className="op-admin-login">{op.login}</td>
                <td className="op-admin-cell-status">
                  <div className="op-admin-status-stack">
                    <span
                      className={`op-admin-badge ${op.is_active ? "op-admin-badge--on" : "op-admin-badge--off"}`}
                    >
                      {op.is_active ? "Активен" : "Архив"}
                    </span>
                    {op.is_active && !op.is_online ? (
                      <span
                        className="op-admin-last-seen"
                        title={
                          op.last_activity
                            ? "Последняя активность на портале"
                            : "Учётная запись ещё не использовалась для входа"
                        }
                      >
                        {formatLastSeenLabel(op.last_activity)}
                      </span>
                    ) : null}
                  </div>
                </td>
                <td className="op-admin-cell-online">
                  {op.is_active ? <OnlineDot online={op.is_online} /> : "—"}
                </td>
                {showOpenTickets ? (
                  <td className="op-admin-cell-open" title="Открытые тикеты, где оператор — исполнитель">
                    {op.open_tickets_count ?? 0}
                  </td>
                ) : (
                  <td className="op-admin-cell-open op-admin-cell-open--spacer" aria-hidden />
                )}
                <td className="op-admin-actions">
                  {editable ? (
                    <button
                      type="button"
                      className="op-admin-edit-btn"
                      aria-label="Редактировать"
                      title="Редактировать"
                      onClick={() => onEdit(op)}
                    >
                      <img src={staffEditIcon} alt="" className="op-admin-edit-ico" width={18} height={18} />
                    </button>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminOperatorsPage() {
  const [me, setMe] = useState<AuthMe | null>(null);
  const [admins, setAdmins] = useState<OperatorManageItem[]>([]);
  const [operators, setOperators] = useState<OperatorManageItem[]>([]);
  const [stats, setStats] = useState<OperatorManageStats>({ active_count: 0, online_count: 0 });
  const [operatorsPage, setOperatorsPage] = useState(1);
  const [operatorsPagination, setOperatorsPagination] = useState<OperatorManagePagination>({
    page: 1,
    per_page: OPERATORS_MANAGE_PER_PAGE,
    total: 0,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [editTarget, setEditTarget] = useState<OperatorManageItem | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [credsModal, setCredsModal] = useState<{
    variant: OperatorCredsVariant;
    login: string;
    password: string;
    fullName: string;
  } | null>(null);
  const [archiveConfirm, setArchiveConfirm] = useState<{
    operator: OperatorManageItem;
    restore: boolean;
  } | null>(null);

  const currentUserId = me?.user_id ?? null;

  const patchRow = useCallback((updated: OperatorManageItem) => {
    const patch = (list: OperatorManageItem[]) =>
      list.map((row) => (row.id === updated.id ? updated : row));
    setAdmins((prev) => patch(prev));
    setOperators((prev) => patch(prev));
    setEditTarget((prev) => (prev?.id === updated.id ? updated : prev));
  }, []);

  const load = useCallback(async (page: number, silent = false) => {
    if (!silent) setLoading(true);
    setError("");
    try {
      const data = await fetchOperatorsManage({
        page,
        per_page: OPERATORS_MANAGE_PER_PAGE,
      });
      const pg = data.operators_pagination;
      if (pg.total > 0 && page > pg.total_pages) {
        setOperatorsPage(pg.total_pages);
        return;
      }
      setAdmins(data.admins);
      setOperators(data.operators);
      setStats(data.stats);
      setOperatorsPagination(pg);
      setOperatorsPage(pg.page);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchAuthMe()
      .then((auth) => {
        if (!cancelled) setMe(auth);
      })
      .catch(() => {
        if (!cancelled) setMe(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    void load(operatorsPage);
  }, [load, operatorsPage]);

  useEffect(() => {
    const timer = window.setInterval(() => void load(operatorsPage, true), POLL_MS);
    function onVisible() {
      if (document.visibilityState === "visible") void load(operatorsPage, true);
    }
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [load, operatorsPage]);

  async function handleResetPassword(password: string) {
    if (!editTarget) return;
    setBusy(true);
    try {
      await resetOperatorPassword(editTarget.id, password);
      setCredsModal({
        variant: "password",
        login: editTarget.login,
        password,
        fullName: displayName(editTarget),
      });
      setEditTarget(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Не удалось сменить пароль");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreate(payload: {
    login: string;
    password: string;
    full_name: string;
    email: string | null;
  }) {
    setBusy(true);
    try {
      await createOperator(payload);
      setCreateOpen(false);
      setCredsModal({
        variant: "created",
        login: payload.login,
        password: payload.password,
        fullName: payload.full_name,
      });
      setOperatorsPage(1);
      await load(1, true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Не удалось создать оператора");
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveName(fullName: string) {
    if (!editTarget) return;
    setBusy(true);
    try {
      const updated = await updateOperator(editTarget.id, { full_name: fullName });
      patchRow(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить ФИО");
    } finally {
      setBusy(false);
    }
  }

  function requestArchiveToggle(operator: OperatorManageItem, restore: boolean) {
    setArchiveConfirm({ operator, restore });
  }

  async function confirmArchiveToggle() {
    if (!archiveConfirm) return;
    const { operator, restore } = archiveConfirm;
    const label = restore ? "восстановить" : "архивировать";
    setBusy(true);
    try {
      const updated = await updateOperator(operator.id, { is_active: restore });
      patchRow(updated);
      setArchiveConfirm(null);
      if (editTarget?.id === operator.id) {
        setEditTarget(updated);
        if (!restore) setEditTarget(null);
      }
      await load(operatorsPage, true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : `Не удалось ${label} оператора`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="op-page op-page--admin">
      <div className="op-head">
        <h1 className="op-title">Сотрудники</h1>
        <p className="op-sub">Управление учётными записями операторов Helpdesk</p>
      </div>

      <div className="op-admin-metrics">
        <div className="op-admin-metric">
          <div className="op-admin-metric-label">Активных операторов</div>
          <div className="op-admin-metric-value">{loading ? "…" : stats.active_count}</div>
        </div>
        <div className="op-admin-metric">
          <div className="op-admin-metric-label">Онлайн</div>
          <div className="op-admin-metric-value op-admin-metric-value--online">
            {loading ? "…" : stats.online_count}
          </div>
        </div>
      </div>

      {error ? <div className="op-error">{error}</div> : null}

      <div className="op-admin-staff">
        {admins.length > 0 || loading ? (
          <div className="card op-card op-admin-staff-card">
            <div className="op-section-head">
              <h2 className="op-section-title">Администраторы</h2>
            </div>
            <StaffTable
              rows={admins}
              loading={loading}
              emptyLabel="Нет администраторов"
              currentUserId={currentUserId}
              onEdit={setEditTarget}
            />
          </div>
        ) : null}

        <div className="card op-card op-admin-staff-card">
          <div className="op-section-head">
            <h2 className="op-section-title">Операторы</h2>
            <button type="button" className="clf-btn pri op-admin-add-btn" onClick={() => setCreateOpen(true)}>
              Добавить оператора
            </button>
          </div>

          <StaffTable
            rows={operators}
            loading={loading}
            emptyLabel="Нет операторов"
            currentUserId={currentUserId}
            showOpenTickets
            onEdit={setEditTarget}
          />

          {operatorsPagination.total > OPERATORS_MANAGE_PER_PAGE ? (
            <div className="ch-pager op-admin-pager">
              <button
                type="button"
                className="ch-page-btn"
                disabled={operatorsPage <= 1 || loading}
                onClick={() => setOperatorsPage((p) => Math.max(1, p - 1))}
              >
                Назад
              </button>
              <span className="ch-page-info">
                Стр. {operatorsPagination.page} / {operatorsPagination.total_pages} · всего{" "}
                {operatorsPagination.total}
              </span>
              <button
                type="button"
                className="ch-page-btn"
                disabled={operatorsPage >= operatorsPagination.total_pages || loading}
                onClick={() => setOperatorsPage((p) => p + 1)}
              >
                Вперёд
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <OperatorCreateModal
        open={createOpen}
        busy={busy}
        onClose={() => {
          if (!busy) setCreateOpen(false);
        }}
        onSave={handleCreate}
      />

      <OperatorCreatedModal
        open={Boolean(credsModal)}
        variant={credsModal?.variant || "created"}
        login={credsModal?.login || ""}
        password={credsModal?.password || ""}
        fullName={credsModal?.fullName || ""}
        onClose={() => setCredsModal(null)}
      />

      <OperatorEditModal
        open={Boolean(editTarget)}
        operator={editTarget}
        busy={busy}
        onClose={() => {
          if (!busy) setEditTarget(null);
        }}
        onSaveName={handleSaveName}
        onSavePassword={handleResetPassword}
        onArchive={() => {
          if (editTarget) requestArchiveToggle(editTarget, false);
        }}
        onRestore={() => {
          if (editTarget) requestArchiveToggle(editTarget, true);
        }}
      />

      <OperatorArchiveConfirmModal
        open={Boolean(archiveConfirm)}
        operatorName={archiveConfirm ? displayName(archiveConfirm.operator) : ""}
        operatorLogin={archiveConfirm?.operator.login || ""}
        restore={archiveConfirm?.restore ?? false}
        openTicketsCount={archiveConfirm?.operator.open_tickets_count ?? 0}
        busy={busy}
        onClose={() => {
          if (!busy) setArchiveConfirm(null);
        }}
        onConfirm={() => void confirmArchiveToggle()}
      />
    </div>
  );
}
