import type { TicketSubscriberAccountSummary } from "@/api/ticket";

function fmtMoney(n: number) {
  return `${n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ₽`;
}

function fmtTrafficMb(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 1 });
}

function clampMainMb(n: number | null | undefined): number | null {
  if (n == null || Number.isNaN(n)) return null;
  return Math.max(0, n);
}

function statusClass(label: string): string {
  if (label === "Активен") return "ok";
  if (label === "Заморожен" || label === "Неактивен") return "red";
  if (label === "Запланирована заморозка") return "wn";
  return "";
}

type Props = {
  account: TicketSubscriberAccountSummary;
  isJuridical: number;
};

export default function TicketSubscriberAccountSidebar({ account, isJuridical }: Props) {
  const t = account.tariff;
  const isJur = isJuridical === 2;
  const isFrozen = t.status_label === "Заморожен";
  const isLimited = t.type_label === "Лимитный";
  const trafficLabel = t.type_label === "Безлимитный" ? "Суточный трафик" : "Трафик";
  const speed =
    t.rate_up && t.rate_down
      ? `↑ ${t.rate_up} / ↓ ${t.rate_down}`
      : t.rate_up || t.rate_down || null;
  const showJurLimited = isJur && isLimited;
  const mainRemainMb = clampMainMb(t.jur_main_packet_mb);
  const overrunMb = t.overrun_mb != null && t.overrun_mb > 0 ? t.overrun_mb : null;

  return (
    <>
      <div className="ipb tk-side-account">
        <div className="ipl">Баланс</div>
        <div className={`tk-side-balance${account.balance < 0 ? " tk-side-balance--neg" : ""}`}>
          {fmtMoney(account.balance)}
        </div>
      </div>

      <div className="ipb tk-side-account">
        <div className="ipl">Тариф</div>
        {!t.connected ? (
          <div className="tk-side-tariff-empty" role="status">
            Тариф не подключен
          </div>
        ) : (
          <>
            {t.tariff_name ? (
              <div className="kv">
                <span className="kvk">Название</span>
                <span className="kvv">{t.tariff_name}</span>
              </div>
            ) : null}
            <div className="kv">
              <span className="kvk">Статус</span>
              <span className={`kvv ${statusClass(t.status_label)}`}>{t.status_label}</span>
            </div>
            {t.type_label ? (
              <div className="kv">
                <span className="kvk">Тип</span>
                <span className="kvv">{t.type_label}</span>
              </div>
            ) : null}

            {showJurLimited && isFrozen ? (
              <>
                {mainRemainMb != null ? (
                  <div className="kv">
                    <span className="kvk">Остаток основного пакета</span>
                    <span className="kvv">{fmtTrafficMb(mainRemainMb)} МБ</span>
                  </div>
                ) : null}
                {overrunMb != null ? (
                  <div className="kv">
                    <span className="kvk">Использовано доп. трафика</span>
                    <span className="kvv red">{fmtTrafficMb(overrunMb)} МБ</span>
                  </div>
                ) : null}
              </>
            ) : null}

            {showJurLimited && !isFrozen ? (
              <>
                {t.remain_traffic_mb != null && t.full_packet_mb != null ? (
                  <div className="kv">
                    <span className="kvk">Трафик (остаток / всего)</span>
                    <span className={`kvv${overrunMb ? " red" : ""}`}>
                      {fmtTrafficMb(t.remain_traffic_mb)} / {fmtTrafficMb(t.full_packet_mb)} МБ
                    </span>
                  </div>
                ) : null}
                {t.jur_main_packet_mb != null ? (
                  <div className="kv">
                    <span className="kvk">Основной пакет (ЮЛ)</span>
                    <span className="kvv">{fmtTrafficMb(t.jur_main_packet_mb)} МБ</span>
                  </div>
                ) : null}
                {t.jur_dop_packet_mb != null ? (
                  <div className="kv">
                    <span className="kvk">Доп. пакет (ЮЛ)</span>
                    <span className="kvv">{fmtTrafficMb(t.jur_dop_packet_mb)} МБ</span>
                  </div>
                ) : null}
                {overrunMb != null ? (
                  <div className="tk-side-overrun" role="status">
                    Перерасход трафика: ~{overrunMb.toFixed(1)} МБ
                  </div>
                ) : null}
              </>
            ) : null}

            {!showJurLimited && t.remain_traffic_mb != null && t.full_packet_mb != null ? (
              <div className="kv">
                <span className="kvk">{trafficLabel}</span>
                <span className="kvv">
                  {fmtTrafficMb(t.remain_traffic_mb)} / {fmtTrafficMb(t.full_packet_mb)} МБ
                </span>
              </div>
            ) : null}

            {speed ? (
              <div className="kv">
                <span className="kvk">Скорость</span>
                <span className="kvv">{speed}</span>
              </div>
            ) : null}
            {t.msk_reset ? (
              <>
                <div className="kv">
                  <span className="kvk">Сброс суточного трафика</span>
                  <span className="kvv">{t.msk_reset}</span>
                </div>
                {t.local_reset ? (
                  <div className="kv">
                    <span className="kvk">Местное время</span>
                    <span className="kvv">{t.local_reset}</span>
                  </div>
                ) : null}
              </>
            ) : null}
          </>
        )}
      </div>
    </>
  );
}
