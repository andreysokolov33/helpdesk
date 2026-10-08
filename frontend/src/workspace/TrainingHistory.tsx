import { useCallback, useEffect, useState } from "react";
import { fetchMyTrainingSessions, type TrainingMySessions } from "@/api/training";
import { quizScoreClass } from "@/api/statsQuizTraining";
import TrainingSessionsTable from "@/workspace/TrainingSessionsTable";
import { formatTrainingDuration } from "@/workspace/trainingFormat";

const PER_PAGE = 20;

type Props = {
  onStartTraining: () => void;
};

export default function TrainingHistory({ onStartTraining }: Props) {
  const [data, setData] = useState<TrainingMySessions | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchMyTrainingSessions(1, PER_PAGE));
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : "Не удалось загрузить историю");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function loadMore() {
    if (!data || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await fetchMyTrainingSessions(data.page + 1, PER_PAGE);
      setData({ ...page, items: [...data.items, ...page.items] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить историю");
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading) {
    return (
      <div className="trn-history" aria-busy="true">
        <div className="stats-metrics stats-metrics--placeholder trn-kpis">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="stats-m-card stats-m-card--skeleton" />
          ))}
        </div>
        <div className="card trn-skeleton trn-skeleton--table" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="trn-state trn-state--error">
        <p>{error}</p>
        <button type="button" className="kb-quiz-btn-secondary" onClick={() => void load()}>
          Повторить
        </button>
      </div>
    );
  }

  if (!data || data.total === 0) {
    return (
      <div className="trn-empty">
        <div className="trn-empty__title">Тренировок пока нет</div>
        <p className="trn-empty__text">Здесь появятся ваши сессии: сколько ответов, точность и время.</p>
        <button type="button" className="trn-btn trn-btn--primary" onClick={onStartTraining}>
          Начать тренировку
        </button>
      </div>
    );
  }

  const t = data.totals;
  const hasMore = data.items.length < data.total;

  return (
    <div className="trn-history">
      <div className="stats-metrics trn-kpis">
        <div className="stats-m-card">
          <div className="stats-m-label">Точность за всё время</div>
          <div className={`stats-m-val ${quizScoreClass(t.score_percent)}`}>{Math.round(t.score_percent)}%</div>
        </div>
        <div className="stats-m-card">
          <div className="stats-m-label">Сессий</div>
          <div className="stats-m-val">{t.sessions_count}</div>
        </div>
        <div className="stats-m-card">
          <div className="stats-m-label">Ответов</div>
          <div className="stats-m-val">
            {t.total_answers}
            <span className="trn-kpi-sub"> · верно {t.correct_count}</span>
          </div>
        </div>
        <div className="stats-m-card">
          <div className="stats-m-label">Время в тренажёре</div>
          <div className="stats-m-val">{formatTrainingDuration(t.total_duration_sec)}</div>
        </div>
      </div>

      <div className="card stats-card">
        <div className="stats-card__title">Мои тренировки</div>
        <TrainingSessionsTable items={data.items} />
        {error ? <div className="kb-quiz-inline-error">{error}</div> : null}
        {hasMore ? (
          <div className="trn-more">
            <button type="button" className="kb-quiz-btn-secondary" onClick={() => void loadMore()} disabled={loadingMore}>
              {loadingMore ? "Загрузка…" : `Показать ещё (${data.total - data.items.length})`}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
