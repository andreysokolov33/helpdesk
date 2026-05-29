import type { TicketSubscriberAccountSummary, TicketSubscriberTariffSummary } from "@/api/ticket";

function fmtMoney(n: number) {
  return `${n.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ₽`;
}

function fmtTrafficMb(n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return "—";
  const v = Object.is(n, -0) || n < 0 ? 0 : n;
  return v.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 1 });
}

function fmtTrafficRemainTotal(
  remain: number | null | undefined,
  full: number | null | undefined,
  tariffEnded: boolean,
) {
  const rem = tariffEnded ? 0 : remain;
  return `${fmtTrafficMb(rem)} / ${fmtTrafficMb(full)} МБ`;
}

function clampMainMb(n: number | null | undefined): number | null {
  if (n == null || Number.isNaN(n)) return null;
  return Math.max(0, n);
}

function hasJurDopPacket(mb: number | null | undefined): boolean {
  return mb != null && mb > 0;
}

function tariffBadgeMod(state: string): string {
  if (state === "frozen") return "frozen";
  if (state === "active") return "active";
  if (state === "ended") return "ended";
  if (state === "planned_freeze") return "planned";
  return "inactive";
}

function TariffStatusBadge({ tariff }: { tariff: TicketSubscriberTariffSummary }) {
  return (
    <span className={`ch-tariff-badge ch-tariff-badge--${tariffBadgeMod(tariff.state)}`}>
      {tariff.status_label}
    </span>
  );
}

type Props = {
  account: TicketSubscriberAccountSummary;
  isJuridical: number;
};

export default function TicketSubscriberAccountSidebar({ account, isJuridical }: Props) {
  const t = account.tariff;
  const isJur = isJuridical === 2;
  const isFrozen = t.state === "frozen";
  const isEnded = t.state === "ended";
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
          <div className="tk-side-tariff-none" role="status">
            Нет активного тарифа
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
              <span className="kvv">
                <TariffStatusBadge tariff={t} />
              </span>
            </div>

            {isFrozen ? (
              <>
                {t.frozen_at_label ? (
                  <div className="kv">
                    <span className="kvk">Заморожен с</span>
                    <span className="kvv">{t.frozen_at_label}</span>
                  </div>
                ) : null}
                {t.unfreeze_at_label ? (
                  <div className="kv">
                    <span className="kvk">Заморожен до</span>
                    <span className="kvv">{t.unfreeze_at_label}</span>
                  </div>
                ) : null}
                {t.type_label ? (
                  <div className="kv">
                    <span className="kvk">Тип</span>
                    <span className="kvv">{t.type_label}</span>
                  </div>
                ) : null}
                {showJurLimited ? (
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
                        <span className="kvv">{fmtTrafficMb(overrunMb)} МБ</span>
                      </div>
                    ) : null}
                  </>
                ) : t.remain_traffic_mb != null && t.full_packet_mb != null ? (
                  <div className="kv">
                    <span className="kvk">Трафик (остаток / всего)</span>
                    <span className="kvv">
                      {fmtTrafficMb(t.remain_traffic_mb)} / {fmtTrafficMb(t.full_packet_mb)} МБ
                    </span>
                  </div>
                ) : null}
                {t.frozen_remaining_label ? (
                  <div className="kv">
                    <span className="kvk">Замороженный срок</span>
                    <span className="kvv">{t.frozen_remaining_label}</span>
                  </div>
                ) : null}
              </>
            ) : (
              <>
                {t.type_label ? (
                  <div className="kv">
                    <span className="kvk">Тип</span>
                    <span className="kvv">{t.type_label}</span>
                  </div>
                ) : null}
                {(t.state === "active" || t.state === "ended") &&
                (t.valid_date_label || t.remaining_label) ? (
                  <div className="kv">
                    <span className="kvk">Срок действия</span>
                    <span className="kvv tk-side-validity">
                      {t.valid_date_label ? <span>До {t.valid_date_label}</span> : null}
                      {t.remaining_label ? (
                        <span className="tk-side-validity__remain">{t.remaining_label}</span>
                      ) : null}
                    </span>
                  </div>
                ) : null}

                {showJurLimited ? (
                  <>
                    {t.remain_traffic_mb != null && t.full_packet_mb != null ? (
                      <div className="kv">
                        <span className="kvk">Трафик (остаток / всего)</span>
                        <span className={`kvv${overrunMb && !isEnded ? " red" : ""}`}>
                          {fmtTrafficRemainTotal(t.remain_traffic_mb, t.full_packet_mb, isEnded)}
                        </span>
                      </div>
                    ) : null}
                    {t.jur_main_packet_mb != null ? (
                      <div className="kv">
                        <span className="kvk">Основной пакет (ЮЛ)</span>
                        <span className="kvv">{fmtTrafficMb(t.jur_main_packet_mb)} МБ</span>
                      </div>
                    ) : null}
                    {showJurLimited ? (
                      <div className="kv">
                        <span className="kvk">
                          {hasJurDopPacket(t.jur_dop_packet_mb) ? "Доп. пакет (ЮЛ)" : "Доп. пакет"}
                        </span>
                        <span className="kvv">
                          {hasJurDopPacket(t.jur_dop_packet_mb)
                            ? `${fmtTrafficMb(t.jur_dop_packet_mb)} МБ`
                            : "не предусмотрен"}
                        </span>
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
                      {fmtTrafficRemainTotal(t.remain_traffic_mb, t.full_packet_mb, isEnded)}
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
          </>
        )}
      </div>
    </>
  );
}
