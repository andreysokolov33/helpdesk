import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchDeskSearch, type SubscriberSearchHit } from "@/api/search";
import HighlightText from "@/components/HighlightText";
import { MOCK_KB, type KbArticle } from "@/data/mockCc";

const SCOPE_STORAGE_KEY = "helpdesk.universal-search.scope";

type SearchScope = { abon: boolean; kb: boolean };

function loadSearchScope(): SearchScope {
  try {
    const raw = localStorage.getItem(SCOPE_STORAGE_KEY);
    if (!raw) return { abon: true, kb: true };
    const p = JSON.parse(raw) as Partial<SearchScope>;
    const abon = p.abon !== false;
    const kb = p.kb !== false;
    if (!abon && !kb) return { abon: true, kb: true };
    return { abon, kb };
  } catch {
    return { abon: true, kb: true };
  }
}

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
  const [scope, setScope] = useState<SearchScope>(loadSearchScope);
  const [openDrop, setOpenDrop] = useState(false);
  const [kbOpen, setKbOpen] = useState(false);
  const [kbTitle, setKbTitle] = useState("");
  const [kbBody, setKbBody] = useState("");
  const [subs, setSubs] = useState<SubscriberSearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  function toggleScope(key: keyof SearchScope) {
    setScope((prev) => {
      const other = key === "abon" ? "kb" : "abon";
      if (prev[key] && !prev[other]) return prev;
      const next = { ...prev, [key]: !prev[key] };
      try {
        localStorage.setItem(SCOPE_STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* ignore quota / private mode */
      }
      return next;
    });
  }

  const kb = useMemo(() => {
    if (!scope.kb) return [];
    const s = q.trim().toLowerCase();
    if (s.length < 2) return [];
    return MOCK_KB.filter((k) => k.t.toLowerCase().includes(s) || k.k.includes(s));
  }, [q, scope.kb]);

  useEffect(() => {
    const s = q.trim();
    if (!scope.abon || s.length < 2) {
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
    }, 280);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [q, scope.abon]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpenDrop(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const trimmed = q.trim();
  const subsVisible = scope.abon && subs.length > 0;
  const kbVisible = scope.kb && kb.length > 0;
  const hasResults = subsVisible || kbVisible;
  const showDrop = openDrop && trimmed.length >= 2;
  const scopeActive = scope.abon || scope.kb;

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
    if (!s || !scopeActive) return;
    setOpenDrop(false);
    if (scope.kb) {
      const kh = MOCK_KB.filter((k) => k.t.toLowerCase().includes(s) || k.k.includes(s));
      if (kh.length) {
        showKbCard(kh[0]);
        return;
      }
    }
    if (scope.abon && subs.length) pickSubscriber(subs[0]);
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
        <div className="sr-scope" role="group" aria-label="Область поиска">
          <button
            type="button"
            className={`sr-scope-btn sr-scope-btn--kb${scope.kb ? " on" : ""}`}
            aria-pressed={scope.kb}
            title={scope.kb ? "Искать в базе знаний" : "Не искать в базе знаний"}
            onClick={() => toggleScope("kb")}
          >
            БД
          </button>
          <button
            type="button"
            className={`sr-scope-btn sr-scope-btn--ab${scope.abon ? " on" : ""}`}
            aria-pressed={scope.abon}
            title={scope.abon ? "Искать абонентов" : "Не искать абонентов"}
            onClick={() => toggleScope("abon")}
          >
            Абон
          </button>
        </div>
        {loading ? <span className="sr-spinner" aria-hidden /> : null}

        <div className={`sd sr-drop ${showDrop ? "vis" : ""}`} role="listbox">
          {!scopeActive ? <div className="sr-empty">Включите БД или Абон</div> : null}

          {scopeActive && searchError ? <div className="sr-empty sr-error">{searchError}</div> : null}

          {scopeActive && !searchError && loading && !hasResults ? (
            <div className="sr-empty">Ищем…</div>
          ) : null}

          {scopeActive && !searchError && !loading && trimmed.length >= 2 && !hasResults ? (
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
