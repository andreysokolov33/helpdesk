import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SubscriberSearchField from "@/components/SubscriberSearchField";
import type { SubscriberSearchHit } from "@/api/search";
import { registerCall } from "@/api/tracker";

export default function CallTab() {
  const navigate = useNavigate();
  const [desc, setDesc] = useState("");
  const [subscriber, setSubscriber] = useState<SubscriberSearchHit | null>(null);
  const [unknownSubscriber, setUnknownSubscriber] = useState(false);
  const [callerName, setCallerName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    const body = desc.trim();
    if (!body) {
      setError("Опишите, что говорит клиент");
      return;
    }
    if (!unknownSubscriber && !subscriber) {
      setError("Выберите абонента или отметьте «Не удалось определить»");
      return;
    }
    if (unknownSubscriber && !callerName.trim()) {
      setError("Укажите, как представился клиент");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const result = await registerCall({
        body,
        subscriber_unknown: unknownSubscriber,
        user_id: unknownSubscriber ? null : subscriber!.id,
        caller_name: unknownSubscriber ? callerName.trim() : null,
        station_id: unknownSubscriber ? null : subscriber!.station_id ?? null,
        hotspot_id: unknownSubscriber ? null : subscriber!.hotspot_id ?? null,
      });
      navigate(`/tickets/${result.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Не удалось создать заявку");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="tp on call-page">
      <div className="call-page__inner">
        <header className="call-page__header">
          <div className="call-page__icon" aria-hidden>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path
                d="M6.5 4.5h3l2 4-2.5 1.5a11 11 0 005.5 5.5L15 13l4 2v3a2 2 0 01-2 2A15 15 0 014 6.5a2 2 0 012-2z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <h1 className="call-page__title">
              Регистрация <span>звонка</span>
            </h1>
            <p className="call-page__lead">
              Входящие на 8-800. Категорию и SLA выберете при завершении обращения.
            </p>
          </div>
        </header>

        <div className="call-card">
          <section className="call-step">
            <div className="call-step__head-row">
              <div className="call-step__head">
                <span className="call-step__num">1</span>
                <span className="call-step__label">Абонент</span>
              </div>
              <label className="call-unknown">
                <input
                  type="checkbox"
                  checked={unknownSubscriber}
                  onChange={(e) => {
                    setUnknownSubscriber(e.target.checked);
                    if (e.target.checked) setSubscriber(null);
                    setError(null);
                  }}
                />
                <span>Не удалось определить</span>
              </label>
            </div>

            {unknownSubscriber ? (
              <div className="call-field">
                <label className="call-field__lbl" htmlFor="caller-name">
                  Как представился клиент <span className="call-req">*</span>
                </label>
                <input
                  id="caller-name"
                  className="call-input"
                  value={callerName}
                  onChange={(e) => setCallerName(e.target.value)}
                  placeholder="Иванов Иван, ООО «Пример»…"
                  autoComplete="name"
                  required
                />
              </div>
            ) : (
              <SubscriberSearchField
                selected={subscriber}
                onSelect={setSubscriber}
                disabled={unknownSubscriber}
              />
            )}
          </section>

          <section className="call-step">
            <div className="call-step__head">
              <span className="call-step__num">2</span>
              <span className="call-step__label">Что говорит клиент</span>
            </div>
            <textarea
              className="call-textarea"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              placeholder="С утра нет интернета, индикатор на роутере мигает красным…"
              rows={5}
            />
          </section>

          {error ? <div className="call-error" role="alert">{error}</div> : null}

          <footer className="call-card__footer">
            <button type="button" className="tb call-btn-sec" onClick={() => navigate("/")} disabled={submitting}>
              Отмена
            </button>
            <button type="button" className="call-btn-primary" onClick={submit} disabled={submitting}>
              {submitting ? "Создаём…" : "Создать заявку"}
            </button>
          </footer>
        </div>
      </div>
    </div>
  );
}
