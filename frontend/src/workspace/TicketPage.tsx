import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import MessageBody from "@/components/MessageBody";
import {
  fetchTicketDetail,
  fetchTicketMessages,
  formatMsgTime,
  formatTicketCreated,
  sendTicketMessage,
  type TicketDetail,
  type TicketMessage,
} from "@/api/ticket";

function sideLabel(msg: TicketMessage): string {
  if (msg.side === "client") return "Абонент";
  if (msg.side === "partner") return msg.author_name || "Партнёр";
  if (msg.author_name) return msg.author_name;
  return "КЦ";
}

function avatarLetter(msg: TicketMessage, subscriberName: string): string {
  if (msg.side === "client") return subscriberName.trim()[0]?.toUpperCase() || "А";
  if (msg.side === "note") return "З";
  return "К";
}

type AttachBlockProps = { msg: TicketMessage };

function AttachmentsBlock({ msg }: AttachBlockProps) {
  const items = [
    ...(msg.legacy_file_url
      ? [
          {
            id: -1,
            file_path: msg.legacy_file_url,
            original_filename: "Файл",
            is_image: /\.(jpe?g|png|gif|webp|bmp)$/i.test(msg.legacy_file_url),
          },
        ]
      : []),
    ...msg.attachments,
  ];
  if (!items.length) return null;
  return (
    <div className="tk-att">
      {items.map((a) =>
        a.is_image ? (
          <a key={a.id} href={a.file_path} target="_blank" rel="noreferrer" className="tk-att-img">
            <img src={a.file_path} alt={a.original_filename || "Вложение"} loading="lazy" />
          </a>
        ) : (
          <a key={a.id} href={a.file_path} target="_blank" rel="noreferrer" className="tk-att-file">
            {a.original_filename || "Скачать файл"}
          </a>
        ),
      )}
    </div>
  );
}

export default function TicketPage() {
  const { ticketId: ticketIdParam } = useParams();
  const ticketId = Number(ticketIdParam);
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [messages, setMessages] = useState<TicketMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sending, setSending] = useState(false);
  const [sideOpen, setSideOpen] = useState(true);

  const load = useCallback(async () => {
    if (!Number.isFinite(ticketId) || ticketId <= 0) {
      setError("Некорректный ID тикета");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [d, m] = await Promise.all([fetchTicketDetail(ticketId), fetchTicketMessages(ticketId)]);
      setDetail(d);
      setMessages(m.messages);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
      setDetail(null);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    const ta = inputRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  async function submit() {
    const t = input.trim();
    if (!t && !file) return;
    if (!detail?.can_reply && detail?.chat_mode === "mail") return;
    setSending(true);
    try {
      const msg = await sendTicketMessage(ticketId, t, file);
      setMessages((prev) => [...prev, msg]);
      setInput("");
      setFile(null);
    } catch (e: unknown) {
      window.alert(e instanceof Error ? e.message : "Не удалось отправить");
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return (
      <div className="tp on">
        <div className="pg">
          <p className="ch-list-loading">Загрузка тикета…</p>
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="tp on">
        <div className="pg">
          <div className="ch-list-err">{error || "Тикет не найден"}</div>
          <Link to="/chats" className="tk-back-link">
            ← К чатам
          </Link>
        </div>
      </div>
    );
  }

  const subName = detail.subscriber_name || detail.caller_name || "Абонент";
  const introBody = detail.body?.trim() || "";
  const chatMessages = messages.filter((m) => !m.is_initial);
  const hasIntro = introBody.length > 0;

  return (
    <div className="tp on" id="tp-ticket" style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "hidden", position: "relative" }}>
        <div className="tbar">
          <button type="button" className="tbk" onClick={() => navigate("/chats")}>
            ← Назад
          </button>
          <div style={{ width: 1, height: 16, background: "var(--ln)" }} />
          <div className="tk-tbar-head">
            <span className="tk-tbar-id">#{detail.id}</span>
            <span className="tk-tbar-sep" aria-hidden>
              ·
            </span>
            <h1 className="tk-tbar-title">{detail.title}</h1>
            <span className={`ch-status ch-status--${detail.status}`}>{detail.status_label}</span>
          </div>
          <div className="tacts">
            <button
              type="button"
              className={`tb3 tk-panel-toggle${sideOpen ? " on" : ""}`}
              onClick={() => setSideOpen((v) => !v)}
              title={sideOpen ? "Скрыть панель абонента" : "Показать панель абонента"}
            >
              {sideOpen ? "Панель ▶" : "◀ Панель"}
            </button>
          </div>
        </div>

        <div className="tbody tk-ticket-body">
          <div className="czone tk-chat-main">
            <div className="cscrl tk-chat-scroll" ref={scrollRef}>
              <div className="tk-chat-feed">
                {hasIntro ? (
                  <div className="tk-intro" role="note">
                    <div className="tk-intro__eyebrow">Суть обращения</div>
                    <MessageBody text={introBody} className="tk-intro__text" />
                    {detail.date_of_create_iso ? (
                      <div className="tk-intro__meta">{formatMsgTime(detail.date_of_create_iso)}</div>
                    ) : null}
                  </div>
                ) : null}

                {chatMessages.length > 0 && hasIntro ? (
                  <div className="tk-chat-divider" aria-hidden>
                    <span>Переписка</span>
                  </div>
                ) : null}

                {chatMessages.length === 0 && !hasIntro ? (
                  <div className="tk-chat-empty">Сообщений пока нет</div>
                ) : (
                  chatMessages.map((m) => (
                    <div key={m.id} className={`msg ${m.side === "client" ? "cl" : "me"}`}>
                      <div className={`mav ${m.side === "client" ? "cl" : "ag"}`}>{avatarLetter(m, subName)}</div>
                      <div className="mc2">
                        <div className={`bbl ${m.side === "client" ? "cl" : "ag"}`}>
                          <div className="tk-msg-label">{sideLabel(m)}</div>
                          <MessageBody text={m.text} />
                          <AttachmentsBlock msg={m} />
                        </div>
                        <div className="mtm">{formatMsgTime(m.created_at_iso) || "—"}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="tk-composer">
              {!detail.can_reply ? (
                <div className="tk-no-reply">
                  Абонент не определён — ответ в чат недоступен. Укажите абонента в карточке или завершите
                  обработку звонка.
                </div>
              ) : (
                <>
                  <div className="tk-composer__box">
                    <textarea
                      ref={inputRef}
                      className="tk-composer__input"
                      rows={1}
                      placeholder="Ответ клиенту…"
                      value={input}
                      disabled={sending}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.ctrlKey && e.key === "Enter") {
                          e.preventDefault();
                          submit();
                        }
                      }}
                    />
                    <div className="tk-composer__actions">
                      <label className="tk-composer__attach" title="Прикрепить файл">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                          <path
                            d="M14 8l-4.2 4.2a3 3 0 104.2 4.2l5-5a4 4 0 00-5.7-5.7l-5.8 5.8"
                            stroke="currentColor"
                            strokeWidth="1.7"
                            strokeLinecap="round"
                          />
                        </svg>
                        <input
                          type="file"
                          hidden
                          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv"
                          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                        />
                      </label>
                      <button
                        type="button"
                        className="tk-composer__send"
                        disabled={sending || (!input.trim() && !file)}
                        onClick={submit}
                        title="Отправить"
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                          <path
                            d="M12 19V6M12 6l-5 5M12 6l5 5"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                  {file ? (
                    <div className="tk-composer__file">
                      <span className="tk-composer__file-name">{file.name}</span>
                      <button type="button" className="tk-file-clear" onClick={() => setFile(null)}>
                        Убрать
                      </button>
                    </div>
                  ) : null}
                  <div className="tk-composer__hint">Ctrl+Enter — отправить</div>
                </>
              )}
            </div>
          </div>

          <aside className={`tk-sidebar ip${sideOpen ? "" : " closed"}`} aria-label="Информация о тикете">
            <div className="tk-sidebar__accent" aria-hidden />
            <div className="ips">
              <div className="ipb">
                <div className="ipl">Абонент</div>
                <div
                  className={detail.subscriber_is_juridical === 2 ? "tk-side-name tk-side-name--jur" : "tk-side-name"}
                >
                  {subName}
                </div>
                {detail.caller_name && detail.user_id == null ? (
                  <div className="tk-side-meta">Как представился: {detail.caller_name}</div>
                ) : null}
                {detail.subscriber_login ? (
                  <div className="tk-side-meta">Логин: {detail.subscriber_login}</div>
                ) : null}
                {detail.subscriber_profile_user_id != null ? (
                  <Link to={`/users/${detail.subscriber_profile_user_id}`} className="tk-profile-link">
                    Карточка абонента →
                  </Link>
                ) : null}
              </div>

              <div className="ipb">
                <div className="ipl">Тикет</div>
                <div className="kv">
                  <span className="kvk">Источник</span>
                  <span className="kvv">{detail.source_label}</span>
                </div>
                <div className="kv">
                  <span className="kvk">Линия</span>
                  <span className="kvv">{detail.support_line_label}</span>
                </div>
                {detail.category_label ? (
                  <div className="kv">
                    <span className="kvk">Категория</span>
                    <span className="kvv">{detail.category_label}</span>
                  </div>
                ) : null}
                {detail.priority_label ? (
                  <div className="kv">
                    <span className="kvk">Приоритет</span>
                    <span className="kvv">{detail.priority_label}</span>
                  </div>
                ) : null}
                {detail.station_name ? (
                  <div className="kv">
                    <span className="kvk">Станция</span>
                    <span className="kvv">{detail.station_name}</span>
                  </div>
                ) : null}
                {detail.assignee_name ? (
                  <div className="kv">
                    <span className="kvk">Исполнитель</span>
                    <span className="kvv">{detail.assignee_name}</span>
                  </div>
                ) : null}
                <div className="kv">
                  <span className="kvk">Создан</span>
                  <span className="kvv">{formatTicketCreated(detail.date_of_create_iso) || "—"}</span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
