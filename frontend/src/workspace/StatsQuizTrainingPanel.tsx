import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  quizScoreClass,
  type QuizTrainingDashboard,
  type QuizTrainingOperatorRow,
} from "@/api/statsQuizTraining";
import { quizScoreBarStyle } from "@/workspace/dailyQuizScore";

type Props = {
  operatorId: number | "all";
  onSelectOperator: (id: number) => void;
  data: QuizTrainingDashboard;
  expandedId: number | null;
  onExpandedIdChange: (id: number | null) => void;
};

function formatPercent(v: number): string {
  return `${v.toFixed(0)}%`;
}

function OperatorDetailPanel({
  detail,
  dateFrom,
  dateTo,
}: {
  detail: NonNullable<QuizTrainingDashboard["operator_detail"]>;
  dateFrom: string;
  dateTo: string;
}) {
  const weakCategories = [...detail.categories]
    .filter((c) => c.articles_attempted > 0)
    .sort((a, b) => a.avg_score_percent - b.avg_score_percent);

  return (
    <div className="stats-quiz-detail">
      <div className="stats-quiz-detail__head">
        <h3 className="stats-quiz-detail__title">{detail.operator_name}</h3>
        <p className="stats-quiz-detail__sub">
          Подробная статистика · ежедневные тесты за период {dateFrom} — {dateTo}
        </p>
      </div>

      <div className="stats-quiz-detail__grid">
        <div className="stats-quiz-mini-card">
          <div className="stats-quiz-mini-label">База знаний</div>
          <div className={quizScoreClass(detail.kb_overall.avg_score_percent)}>
            {formatPercent(detail.kb_overall.avg_score_percent)}
          </div>
          <div className="stats-quiz-mini-hint">
            Статей сдано: {detail.kb_overall.articles_passed ?? 0} /{" "}
            {detail.kb_overall.articles_with_quiz ?? 0}
          </div>
        </div>
        <div className="stats-quiz-mini-card">
          <div className="stats-quiz-mini-label">Ежедневные тесты (период)</div>
          <div className={quizScoreClass(detail.daily_overall.avg_score_percent)}>
            {formatPercent(detail.daily_overall.avg_score_percent)}
          </div>
          <div className="stats-quiz-mini-hint">
            Сдано: {detail.daily_overall.passed_count} / {detail.daily_overall.attempts_count}
          </div>
        </div>
      </div>

      {weakCategories.length > 0 ? (
        <div className="stats-quiz-detail__block">
          <div className="stats-card__title">Успеваемость по темам</div>
          <div className="stats-quiz-categories">
            {weakCategories.map((cat) => (
              <div key={cat.category_id} className="stats-quiz-cat">
                <div className="stats-quiz-cat__head">
                  <span>{cat.category_title}</span>
                  <span className={quizScoreClass(cat.avg_score_percent)}>
                    {formatPercent(cat.avg_score_percent)}
                  </span>
                </div>
                <div className="stats-quiz-cat__bar" aria-hidden>
                  <div
                    className="stats-quiz-cat__fill"
                    style={quizScoreBarStyle(cat.avg_score_percent)}
                  />
                </div>
                <div className="stats-quiz-cat__meta">
                  Сдано статей: {cat.articles_passed}/{cat.articles_with_quiz}
                  {cat.articles_attempted > 0 ? ` · попыток: ${cat.articles_attempted}` : ""}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {detail.weak_articles.length > 0 ? (
        <div className="stats-quiz-detail__block">
          <div className="stats-card__title">Темы, требующие дообучения</div>
          <div className="stats-table-wrap">
            <table className="dt stats-table">
              <thead>
                <tr>
                  <th>Статья</th>
                  <th>Категория</th>
                  <th style={{ textAlign: "right" }}>Балл</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {detail.weak_articles.map((a) => (
                  <tr key={a.article_id}>
                    <td>
                      {a.article_slug ? (
                        <Link to={`/kb/${a.article_slug}`} className="stats-ticket-link">
                          {a.article_title}
                        </Link>
                      ) : (
                        a.article_title
                      )}
                    </td>
                    <td>{a.category_title ?? "—"}</td>
                    <td style={{ textAlign: "right" }}>
                      <span className={quizScoreClass(a.score_percent)}>
                        {formatPercent(a.score_percent)}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`stats-status stats-status--${a.passed ? "good" : "bad"}`}
                      >
                        {a.passed ? "Сдан" : "Не сдан"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="stats-quiz-detail__empty">
          По всем пройденным статьям тесты сданы на отлично.
        </div>
      )}
    </div>
  );
}

export default function StatsQuizTrainingPanel({
  operatorId,
  onSelectOperator,
  data,
  expandedId,
  onExpandedIdChange,
}: Props) {
  const detailOperatorId = operatorId === "all" ? expandedId : operatorId;
  const showDetail = data.operator_detail && detailOperatorId != null;

  function toggleOperator(row: QuizTrainingOperatorRow) {
    if (operatorId !== "all") {
      onSelectOperator(row.operator_id);
      return;
    }
    onExpandedIdChange(expandedId === row.operator_id ? null : row.operator_id);
  }

  return (
    <>
      {operatorId === "all" ? (
        <div className="card stats-card">
          <div className="stats-card__title">Прогресс обучения команды</div>
          <div className="stats-table-wrap">
            <table className="dt stats-table">
              <thead>
                <tr>
                  <th>Сотрудник</th>
                  <th>БЗ: сдано</th>
                  <th>Балл БЗ</th>
                  <th>Ежедневные (период)</th>
                  <th>Сегодня</th>
                  <th>Слабый блок</th>
                </tr>
              </thead>
              <tbody>
                {data.operators.map((row) => (
                  <tr
                    key={row.operator_id}
                    className={
                      row.needs_attention
                        ? "stats-table__row--warn"
                        : expandedId === row.operator_id
                          ? "stats-table__row--active"
                          : ""
                    }
                  >
                    <td>
                      <button
                        type="button"
                        className={`stats-op-link${expandedId === row.operator_id ? " is-active" : ""}`}
                        onClick={() => toggleOperator(row)}
                      >
                        {row.operator_name}
                      </button>
                    </td>
                    <td>
                      {row.kb_articles_passed} / {row.kb_articles_with_quiz}
                    </td>
                    <td>
                      <span className={quizScoreClass(row.kb_avg_score_percent)}>
                        {formatPercent(row.kb_avg_score_percent)}
                      </span>
                    </td>
                    <td>
                      {row.daily_attempts_count > 0 ? (
                        <span className={quizScoreClass(row.daily_avg_score_percent)}>
                          {row.daily_passed_count}/{row.daily_attempts_count} ·{" "}
                          {formatPercent(row.daily_avg_score_percent)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      <span
                        className={`stats-status stats-status--${
                          row.today_daily_passed === true
                            ? "good"
                            : row.today_daily_passed === false
                              ? "bad"
                              : "neutral"
                        }`}
                      >
                        {row.today_daily_label}
                      </span>
                    </td>
                    <td>{row.weak_category_title ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {showDetail && data.operator_detail ? (
        <OperatorDetailPanel
          detail={data.operator_detail}
          dateFrom={data.date_from}
          dateTo={data.date_to}
        />
      ) : null}
    </>
  );
}
