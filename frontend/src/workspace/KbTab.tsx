import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchKbHome,
  searchKbArticles,
  type KbArticleListItem,
  type KbCategorySection,
} from "@/api/kb";
import { KbArticleRow } from "@/workspace/KbArticleStatusBadges";

const SEARCH_DEBOUNCE_MS = 300;
const MIN_SEARCH_LEN = 2;

function groupSearchResults(items: KbArticleListItem[]): KbCategorySection[] {
  const map = new Map<number, KbCategorySection>();
  const order: number[] = [];
  for (const item of items) {
    if (!map.has(item.category_id)) {
      map.set(item.category_id, {
        id: item.category_id,
        title: item.category_title,
        slug: null,
        sort_order: 0,
        articles: [],
      });
      order.push(item.category_id);
    }
    map.get(item.category_id)!.articles.push(item);
  }
  return order.map((id) => map.get(id)!);
}

export default function KbTab() {
  const [categories, setCategories] = useState<KbCategorySection[]>([]);
  const [totalArticles, setTotalArticles] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const loadHome = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchKbHome();
      setCategories(data.categories);
      setTotalArticles(data.total_articles);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить базу знаний");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHome();
  }, [loadHome]);

  useEffect(() => {
    const q = query.trim();
    if (q.length < MIN_SEARCH_LEN) {
      setSearchError(null);
      setSearching(false);
      if (!q) void loadHome();
      return;
    }

    setSearching(true);
    setSearchError(null);
    const timer = window.setTimeout(() => {
      void searchKbArticles(q)
        .then((res) => {
          setCategories(groupSearchResults(res.items));
          setTotalArticles(res.items.length);
        })
        .catch((e) => {
          setSearchError(e instanceof Error ? e.message : "Ошибка поиска");
        })
        .finally(() => setSearching(false));
    }, SEARCH_DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
  }, [query, loadHome]);

  const isSearchActive = query.trim().length >= MIN_SEARCH_LEN;
  const visibleCount = useMemo(
    () => categories.reduce((n, c) => n + c.articles.length, 0),
    [categories],
  );

  return (
    <div className="tp on kb-page">
      <div className="pg">
        <div className="kb-page__head">
          <div className="kb-page__title">База знаний</div>
          <div className="kb-page__count">
            {isSearchActive ? `Найдено: ${visibleCount}` : `Статей: ${totalArticles}`}
          </div>
        </div>

        <div className="kb-toolbar">
          <input
            type="search"
            className="kb-search"
            placeholder="Поиск по заголовку и содержимому…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Поиск по базе знаний"
          />
          {searching ? <span className="kb-search-hint">Поиск…</span> : null}
        </div>

        {error ? <div className="kb-error">{error}</div> : null}
        {searchError ? <div className="kb-error">{searchError}</div> : null}

        {loading && !isSearchActive ? (
          <div className="kb-muted">Загрузка…</div>
        ) : null}

        {!loading && visibleCount === 0 ? (
          <div className="kb-muted">
            {isSearchActive ? "Ничего не найдено" : "Статьи пока не опубликованы"}
          </div>
        ) : null}

        {categories.map((sec) =>
          sec.articles.length > 0 ? (
            <section key={sec.id} className="kbsec">
              <h2 className="kbst">{sec.title}</h2>
              <div className="kb-article-list">
                {sec.articles.map((article) => (
                  <KbArticleRow key={article.id} article={article} />
                ))}
              </div>
            </section>
          ) : null,
        )}
      </div>
    </div>
  );
}
