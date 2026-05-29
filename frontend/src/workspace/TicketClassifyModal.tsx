import { useEffect, useMemo, useState } from "react";
import {
  fetchTicketCategories,
  type TicketCategoryGroup,
  type TicketCategoryLeaf,
} from "@/api/ticketCategories";
import { resolveTicketCategorySelection } from "@/utils/ticketCategorySelection";

export type ClassifyAction = "close" | "esc";

type Props = {
  open: boolean;
  ticketId: number;
  ticketSource: string;
  initialCategoryId?: number | null;
  initialCategoryParentId?: number | null;
  action: ClassifyAction;
  onClose: () => void;
  onConfirm: (payload: { categoryId: number; leaf: TicketCategoryLeaf; comment: string }) => void | Promise<void>;
  confirming?: boolean;
};

export default function TicketClassifyModal({
  open,
  ticketId,
  ticketSource,
  initialCategoryId,
  initialCategoryParentId,
  action,
  onClose,
  onConfirm,
  confirming = false,
}: Props) {
  const [groups, setGroups] = useState<TicketCategoryGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [parentId, setParentId] = useState("");
  const [childId, setChildId] = useState("");
  const [comment, setComment] = useState("");
  const [warn, setWarn] = useState("");

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    setComment("");
    setWarn("");
    (async () => {
      try {
        const data = await fetchTicketCategories(ticketSource);
        if (!cancelled) {
          setGroups(data.items);
          const sel = resolveTicketCategorySelection(
            data.items,
            initialCategoryId,
            initialCategoryParentId,
          );
          setParentId(sel.parentId);
          setChildId(sel.childId);
        }
      } catch (e: unknown) {
        if (!cancelled) {
          setParentId("");
          setChildId("");
        }
        if (!cancelled) {
          setLoadError(e instanceof Error ? e.message : "Не удалось загрузить категории");
          setGroups([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, ticketSource, initialCategoryId, initialCategoryParentId]);

  const children = useMemo(() => {
    const pid = Number(parentId);
    if (!pid) return [];
    return groups.find((g) => g.id === pid)?.children ?? [];
  }, [groups, parentId]);

  const selectedLeaf = useMemo(() => {
    const cid = Number(childId);
    if (!cid) return null;
    return children.find((c) => c.id === cid) ?? null;
  }, [children, childId]);

  if (!open) return null;

  const subtitle =
    action === "esc"
      ? `Заявка #${ticketId} — передача инженерам`
      : `Заявка #${ticketId} — завершение`;

  function handleParentChange(value: string) {
    setParentId(value);
    setChildId("");
    setWarn("");
  }

  function handleSubmit() {
    if (confirming) return;
    if (!parentId || !childId || !selectedLeaf) {
      setWarn("Выберите категорию и подкатегорию");
      return;
    }
    void onConfirm({ categoryId: selectedLeaf.id, leaf: selectedLeaf, comment: comment.trim() });
  }

  return (
    <div
      className="clf-mo open"
      role="dialog"
      aria-modal="true"
      aria-labelledby="clf-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="clf-box">
        <div className="clf-hd">
          <div className="clf-hd-ico" aria-hidden>
            ✎
          </div>
          <div>
            <div className="clf-hd-t" id="clf-title">
              Классификация обращения
            </div>
            <div className="clf-hd-sub">{subtitle}</div>
          </div>
        </div>

        <div className="clf-bd">
          {loading ? (
            <p className="ch-list-loading" style={{ margin: 0 }}>
              Загрузка категорий…
            </p>
          ) : null}
          {loadError ? <div className="ch-list-err">{loadError}</div> : null}
          {!loading && !loadError && groups.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--i3)", margin: 0 }}>Категории не найдены для этого источника.</p>
          ) : null}

          <div>
            <div className="clf-lbl">Категория *</div>
            <select
              className="clf-sel"
              value={parentId}
              disabled={loading || Boolean(loadError) || groups.length === 0}
              onChange={(e) => handleParentChange(e.target.value)}
            >
              <option value="">— Выберите категорию —</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="clf-lbl">Подкатегория *</div>
            <select
              className="clf-sel"
              value={childId}
              disabled={!parentId || children.length === 0}
              onChange={(e) => {
                setChildId(e.target.value);
                setWarn("");
              }}
            >
              <option value="">
                {!parentId
                  ? "— Сначала выберите категорию —"
                  : children.length === 0
                    ? "— Нет подкатегорий —"
                    : "— Выберите подкатегорию —"}
              </option>
              {children.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="clf-lbl">Комментарий (необязательно)</div>
            <textarea
              className="clf-ta"
              value={comment}
              placeholder={
                action === "esc"
                  ? "Комментарий для инженеров…"
                  : "Краткое описание решения…"
              }
              onChange={(e) => setComment(e.target.value)}
            />
          </div>

          <div className="clf-warn">{warn}</div>
        </div>

        <div className="clf-ft">
          <button type="button" className="clf-btn sec" onClick={onClose} disabled={confirming}>
            Отмена
          </button>
          <button
            type="button"
            className="clf-btn pri"
            disabled={loading || confirming}
            onClick={handleSubmit}
          >
            {confirming ? "Сохранение…" : "Подтвердить"}
          </button>
        </div>
      </div>
    </div>
  );
}
