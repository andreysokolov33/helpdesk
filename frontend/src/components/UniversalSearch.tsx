import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchDeskSearch, type SubscriberSearchHit } from "@/api/search";
import HighlightText from "@/components/HighlightText";
import { MOCK_KB, type KbArticle } from "@/data/mockCc";

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, "").slice(0, 80);
}

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

export default function UniversalSearch() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [openDrop, setOpenDrop] = useState(false);
  const [kbOpen, setKbOpen] = useState(false);
  const [kbTitle, setKbTitle] = useState("");
  const [kbBody, setKbBody] = useState("");
  const [subs, setSubs] = useState<SubscriberSearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  const kb = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (s.length < 2) return [];
    return MOCK_KB.filter((k) => k.t.toLowerCase().includes(s) || k.k.includes(s));
  }, [q]);

  useEffect(() => {
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
    setKbOpen(false);
  }

  function showKbCard(article: KbArticle) {
    setKbTitle(article.t);
    setKbBody(article.b);
    setKbOpen(true);
    setOpenDrop(false);
    setQ("");
  }

  function pickSubscriber(hit: SubscriberSearchHit) {
    setOpenDrop(false);
    setQ("");
    navigate(`/users/${hit.id}`);
  }

  function onSearchEnter() {
    const s = trimmed.toLowerCase();
    if (!s) return;
    setOpenDrop(false);
    const kh = MOCK_KB.filter((k) => k.t.toLowerCase().includes(s) || k.k.includes(s));
    if (kh.length) {
      showKbCard(kh[0]);
      return;
    }
    if (subs.length) pickSubscriber(subs[0]);
  }

  return (
    <>
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

          {subsVisible ? (
            <>
              <div className="ssc">Абоненты</div>
              {subs.map((s) => (
                <SubscriberRow key={s.id} hit={s} query={trimmed} onPick={() => pickSubscriber(s)} />
              ))}
            </>
          ) : null}

          {kbVisible ? (
            <>
              <div className="ssc">База знаний</div>
              {kb.slice(0, 5).map((k) => (
                <button type="button" key={k.t} className="si2 sr-hit" onClick={() => showKbCard(k)}>
                  <span className="sr-badge sr-badge--kb" aria-hidden>
                    БД
                  </span>
                  <div className="sr-body">
                    <div className="sn">{k.t}</div>
                    <div className="sm">{stripHtml(k.b)}…</div>
                  </div>
                </button>
              ))}
            </>
          ) : null}
        </div>
      </div>

      <div className={`kbc ${kbOpen ? "vis" : ""}`}>
        <button type="button" className="kbc-x" aria-label="Закрыть" onClick={() => setKbOpen(false)}>
          ×
        </button>
        <div className="kbc-t">
          {kbTitle} <span className="kbc-tag">Инструкция</span>
        </div>
        <div className="kbc-b" dangerouslySetInnerHTML={{ __html: kbBody }} />
      </div>
    </>
  );
}
