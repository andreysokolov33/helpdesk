import { useId } from "react";

type Props = {
  hotspotAddress: string | null | undefined;
};

function HelpIcon() {
  return (
    <svg className="up-help-icon" viewBox="0 0 24 24" aria-hidden>
      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.75" />
      <line
        x1="12"
        y1="7.25"
        x2="12"
        y2="13.25"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
      />
      <circle cx="12" cy="16.75" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function AuthPageHelp({ hotspotAddress }: Props) {
  const tipId = useId();
  const addr = hotspotAddress?.trim() || null;

  return (
    <span className="up-help-wrap">
      <button
        type="button"
        className="up-help-btn"
        aria-label="Инструкция: как авторизовать абонента в Wi‑Fi"
        aria-describedby={tipId}
      >
        <HelpIcon />
      </button>
      <div id={tipId} className="up-help-popover" role="tooltip">
        <div className="up-help-title">Инструкция для абонента: вход в Wi‑Fi</div>
        <div className="up-help-body">
          <ol className="up-help-steps">
            <li>
              <span className="up-help-step-name">Подключение к сети</span>
              <p>
                Попросите подключиться к Wi‑Fi нашей сети. В названии сети обычно есть{" "}
                <strong>WFTK</strong>, <strong>Wifitochka</strong> или <strong>FREEWIFI</strong>.
              </p>
              <p>
                После подключения на телефоне должна <strong>сама открыться</strong> страница авторизации — абонент
                вводит <strong>логин и пароль</strong> из договора.
              </p>
            </li>
            <li>
              <span className="up-help-step-name">Страница не открылась сама</span>
              <p>
                Убедитесь, что Wi‑Fi подключён. Откройте <strong>любой браузер</strong> и в{" "}
                <strong>адресной строке</strong> (не в поиске Google/Yandex) введите адрес страницы авторизации:
              </p>
              {addr ? (
                <span className="up-help-addr-line" title={addr}>
                  <code className="up-help-addr">{addr}</code>
                </span>
              ) : (
                <p className="up-help-note">
                  Адрес не указан в карточке — уточните у коллег или в АБС. После ввода адреса должна открыться
                  страница входа.
                </p>
              )}
              {addr ? <p>После перехода по адресу должна открыться страница авторизации.</p> : null}
            </li>
            <li>
              <span className="up-help-step-name">Адрес в браузере не открывается</span>
              <p>
                Попросите зайти в личный кабинет:{" "}
                <a href="https://lk.wifitochka.ru" target="_blank" rel="noopener noreferrer" className="up-help-link">
                  lk.wifitochka.ru
                </a>
                , войти под логином абонента и на главной нажать <strong>«Включить интернет»</strong>. Должна
                открыться страница авторизации.
              </p>
            </li>
          </ol>
        </div>
      </div>
    </span>
  );
}
