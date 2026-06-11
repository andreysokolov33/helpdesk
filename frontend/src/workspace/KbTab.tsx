import { useState } from "react";
import { MOCK_KB_SECTIONS } from "@/data/mockCc";

export default function KbTab() {
  const [open, setOpen] = useState<Record<string, boolean>>({});

  function toggle(key: string) {
    setOpen((o) => ({ ...o, [key]: !o[key] }));
  }

  return (
    <div className="tp on kb-page">
      <div className="pg">
        <div className="kb-page__title">База знаний</div>
        {MOCK_KB_SECTIONS.map((sec) => (
          <div key={sec.title} className="kbsec">
            <div className="kbst">{sec.title}</div>
            {sec.items.map((it) => {
              const key = `${sec.title}:${it.title}`;
              const isOpen = open[key];
              return (
                <button
                  type="button"
                  key={key}
                  className={`kbi${isOpen ? " open" : ""}`}
                  onClick={() => toggle(key)}
                >
                  <div className="kbit">{it.title}</div>
                  <div className="kbid">{it.body}</div>
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
