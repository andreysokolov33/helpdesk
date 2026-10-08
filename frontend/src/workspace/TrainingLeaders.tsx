import type { TrainingLeaderItem, TrainingLeaders as TrainingLeadersData } from "@/api/training";
import { formatAnswerRatio, pluralRu } from "@/workspace/trainingFormat";

type Props = {
  data: TrainingLeadersData | null;
  loading: boolean;
  error: string | null;
};

const PODIUM_ORDER = [1, 0, 2]; // визуально: 2-е, 1-е, 3-е место

function LowDataBadge({ item, threshold }: { item: TrainingLeaderItem; threshold: number }) {
  if (!item.low_data) return null;
  return (
    <span
      className="trn-lowdata"
      title={`Меньше ${threshold} ответов — рейтинг пока сильно сглажен к среднему`}
    >
      мало данных
    </span>
  );
}

function coverageLabel(n: number): string {
  return `${n} ${pluralRu(n, "вопрос", "вопроса", "вопросов")}`;
}

export default function TrainingLeaders({ data, loading, error }: Props) {
  if (loading) {
    return (
      <div className="card stats-card trn-leaders" aria-busy="true">
        <div className="stats-card__title">Лидеры</div>
        <div className="trn-podium">
          {PODIUM_ORDER.map((i) => (
            <div key={i} className={`trn-podium__spot trn-podium__spot--${i + 1} trn-skeleton`} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card stats-card trn-leaders">
        <div className="stats-card__title">Лидеры</div>
        <div className="trn-state trn-state--error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const top = data.items.slice(0, 3);
  const rest = data.items.slice(3);
  const formulaHint = `Рейтинг = (верные + ${data.k}·p0) / (ответы + ${data.k}), где p0 = ${Math.round(
    data.p0_percent,
  )}% — средняя точность команды за период. Так 1 случайный верный ответ не обгонит 98 из 100.`;

  return (
    <div className="card stats-card trn-leaders">
      <div className="trn-leaders__head">
        <div className="stats-card__title">Лидеры</div>
        <span className="trn-leaders__formula" data-tip={formulaHint} tabIndex={0} aria-label={formulaHint}>
          Как считается рейтинг
        </span>
      </div>

      {data.items.length === 0 ? (
        <div className="trn-state">За выбранный период никто из сотрудников не тренировался.</div>
      ) : (
        <>
          <ol className="trn-podium" aria-label="Тройка лидеров">
            {PODIUM_ORDER.map((idx) => {
              const item = top[idx];
              if (!item) return <li key={`empty-${idx}`} className="trn-podium__spot trn-podium__spot--empty" aria-hidden />;
              return (
                <li key={item.operator_id} className={`trn-podium__spot trn-podium__spot--${item.rank}`}>
                  <span className={`trn-medal trn-medal--${item.rank}`} aria-label={`${item.rank} место`}>
                    {item.rank}
                  </span>
                  <span className="trn-podium__name" title={item.operator_name}>
                    {item.operator_name}
                  </span>
                  <span className="trn-podium__score">
                    {Math.round(item.score_percent)}
                    <span className="trn-podium__score-cap">рейтинг</span>
                  </span>
                  <span className="trn-podium__raw">
                    {formatAnswerRatio(item.correct, item.total)} · {Math.round(item.raw_percent)}%
                  </span>
                  <span className="trn-podium__cov">Охват: {coverageLabel(item.coverage)}</span>
                  <LowDataBadge item={item} threshold={data.low_data_threshold} />
                  <span className="trn-podium__step" aria-hidden />
                </li>
              );
            })}
          </ol>

          {rest.length > 0 ? (
            <ol className="trn-ranklist" start={4}>
              {rest.map((item) => (
                <li key={item.operator_id} className="trn-ranklist__row">
                  <span className="stats-rank">{item.rank}</span>
                  <span className="trn-ranklist__name" title={item.operator_name}>
                    {item.operator_name}
                    <LowDataBadge item={item} threshold={data.low_data_threshold} />
                  </span>
                  <span className="trn-ranklist__raw">
                    {formatAnswerRatio(item.correct, item.total)} · {Math.round(item.raw_percent)}%
                  </span>
                  <span className="trn-ranklist__cov">{coverageLabel(item.coverage)}</span>
                  <span className="trn-ranklist__score" title="Рейтинг">
                    {Math.round(item.score_percent)}
                  </span>
                </li>
              ))}
            </ol>
          ) : null}
        </>
      )}
    </div>
  );
}
