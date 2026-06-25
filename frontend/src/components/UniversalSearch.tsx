import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchDeskSearch, type DeskSearchKbHit, type SubscriberSearchHit } from "@/api/search";
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

type KbRowProps = {
  hit: DeskSearchKbHit;
  query: string;
  onPick: () => void;
};

function KbRow({ hit, query, onPick }: KbRowProps) {
  const excerpt = hit.excerpt?.trim();
  return (
    <button type="button" className="si2 sr-hit" onClick={onPick}>
      <span className="sr-badge sr-badge--kb" aria-hidden>
        БЗ
      </span>
      <div className="sr-body">
        <div className="sn">
          <HighlightText text={hit.title} query={query} />
        </div>
        {excerpt ? (
          <div className="sm">
            <HighlightText text={excerpt} query={query} />
          </div>
        ) : null}
      </div>
    </button>
  );
}

export default function UniversalSearch() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [openDrop, setOpenDrop] = useState(false);
  const [subs, setSubs] = useState<SubscriberSearchHit[]>([]);
  const [kb, setKb] = useState<DeskSearchKbHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const s = q.trim();
    if (s.length < 2) {
      setSubs([]);
      setKb([]);
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
          if (!cancelled) {
            setSubs(data.subscribers);
            setKb(data.kb);
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setSubs([]);
            setKb([]);
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
  }, [q]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpenDrop(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const trimmed = q.trim();
  const subsVisible = subs.length > 0;
  const kbVisible = kb.length > 0;
  const hasResults = subsVisible || kbVisible;
  const showDrop = openDrop && trimmed.length >= 2;

  function onSearchInput(v: string) {
    setQ(v);
    setOpenDrop(v.trim().length >= 2);
  }

  function pickSubscriber(hit: SubscriberSearchHit) {
    setOpenDrop(false);
    setQ("");
    navigate(`/users/${hit.id}`);
  }

  function pickKbArticle(hit: DeskSearchKbHit) {
    setOpenDrop(false);
    setQ("");
    navigate(`/kb/${hit.slug}`);
  }

  function onSearchEnter() {
    if (!trimmed) return;
    setOpenDrop(false);
    if (kb.length) {
      pickKbArticle(kb[0]);
      return;
    }
    if (subs.length) pickSubscriber(subs[0]);
  }

  return (
    <div ref={wrapRef} className="sw sr-wrap" style={{ maxWidth: 680, margin: "0 auto" }}>
      <input
        className="si sr-input"
        value={q}
        onChange={(e) => onSearchInput(e.target.value)}
        onFocus={() => trimmed.length >= 2 && setOpenDrop(true)}
        onKeyDown={(e) => e.key === "Enter" && onSearchEnter()}
        placeholder="ФИО, логин, ID, телефон, email, паспорт, ИНН…"
        autoComplete="off"
        spellCheck={false}
        aria-label="Поиск абонента или базы знаний"
        aria-expanded={showDrop}
        aria-haspopup="listbox"
      />
      <svg className="sic sr-icon" width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden>
        <circle cx="9" cy="9" r="5.5" stroke="currentColor" strokeWidth="1.5" />
        <path d="M14 14l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      {loading ? <span className="sr-spinner" aria-hidden /> : null}

      <div className={`sd sr-drop ${showDrop ? "vis" : ""}`} role="listbox">
        {searchError ? <div className="sr-empty sr-error">{searchError}</div> : null}

        {!searchError && loading && !hasResults ? <div className="sr-empty">Ищем…</div> : null}

        {!searchError && !loading && trimmed.length >= 2 && !hasResults ? (
          <div className="sr-empty">Ничего не найдено</div>
        ) : null}

        {kbVisible ? (
          <>
            <div className="ssc">База знаний</div>
            {kb.map((item) => (
              <KbRow
                key={item.id}
                hit={item}
                query={trimmed}
                onPick={() => pickKbArticle(item)}
              />
            ))}
          </>
        ) : null}

        {subsVisible ? (
          <>
            <div className="ssc">Абоненты</div>
            {subs.map((s) => (
              <SubscriberRow key={s.id} hit={s} query={trimmed} onPick={() => pickSubscriber(s)} />
            ))}
          </>
        ) : null}
      </div>
    </div>
  );
}
