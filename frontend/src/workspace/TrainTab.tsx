const TRAIN_CARDS = [
  {
    icon: "🎧",
    title: "Стандарты общения",
    desc: "Скрипты, приветствия, завершение диалога",
    duration: "15 мин · видео",
    stub: "Откроется видео «Стандарты общения с абонентами»",
  },
  {
    icon: "🔧",
    title: "Диагностика подключения",
    desc: "Как быстро найти причину проблемы",
    duration: "12 мин · видео",
    stub: "Откроется видео «Диагностика подключения»",
  },
  {
    icon: "📊",
    title: "Тарифные планы и опции",
    desc: "Безлимиты, турбо-кнопка, заморозка",
    duration: "10 мин · чтение",
    stub: "Откроется статья «Тарифные планы»",
  },
  {
    icon: "📝",
    title: "Итоговое тестирование",
    desc: "Проверка знаний после обучения",
    duration: "20 мин · тест",
    stub: "Откроется тестирование",
  },
] as const;

export default function TrainTab() {
  return (
    <div className="tp on train-page">
      <div className="pg">
        <div className="train-page__title">Обучение оператора</div>
        <div className="train-grid">
          {TRAIN_CARDS.map((card) => (
            <button
              key={card.title}
              type="button"
              className="train-card"
              onClick={() => window.alert(card.stub)}
            >
              <div className="train-icon" aria-hidden>
                {card.icon}
              </div>
              <div className="train-title">{card.title}</div>
              <div className="train-desc">{card.desc}</div>
              <div className="train-duration">{card.duration}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
