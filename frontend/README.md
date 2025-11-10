# HR Co-Pilot Frontend

Modern React frontend for the HR Automation platform built with Vite, React, TypeScript, and shadcn/ui.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TanStack Query** (React Query) - Server state management
- **Zustand** - Client state management
- **React Router** - Routing
- **shadcn/ui** - UI components
- **Tailwind CSS** - Styling
- **Radix UI** - Accessible component primitives
- **Axios** - HTTP client
- **React Hot Toast** - Notifications

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

The development server includes:
- Hot Module Replacement (HMR)
- TypeScript type checking
- Automatic proxy to backend API on port 8000

### Building for Production

```bash
npm run build
```

Build output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── auth/         # Authentication components
│   │   ├── dashboard/    # Dashboard widgets
│   │   ├── layout/       # Layout components (Sidebar, Header)
│   │   └── ui/           # shadcn/ui components
│   ├── hooks/            # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useSubmissions.ts
│   │   ├── useExitInterviews.ts
│   │   ├── useAssets.ts
│   │   └── useDashboard.ts
│   ├── lib/              # Utilities and configuration
│   │   ├── api.ts        # Axios instance with auth
│   │   ├── types.ts      # TypeScript types
│   │   └── utils.ts      # Helper functions
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── SubmissionsPage.tsx
│   │   ├── ExitInterviewsPage.tsx
│   │   └── AssetsPage.tsx
│   ├── stores/           # Zustand stores
│   │   └── authStore.ts
│   ├── App.tsx           # Root component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies
```

## Features

### Authentication
- JWT-based authentication
- Automatic token refresh
- Protected routes
- Auto-logout on 401

### Dashboard
- Statistics overview
- Recent submissions
- Upcoming interviews
- Pending feedback

### Submissions Management
- Create/view/delete submissions
- Filter by status and date
- Resend approval emails
- View detailed submission info

### Exit Interview Management
- Schedule interviews
- Submit feedback
- Skip interviews
- Track upcoming and pending interviews
- Interview statistics

### Asset Management (Phase 3)
- Record IT assets (laptop, accessories)
- Track collection status
- IT approval workflow
- Filter assets by status
- Comprehensive asset forms

## API Integration

The frontend communicates with the FastAPI backend through:

- **Base URL**: `http://localhost:8000`
- **Auth**: JWT tokens in `Authorization: Bearer <token>` header
- **Storage**: Tokens stored in `localStorage`

### API Endpoints

```typescript
// Auth
POST /api/auth/login
POST /api/auth/logout

// Submissions
GET  /api/submissions
POST /api/submissions
GET  /api/submissions/{id}
PUT  /api/submissions/{id}
DELETE /api/submissions/{id}
POST /api/submissions/{id}/resend

// Exit Interviews
GET  /api/exit-interviews/stats
GET  /api/exit-interviews/upcoming
GET  /api/exit-interviews/pending-feedback
GET  /api/exit-interviews/pending-scheduling
POST /api/exit-interviews/schedule
POST /api/exit-interviews/feedback
POST /api/exit-interviews/skip

// Assets
GET  /api/assets
POST /api/assets/submissions/{id}/assets
POST /api/assets/{id}/approve
GET  /api/assets/stats
```

## State Management

### Server State (TanStack Query)
- Automatic caching
- Background refetching
- Optimistic updates
- Error handling

### Client State (Zustand)
- User authentication
- Token management
- Persistent login

## Styling

### Tailwind CSS
Utility-first CSS with custom design tokens:

```css
--background: 0 0% 100%
--foreground: 222.2 84% 4.9%
--primary: 221.2 83.2% 53.3%
--secondary: 210 40% 96.1%
--accent: 210 40% 96.1%
--destructive: 0 84.2% 60.2%
--muted: 210 40% 96.1%
```

### shadcn/ui Components
Pre-built accessible components:
- Button, Card, Badge, Input, Label
- Dialog, Select, Table, Tabs
- And more...

## Development Guidelines

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route in `App.tsx`
3. Add navigation link in `Sidebar.tsx`

### Adding New API Hooks

1. Create hook file in `src/hooks/`
2. Use TanStack Query for GET requests
3. Use mutations for POST/PUT/DELETE
4. Add TypeScript types in `lib/types.ts`

### Adding New UI Components

Use shadcn/ui CLI:

```bash
npx shadcn@latest add <component-name>
```

## Environment Variables

Create `.env` file in frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Port Already in Use
If port 5173 is occupied, Vite will automatically use the next available port (5174, 5175, etc.)

### CORS Issues
- Ensure backend CORS is configured for `http://localhost:5173`
- Check that backend is running on port 8000

### Type Errors
Run TypeScript check:
```bash
npm run type-check
```

### Build Errors
Clear cache and reinstall:
```bash
rm -rf node_modules node_modules/.vite
npm install
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

MIT
