import { useMemo, useState } from "react";
import DatePickerField from "@/components/DatePickerField";
import { postTrafficDetailSend } from "@/api/userProfile";

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

function toYmd(d: Date) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function defaultRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);
  return { from: toYmd(from), to: toYmd(to) };
}

function splitEmails(email: string | null, isJuridical: number): string[] {
  if (!email?.trim()) return [];
  if (isJuridical !== 2) return [email.trim()];
  return email
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean);
}

type Props = {
  userId: number;
  email: string | null;
  isJuridical: number;
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
};

export default function TrafficDetailPanel({ userId, email, isJuridical, onSuccess, onError }: Props) {
  const initial = useMemo(() => defaultRange(), []);
  const [dateFrom, setDateFrom] = useState(initial.from);
  const [dateTo, setDateTo] = useState(initial.to);
  const [busy, setBusy] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(null);

  const recipient = splitEmails(email, isJuridical)[0] ?? null;
  const canSend = Boolean(recipient && dateFrom && dateTo && !busy);

  async function handleSend() {
    if (!recipient || !dateFrom || !dateTo) return;
    setBusy(true);
    setSentTo(null);
    try {
      const res = await postTrafficDetailSend(userId, {
        date_from: dateFrom,
        date_to: dateTo,
      });
      setSentTo(res.email);
      onSuccess?.(res.message);
    } catch (e: unknown) {
      onError?.(e instanceof Error ? e.message : "Не удалось отправить детализацию");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="up-traffic-detail">
      <p className="up-traffic-detail-intro">
        Выберите период и отправьте абоненту детализацию расхода трафика в формате Excel на
        e-mail из профиля.
      </p>
      {recipient ? (
        <p className="up-traffic-detail-email">
          Детализация будет отправлена на адрес: <strong>{recipient}</strong>
          {isJuridical === 2 && (email?.includes(";") ?? false) ? (
            <span className="up-muted"> (первый из списка в профиле)</span>
          ) : null}
        </p>
      ) : (
        <p className="up-muted up-error">В профиле абонента не указан e-mail — отправка невозможна.</p>
      )}
      <div className="up-traffic-detail-dates">
        <div className="up-traffic-detail-date-field">
          <span className="up-label up-label--inline">С</span>
          <DatePickerField value={dateFrom} onChange={setDateFrom} placeholder="дд.мм.гггг" />
        </div>
        <span className="up-traffic-detail-sep" aria-hidden>
          —
        </span>
        <div className="up-traffic-detail-date-field">
          <span className="up-label up-label--inline">По</span>
          <DatePickerField
            value={dateTo}
            minDate={dateFrom || undefined}
            onChange={setDateTo}
            placeholder="дд.мм.гггг"
          />
        </div>
      </div>
      <button
        type="button"
        className="up-fc-run-btn up-traffic-detail-send"
        disabled={!canSend}
        onClick={() => void handleSend()}
      >
        {busy ? "Отправка…" : "Отправить детализацию"}
      </button>
      {sentTo ? (
        <p className="up-traffic-detail-ok" role="status">
          Отправлено на {sentTo}
        </p>
      ) : null}
    </div>
  );
}
