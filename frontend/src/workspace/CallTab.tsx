import { useCallback, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import SubscriberSearchField from "@/components/SubscriberSearchField";
import PartnerTicketSuccessModal from "@/components/PartnerTicketSuccessModal";
import type { SubscriberSearchHit } from "@/api/search";
import { registerCall, type CallConnectionKind, type ConnectionLeadPayload } from "@/api/tracker";
import { maskRuPhoneInput, normalizeRuPhone } from "@/utils/phone";

type CallLocationState = { returnTo?: string };

const EMPTY_LEAD: ConnectionLeadPayload = {
  full_name: "",
  address: "",
  phone: "+7",
  potential_subscribers: null,
  sees_network: null,
  plans_new_station: null,
  notes: "",
};

type ModeCard = {
  id: CallConnectionKind;
  title: string;
  hint: string;
};

const MODE_CARDS: ModeCard[] = [
  {
    id: "existing",
    title: "Абонент в базе",
    hint: "Поиск по ФИО, логину или ID — обычное обращение",
  },
  {
    id: "new_subscriber",
    title: "Новый абонент",
    hint: "Не может зарегистрироваться — помощь с подключением",
  },
  {
    id: "new_partner",
    title: "Новый партнёр",
    hint: "Хочет поставить станцию — заявка менеджеру",
  },
];

function BoolToggle({
  value,
  onChange,
  yesLabel = "Да",
  noLabel = "Нет",
}: {
  value: boolean | null;
  onChange: (v: boolean) => void;
  yesLabel?: string;
  noLabel?: string;
}) {
  return (
    <div className="call-bool" role="group">
      <button
        type="button"
        className={`call-bool__btn${value === true ? " on" : ""}`}
        onClick={() => onChange(true)}
      >
        {yesLabel}
      </button>
      <button
        type="button"
        className={`call-bool__btn${value === false ? " on" : ""}`}
        onClick={() => onChange(false)}
      >
        {noLabel}
      </button>
    </div>
  );
}

export default function CallTab() {
  const navigate = useNavigate();
  const location = useLocation();

  function cancel() {
    const returnTo = (location.state as CallLocationState | null)?.returnTo;
    if (returnTo) {
      navigate(returnTo);
      return;
    }
    if (location.key !== "default") {
      navigate(-1);
      return;
    }
    navigate("/");
  }

  const [mode, setMode] = useState<CallConnectionKind>("existing");
  const [desc, setDesc] = useState("");
  const [subscriber, setSubscriber] = useState<SubscriberSearchHit | null>(null);
  const [lead, setLead] = useState<ConnectionLeadPayload>({ ...EMPTY_LEAD });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [partnerTicketId, setPartnerTicketId] = useState<number | null>(null);

  const goHome = useCallback(() => {
    setPartnerTicketId(null);
    navigate("/");
  }, [navigate]);

  function switchMode(next: CallConnectionKind) {
    setMode(next);
    setError(null);
    if (next !== "existing") {
      setSubscriber(null);
      setDesc("");
    }
    if (next === "existing") {
      setLead({ ...EMPTY_LEAD });
    } else {
      setLead({
        ...EMPTY_LEAD,
        sees_network: next === "new_subscriber" ? null : undefined,
        plans_new_station: next === "new_partner" ? null : undefined,
      });
    }
  }

  function patchLead<K extends keyof ConnectionLeadPayload>(key: K, value: ConnectionLeadPayload[K]) {
    setLead((prev) => ({ ...prev, [key]: value }));
  }

  async function submit() {
    setError(null);

    if (mode === "existing") {
      const body = desc.trim();
      if (!subscriber) {
        setError("Выберите абонента");
        return;
      }
      if (!body) {
        setError("Опишите, что говорит клиент");
        return;
      }
      setSubmitting(true);
      try {
        const result = await registerCall({
          connection_kind: "existing",
          body,
          user_id: subscriber.id,
          station_id: subscriber.station_id ?? null,
          hotspot_id: subscriber.hotspot_id ?? null,
        });
        navigate(`/tickets/${result.id}`);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Не удалось создать заявку");
      } finally {
        setSubmitting(false);
      }
      return;
    }

    const fullName = lead.full_name.trim();
    const address = lead.address.trim();
    const phone = lead.phone.trim();
    if (!fullName) {
      setError("Укажите ФИО");
      return;
    }
    if (!address) {
      setError("Укажите адрес");
      return;
    }
    const phoneNorm = normalizeRuPhone(phone);
    if (!phoneNorm) {
      setError("Укажите телефон в формате +7XXXXXXXXXX");
      return;
    }
    if (mode === "new_subscriber" && lead.sees_network == null) {
      setError("Укажите, видит ли клиент сеть");
      return;
    }
    if (mode === "new_partner" && lead.plans_new_station == null) {
      setError("Укажите, планирует ли партнёр новую станцию");
      return;
    }
    if (mode === "new_partner") {
      const count = lead.potential_subscribers;
      if (count == null || count < 0) {
        setError("Укажите число потенциальных абонентов");
        return;
      }
    }

    setSubmitting(true);
    try {
      const result = await registerCall({
        connection_kind: mode,
        lead: {
          full_name: fullName,
          address,
          phone: phoneNorm,
          potential_subscribers:
            mode === "new_partner" ? Math.max(0, lead.potential_subscribers ?? 0) : undefined,
          sees_network: mode === "new_subscriber" ? lead.sees_network : undefined,
          plans_new_station: mode === "new_partner" ? lead.plans_new_station : undefined,
          notes: lead.notes?.trim() || null,
        },
      });
      if (mode === "new_partner") {
        setPartnerTicketId(result.id);
        setLead({ ...EMPTY_LEAD });
        setMode("existing");
      } else {
        navigate(`/tickets/${result.id}`);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Не удалось создать заявку");
    } finally {
      setSubmitting(false);
    }
  }

  const step2Label =
    mode === "existing"
      ? "Что говорит клиент"
      : mode === "new_subscriber"
        ? "Анкета нового абонента"
        : "Анкета нового партнёра";

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
              Входящие на 8-800. Выберите тип обращения — категорию и SLA укажете при завершении.
            </p>
          </div>
        </header>

        <div className="call-card">
          <section className="call-step">
            <div className="call-step__head">
              <span className="call-step__num">1</span>
              <span className="call-step__label">Тип обращения</span>
            </div>
            <div className="call-mode-grid" role="radiogroup" aria-label="Тип обращения">
              {MODE_CARDS.map((card) => (
                <button
                  key={card.id}
                  type="button"
                  role="radio"
                  aria-checked={mode === card.id}
                  className={`call-mode-card${mode === card.id ? " call-mode-card--on" : ""}${
                    card.id === "new_partner" ? " call-mode-card--partner" : ""
                  }`}
                  onClick={() => switchMode(card.id)}
                >
                  <span className="call-mode-card__title">{card.title}</span>
                  <span className="call-mode-card__hint">{card.hint}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="call-step">
            <div className="call-step__head">
              <span className="call-step__num">2</span>
              <span className="call-step__label">{step2Label}</span>
            </div>

            {mode === "existing" ? (
              <>
                <SubscriberSearchField selected={subscriber} onSelect={setSubscriber} />
                <div className="call-field" style={{ marginTop: 14 }}>
                  <label className="call-field__lbl" htmlFor="call-desc">
                    Суть обращения <span className="call-req">*</span>
                  </label>
                  <textarea
                    id="call-desc"
                    className="call-textarea"
                    value={desc}
                    onChange={(e) => setDesc(e.target.value)}
                    placeholder="С утра нет интернета, индикатор на роутере мигает красным…"
                    rows={5}
                  />
                </div>
              </>
            ) : (
              <div className="call-lead-form">
                <div className="call-lead-form__row">
                  <div className="call-field">
                    <label className="call-field__lbl" htmlFor="lead-name">
                      ФИО <span className="call-req">*</span>
                    </label>
                    <input
                      id="lead-name"
                      className="call-input"
                      value={lead.full_name}
                      onChange={(e) => patchLead("full_name", e.target.value)}
                      placeholder="Иванов Иван Иванович"
                      autoComplete="name"
                    />
                  </div>
                  <div className="call-field">
                    <label className="call-field__lbl" htmlFor="lead-phone">
                      Телефон <span className="call-req">*</span>
                    </label>
                    <input
                      id="lead-phone"
                      className="call-input"
                      type="tel"
                      inputMode="numeric"
                      value={lead.phone}
                      onChange={(e) => patchLead("phone", maskRuPhoneInput(e.target.value))}
                      onFocus={() => {
                        if (!lead.phone.trim()) patchLead("phone", "+7");
                      }}
                      placeholder="+7XXXXXXXXXX"
                      autoComplete="tel"
                      maxLength={12}
                    />
                  </div>
                </div>
                <div className="call-field">
                  <label className="call-field__lbl" htmlFor="lead-address">
                    Адрес <span className="call-req">*</span>
                  </label>
                  <input
                    id="lead-address"
                    className="call-input"
                    value={lead.address}
                    onChange={(e) => patchLead("address", e.target.value)}
                    placeholder="Населённый пункт, улица, дом…"
                  />
                </div>
                {mode === "new_subscriber" ? (
                  <div className="call-field">
                    <span className="call-field__lbl">
                      Видит сеть <span className="call-req">*</span>
                    </span>
                    <BoolToggle
                      value={lead.sees_network ?? null}
                      onChange={(v) => patchLead("sees_network", v)}
                    />
                  </div>
                ) : (
                  <div className="call-lead-form__row call-lead-form__row--split">
                    <div className="call-field">
                      <span className="call-field__lbl">
                        Планирует новую станцию <span className="call-req">*</span>
                      </span>
                      <BoolToggle
                        value={lead.plans_new_station ?? null}
                        onChange={(v) => patchLead("plans_new_station", v)}
                      />
                    </div>
                    <div className="call-field">
                      <label className="call-field__lbl" htmlFor="lead-count">
                        Потенциальных абонентов <span className="call-req">*</span>
                      </label>
                      <input
                        id="lead-count"
                        className="call-input call-input--num"
                        type="number"
                        min={0}
                        max={99999}
                        value={lead.potential_subscribers ?? ""}
                        onChange={(e) => {
                          const raw = e.target.value;
                          patchLead(
                            "potential_subscribers",
                            raw === "" ? null : Math.max(0, parseInt(raw, 10) || 0),
                          );
                        }}
                        placeholder="0"
                      />
                    </div>
                  </div>
                )}
                <div className="call-field">
                  <label className="call-field__lbl" htmlFor="lead-notes">
                    Дополнительно
                  </label>
                  <textarea
                    id="lead-notes"
                    className="call-textarea call-textarea--compact"
                    value={lead.notes ?? ""}
                    onChange={(e) => patchLead("notes", e.target.value)}
                    placeholder="Уточнения от звонящего…"
                    rows={3}
                  />
                </div>
              </div>
            )}
          </section>

          {error ? (
            <div className="call-error" role="alert">
              {error}
            </div>
          ) : null}

          <footer className="call-card__footer">
            <button type="button" className="tb call-btn-sec" onClick={cancel} disabled={submitting}>
              Отмена
            </button>
            <button type="button" className="call-btn-primary" onClick={submit} disabled={submitting}>
              {submitting ? "Создаём…" : "Создать заявку"}
            </button>
          </footer>
        </div>
      </div>

      <PartnerTicketSuccessModal
        open={partnerTicketId != null}
        ticketId={partnerTicketId ?? 0}
        onGoHome={goHome}
      />
    </div>
  );
}
