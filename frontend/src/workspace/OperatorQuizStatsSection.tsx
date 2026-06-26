import { useState } from "react";
import {
  fetchOperatorQuizStats,
  type OperatorQuizStats,
} from "@/api/operatorQuizStats";
import { quizScoreBarStyle } from "@/workspace/dailyQuizScore";
import QuizAttemptDotChain from "@/workspace/QuizAttemptDotChain";
import QuizAttemptReviewModal from "@/workspace/QuizAttemptReviewModal";
import { useEffect } from "react";

function OverallCard({
  label,
  stats,
  extra,
}: {
  label: string;
  stats: OperatorQuizStats["kb_overall"];
  extra?: string;
}) {
  return (
    <div className="op-quiz-overall-card">
      <div className="op-quiz-overall-label">{label}</div>
      <div className="op-quiz-overall-value">{stats.avg_score_percent.toFixed(1)}%</div>
      <div className="op-quiz-overall-bar" aria-hidden>
        <div className="op-quiz-overall-bar__fill" style={quizScoreBarStyle(stats.avg_score_percent)} />
      </div>
      <div className="op-quiz-overall-hint">
        Попыток: {stats.attempts_count} · сдано: {stats.passed_count}
        {extra ? ` · ${extra}` : ""}
      </div>
    </div>
  );
}

export default function OperatorQuizStatsSection() {
  const [stats, setStats] = useState<OperatorQuizStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedAttemptId, setSelectedAttemptId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchOperatorQuizStats()
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка загрузки");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="card op-card">
        <h2 className="op-section-title">Тестирование</h2>
        <div className="op-quiz-muted">Загрузка…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card op-card">
        <h2 className="op-section-title">Тестирование</h2>
        <div className="op-error">{error}</div>
      </div>
    );
  }

  if (!stats?.eligible) return null;

  const kbExtra =
    stats.kb_overall.articles_with_quiz != null
      ? `статей сдано ${stats.kb_overall.articles_passed ?? 0} из ${stats.kb_overall.articles_with_quiz}`
      : undefined;

  return (
    <>
      <div className="card op-card op-quiz-card">
        <div className="op-section-head">
          <h2 className="op-section-title">Тестирование</h2>
        </div>

        <div className="op-quiz-overall-grid">
          <OverallCard label="База знаний (средний балл)" stats={stats.kb_overall} extra={kbExtra} />
          <OverallCard label="Ежедневные тесты (средний балл)" stats={stats.daily_overall} />
        </div>

        {stats.categories.length > 0 ? (
          <div className="op-quiz-block">
            <h3 className="op-quiz-block-title">Успеваемость по категориям</h3>
            <div className="op-quiz-categories">
              {stats.categories.map((cat) => (
                <div key={cat.category_id} className="op-quiz-cat">
                  <div className="op-quiz-cat-head">
                    <span className="op-quiz-cat-title">{cat.category_title}</span>
                    <span className="op-quiz-cat-pct">{cat.avg_score_percent.toFixed(0)}%</span>
                  </div>
                  <div className="op-quiz-cat-bar" aria-hidden>
                    <div className="op-quiz-cat-bar__fill" style={quizScoreBarStyle(cat.avg_score_percent)} />
                  </div>
                  <div className="op-quiz-cat-meta">
                    Сдано статей: {cat.articles_passed}/{cat.articles_with_quiz}
                    {cat.articles_attempted > 0 ? ` · попыток: ${cat.articles_attempted}` : ""}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div className="op-quiz-block">
          <h3 className="op-quiz-block-title">Ежедневные тесты</h3>
          <p className="op-quiz-chain-hint">Нажмите на дату — откроется просмотр ваших ответов</p>
          <QuizAttemptDotChain
            items={stats.daily_attempts}
            selectedId={selectedAttemptId}
            onSelect={setSelectedAttemptId}
            emptyMessage="Пока нет завершённых ежедневных тестов"
          />
        </div>

        <div className="op-quiz-block">
          <h3 className="op-quiz-block-title">Тесты по статьям базы знаний</h3>
          <p className="op-quiz-chain-hint">Последние попытки — от новых к старым</p>
          <QuizAttemptDotChain
            items={stats.kb_attempts}
            selectedId={selectedAttemptId}
            onSelect={setSelectedAttemptId}
            emptyMessage="Пока нет завершённых тестов по статьям"
          />
        </div>
      </div>

      <QuizAttemptReviewModal
        attemptId={selectedAttemptId}
        onClose={() => setSelectedAttemptId(null)}
      />
    </>
  );
}
