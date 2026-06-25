import { Link } from "react-router-dom";
import {
  kbQuizStatusLabel,
  kbReadStatusLabel,
  type KbArticleListItem,
} from "@/api/kb";

export function KbArticleStatusBadges({ article }: { article: KbArticleListItem }) {
  const readLabel = kbReadStatusLabel(article.read_status);
  const quizLabel = kbQuizStatusLabel(article);

  return (
    <div className="kb-badges">
      <span className={`kb-badge kb-badge--read kb-badge--read-${article.read_status}`}>
        {readLabel}
      </span>
      {quizLabel ? (
        <span
          className={`kb-badge kb-badge--quiz kb-badge--quiz-${article.quiz_status}`}
        >
          {quizLabel}
        </span>
      ) : null}
    </div>
  );
}

export function KbArticleRow({ article }: { article: KbArticleListItem }) {
  return (
    <Link to={`/kb/${article.slug}`} className="kb-article-row">
      <span className="kb-article-row__title">{article.title}</span>
      <KbArticleStatusBadges article={article} />
    </Link>
  );
}
