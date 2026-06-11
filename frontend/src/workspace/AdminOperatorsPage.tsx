import { useCallback, useEffect, useState } from "react";
import { fetchAuthMe, type AuthMe } from "@/api/auth";
import {
  createOperator,
  fetchOperatorsManage,
  resetOperatorPassword,
  updateOperator,
  type OperatorManageItem,
  type OperatorManageStats,
} from "@/api/operatorsManage";
import OperatorCreateModal from "@/components/OperatorCreateModal";
import OperatorCreatedModal, { type OperatorCredsVariant } from "@/components/OperatorCreatedModal";
import OperatorEditModal from "@/components/OperatorEditModal";
import { staffEditIcon } from "@/staffIcons";

const POLL_MS = 30_000;

function displayName(op: OperatorManageItem): string {
  return op.full_name?.trim() || op.login;
}

function canEditOperator(op: OperatorManageItem, currentUserId: number | null): boolean {
  if (currentUserId == null) return false;
  if (op.level === 2) return op.id === currentUserId;
  return true;
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

function StaffTableColgroup({ showOpenTickets }: { showOpenTickets: boolean }) {
  return (
    <colgroup>
      <col className="op-admin-col-name" />
      <col className="op-admin-col-login" />
      <col className="op-admin-col-status" />
      <col className="op-admin-col-online" />
      {showOpenTickets ? <col className="op-admin-col-open" /> : null}
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
  const colCount = showOpenTickets ? 6 : 5;
  return (
    <div className="op-admin-table-wrap">
      <table className="dt op-admin-table">
        <StaffTableColgroup showOpenTickets={showOpenTickets} />
        <thead>
          <tr>
            <th>ФИО</th>
            <th>Логин</th>
            <th>Статус</th>
            <th>Онлайн</th>
            {showOpenTickets ? <th>Открытые</th> : null}
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
                  <span
                    className={`op-admin-badge ${op.is_active ? "op-admin-badge--on" : "op-admin-badge--off"}`}
                  >
                    {op.is_active ? "Активен" : "Архив"}
                  </span>
                </td>
                <td className="op-admin-cell-online">
                  {op.is_active ? <OnlineDot online={op.is_online} /> : "—"}
                </td>
                {showOpenTickets ? (
                  <td className="op-admin-cell-open" title="Открытые тикеты, где оператор — исполнитель">
                    {op.open_tickets_count ?? 0}
                  </td>
                ) : null}
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

  const currentUserId = me?.user_id ?? null;

  const patchRow = useCallback((updated: OperatorManageItem) => {
    const patch = (list: OperatorManageItem[]) =>
      list.map((row) => (row.id === updated.id ? updated : row));
    setAdmins((prev) => patch(prev));
    setOperators((prev) => patch(prev));
    setEditTarget((prev) => (prev?.id === updated.id ? updated : prev));
  }, []);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError("");
    try {
      const data = await fetchOperatorsManage();
      setAdmins(data.admins);
      setOperators(data.operators);
      setStats(data.stats);
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
    void load();
  }, [load]);

  useEffect(() => {
    const timer = window.setInterval(() => void load(true), POLL_MS);
    function onVisible() {
      if (document.visibilityState === "visible") void load(true);
    }
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [load]);

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
      await load(true);
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

  async function handleArchiveToggle(restore: boolean) {
    if (!editTarget) return;
    const label = restore ? "восстановить" : "архивировать";
    const ok = window.confirm(
      restore
        ? `Восстановить оператора «${displayName(editTarget)}»?`
        : `Архивировать оператора «${displayName(editTarget)}»? Вход будет заблокирован.`,
    );
    if (!ok) return;
    setBusy(true);
    try {
      const updated = await updateOperator(editTarget.id, { is_active: restore });
      patchRow(updated);
      await load(true);
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
        onArchive={() => handleArchiveToggle(false)}
        onRestore={() => handleArchiveToggle(true)}
      />
    </div>
  );
}
