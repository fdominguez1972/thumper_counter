# Thumper Counter - Frontend Dashboard

React TypeScript dashboard for the Thumper Counter deer tracking system.

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **React Router** - Navigation
- **React Query** - API state management
- **Recharts** - Data visualization
- **Axios** - HTTP client

## Features

### Dashboard Overview
- Total deer count and statistics
- Population breakdown (bucks, does, fawns)
- Recent sightings

### Deer Gallery
- Grid view of all deer profiles
- Filter by sex (buck, doe, fawn, unknown)
- Sort by last seen, first seen, or sighting count
- Click to view individual deer details

### Individual Deer View
- Profile information (sex, confidence, sightings)
- Activity timeline chart
- Location patterns with sighting counts
- First and last seen dates

### Image Management (Coming Soon)
- Upload images via drag-and-drop
- View processing status
- Filter by location, date, and status

## Development

### Prerequisites
- Docker and Docker Compose
- OR Node.js 20+ (if running locally)

### Running with Docker (Recommended)

```bash
# From project root
docker-compose up -d frontend

# View logs
docker-compose logs -f frontend
```

The dashboard will be available at http://localhost:3000

### Running Locally

```bash
# Install dependencies
cd frontend
npm install

# Start dev server
npm run dev
```

The dev server includes proxy configuration to forward API requests to http://localhost:8001

### Building for Production

```bash
# Build production bundle
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/             # API client and endpoints
│   │   ├── client.ts    # Axios instance
│   │   └── deer.ts      # Deer API functions
│   ├── components/      # React components
│   │   └── layout/      # Layout components
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx
│   │   ├── DeerGallery.tsx
│   │   ├── DeerDetail.tsx
│   │   └── Images.tsx
│   ├── App.tsx          # Root component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Integration

The frontend connects to the backend API at `/api` (proxied in development).

### Available Endpoints

- `GET /api/deer` - List all deer
- `GET /api/deer/{id}` - Get specific deer
- `GET /api/deer/{id}/timeline` - Get activity timeline
- `GET /api/deer/{id}/locations` - Get location patterns
- `PUT /api/deer/{id}` - Update deer (name, notes, etc.)

### Adding New API Endpoints

1. Add TypeScript interfaces in `src/api/deer.ts`
2. Create API function using `apiClient`
3. Use `useQuery` hook in components

Example:
```typescript
// src/api/deer.ts
export const getDeerStats = async (): Promise<DeerStats> => {
  const response = await apiClient.get('/deer/stats');
  return response.data;
};

// In component
const { data } = useQuery({
  queryKey: ['deer', 'stats'],
  queryFn: getDeerStats,
});
```

## Environment Variables

Create `.env` file in frontend directory:

```env
VITE_API_URL=http://localhost:8001
```

## Styling

Uses TailwindCSS utility classes for styling.

### Color Scheme

- Primary: Blue (`bg-blue-500`, `text-blue-700`)
- Buck: Amber (`bg-amber-100`, `text-amber-800`)
- Doe: Pink (`bg-pink-100`, `text-pink-800`)
- Fawn: Blue (`bg-blue-100`, `text-blue-800`)

### Adding New Components

1. Create component in appropriate directory
2. Use Tailwind classes for styling
3. Export from component file
4. Import in parent component or page

## Future Enhancements

- Real-time updates via WebSocket
- Image upload with drag-and-drop
- Advanced filtering and search
- Export to PDF/CSV
- User authentication
- Mobile app (React Native)

## Troubleshooting

### API Connection Issues

Check that backend is running:
```bash
curl http://localhost:8001/health
```

### Build Errors

Clear node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Docker Issues

Rebuild frontend container:
```bash
docker-compose build frontend
docker-compose up -d frontend
```

## License

Same as main project.
