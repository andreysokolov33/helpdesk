export function LogoMark({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 100 100" aria-hidden>
      <circle cx="50" cy="50" r="48" fill="var(--red)" />
      <path
        fill="var(--nvb)"
        d="M50 15 C30 15 15 35 20 55 C22 62 30 70 40 72 C35 60 33 48 38 38 C43 28 50 25 50 25 C50 25 43 35 45 50 C47 62 55 72 55 72 C55 72 48 65 47 55 C46 48 50 42 55 38 C60 34 65 38 65 48 C65 58 58 68 50 72 C62 70 72 60 75 50 C78 38 70 20 50 15Z"
      />
      <circle cx="52" cy="58" r="6" fill="var(--nvb)" />
    </svg>
  );
}
