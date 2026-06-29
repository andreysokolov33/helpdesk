import { useEffect, useState } from "react";
import {
  searchKbArticles,
  type KbArticleListItem,
} from "@/api/kb";

const SEARCH_DEBOUNCE_MS = 300;
const MIN_SEARCH_LEN = 2;

type Props = {
  onOpenArticle: (slug: string) => void;
};

export default function TicketKbSearch({ onOpenArticle }: Props) {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [results, setResults] = useState<KbArticleListItem[]>([]);

  useEffect(() => {
    const q = query.trim();
    if (q.length < MIN_SEARCH_LEN) {
      setSearchError(null);
      setSearching(false);
      setResults([]);
      return;
    }

    setSearching(true);
    setSearchError(null);
    const timer = window.setTimeout(() => {
      void searchKbArticles(q)
        .then((res) => setResults(res.items))
        .catch((e) => {
          setSearchError(e instanceof Error ? e.message : "Ошибка поиска");
          setResults([]);
        })
        .finally(() => setSearching(false));
    }, SEARCH_DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
  }, [query]);

  const isSearchActive = query.trim().length >= MIN_SEARCH_LEN;

  return (
    <div className="tk-cc-kb-search">
      <input
        type="search"
        className="tk-cc-kb-search__input"
        placeholder="Поиск решений…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Поиск по базе знаний"
      />
      {searching ? <div className="tk-cc-kb-search__hint">Поиск…</div> : null}
      {searchError ? <div className="tk-cc-kb-search__error">{searchError}</div> : null}
      {!isSearchActive ? (
        <p className="tk-cc-kb-search__note">Введите не менее 2 символов для поиска по статьям</p>
      ) : null}
      {isSearchActive && !searching && results.length === 0 && !searchError ? (
        <p className="tk-cc-kb-search__note">Ничего не найдено</p>
      ) : null}
      {results.length > 0 ? (
        <div className="tk-cc-kb-search__list" role="listbox" aria-label="Результаты поиска">
          {results.map((article) => (
            <button
              key={article.id}
              type="button"
              role="option"
              className="tk-cc-kb-search__item"
              onClick={() => onOpenArticle(article.slug)}
            >
              <span className="tk-cc-kb-search__item-title">{article.title}</span>
              <span className="tk-cc-kb-search__item-cat">{article.category_title}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
