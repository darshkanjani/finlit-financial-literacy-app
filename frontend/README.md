# FinLit Frontend

React and TypeScript frontend for the FinLit financial literacy platform.

## Setup

```bash
cp .env.example .env
bun install
bun run dev
```

The frontend runs at:

```text
http://localhost:5173
```

## Environment

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Structure

```text
frontend/
├── src/
│   ├── App.tsx
│   ├── components/       # Shared UI and API client
│   ├── pages/            # Home, auth, onboarding, dashboard, goals, stress, advice, chat
│   ├── lib/              # Utility functions and tests
│   └── test/             # Vitest setup
├── package.json
├── vite.config.ts
└── bun.lock
```

## Scripts

```bash
bun run dev       # local development
bun run build     # production build
bun run test      # Vitest tests
bun run lint      # ESLint
```

The frontend talks to the backend through a shared `wretch` API client and sends cookies with `credentials: include`.
