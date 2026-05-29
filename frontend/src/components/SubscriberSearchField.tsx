import { useEffect, useRef, useState } from "react";
import { fetchDeskSearch, type SubscriberSearchHit } from "@/api/search";
import HighlightText from "@/components/HighlightText";

function idDocLabel(isJuridical: number): string {
  if (isJuridical === 2) return "ИНН";
  return "Паспорт";
}

type SubscriberRowProps = {
  hit: SubscriberSearchHit;
  query: string;
  onPick: () => void;
};

function SubscriberRow({ hit, query, onPick }: SubscriberRowProps) {
  return (
    <button type="button" className="si2 sr-hit" onClick={onPick}>
      <span className="sr-badge sr-badge--ab" aria-hidden>
        АБ
      </span>
      <div className="sr-body">
        <div className="sr-line sr-line-title">
          <HighlightText text={hit.name || "Без имени"} query={query} />
        </div>
        <div className="sr-line">
          <span className="sr-lbl">ID</span>
          <HighlightText text={String(hit.id)} query={query} />
          <span className="sr-sep">·</span>
          <span className="sr-lbl">Логин</span>
          <HighlightText text={hit.login || "—"} query={query} />
        </div>
        <div className="sr-line">
          <span className="sr-lbl">Почта</span>
          <HighlightText text={hit.email || "—"} query={query} />
          <span className="sr-sep">·</span>
          <span className="sr-lbl">Тел.</span>
          <HighlightText text={hit.phone || "—"} query={query} />
        </div>
        <div className="sr-line">
          <span className="sr-lbl">{idDocLabel(hit.is_juridical)}</span>
          {hit.id_doc ? (
            <HighlightText text={hit.id_doc} query={query} />
          ) : (
            <span className="sr-muted">—</span>
          )}
        </div>
      </div>
    </button>
  );
}

export type SubscriberSearchFieldProps = {
  disabled?: boolean;
  selected: SubscriberSearchHit | null;
  onSelect: (hit: SubscriberSearchHit | null) => void;
  placeholder?: string;
};

export default function SubscriberSearchField({
  disabled = false,
  selected,
  onSelect,
  placeholder = "ФИО, логин, ID, телефон, email, паспорт, ИНН…",
}: SubscriberSearchFieldProps) {
  const [q, setQ] = useState("");
  const [openDrop, setOpenDrop] = useState(false);
  const [subs, setSubs] = useState<SubscriberSearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (disabled || selected) {
      setSubs([]);
      setLoading(false);
      setSearchError(null);
      return;
    }
    const s = q.trim();
    if (s.length < 2) {
      setSubs([]);
      setLoading(false);
      setSearchError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setSearchError(null);

    const timer = window.setTimeout(() => {
      fetchDeskSearch(s, 15)
        .then((data) => {
          if (!cancelled) setSubs(data.subscribers);
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setSubs([]);
            setSearchError(err instanceof Error ? err.message : "Ошибка поиска");
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 150);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [q, disabled, selected]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpenDrop(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const trimmed = q.trim();
  const subsVisible = subs.length > 0;
  const showDrop = openDrop && trimmed.length >= 2 && !disabled && !selected;

  function onSearchInput(v: string) {
    setQ(v);
    setOpenDrop(v.trim().length >= 2);
  }

  function pick(hit: SubscriberSearchHit) {
    onSelect(hit);
    setQ("");
    setOpenDrop(false);
  }

  function clearSelection() {
    onSelect(null);
    setQ("");
  }

  if (selected) {
    return (
      <div className="call-subscriber-picked">
        <div className="call-subscriber-picked__main">
          <span className="sr-badge sr-badge--ab" aria-hidden>
            АБ
          </span>
          <div>
            <div className="call-subscriber-picked__name">{selected.name || "Без имени"}</div>
            <div className="call-subscriber-picked__meta">
              ID {selected.id}
              {selected.login ? ` · ${selected.login}` : ""}
              {selected.station_id ? ` · станция ${selected.station_id}` : ""}
            </div>
          </div>
        </div>
        {!disabled ? (
          <button type="button" className="call-subscriber-picked__clear" onClick={clearSelection}>
            Сменить
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div ref={wrapRef} className="sw sr-wrap call-search-wrap">
      <input
        className="si sr-input"
        value={q}
        disabled={disabled}
        onChange={(e) => onSearchInput(e.target.value)}
        onFocus={() => trimmed.length >= 2 && setOpenDrop(true)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && subs.length) {
            e.preventDefault();
            pick(subs[0]);
          }
        }}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
        aria-label="Поиск абонента"
        aria-expanded={showDrop}
        aria-haspopup="listbox"
      />
      <svg className="sic sr-icon" width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden>
        <circle cx="9" cy="9" r="5.5" stroke="currentColor" strokeWidth="1.5" />
        <path d="M14 14l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      {loading ? <span className="sr-spinner call-search-spinner" aria-hidden /> : null}

      <div className={`sd sr-drop ${showDrop ? "vis" : ""}`} role="listbox">
        {searchError ? <div className="sr-empty sr-error">{searchError}</div> : null}

        {!searchError && loading && !subsVisible ? <div className="sr-empty">Ищем…</div> : null}

        {!searchError && !loading && trimmed.length >= 2 && !subsVisible ? (
          <div className="sr-empty">Абонент не найден</div>
        ) : null}

        {subsVisible ? (
          <>
            <div className="ssc">Абоненты</div>
            {subs.map((s) => (
              <SubscriberRow key={s.id} hit={s} query={trimmed} onPick={() => pick(s)} />
            ))}
          </>
        ) : null}
      </div>
    </div>
  );
}
