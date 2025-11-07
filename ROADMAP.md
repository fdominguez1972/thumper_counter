# Thumper Counter - Development Roadmap

**Last Updated:** November 6, 2025
**Current Phase:** Backend Complete - Frontend Development Next

## Completed Work (Sprints 1-6)

### Backend ML Pipeline
- [x] YOLOv8 deer detection with GPU acceleration
- [x] Multi-class classification (doe, fawn, mature, mid, young)
- [x] ResNet50 re-identification with pgvector
- [x] Automatic pipeline (detection -> classification -> re-ID)
- [x] Batch processing for existing images

### API Endpoints
- [x] Image upload and management
- [x] Location management
- [x] Deer profile CRUD
- [x] Batch processing control
- [x] Timeline analysis (activity patterns)
- [x] Location patterns (movement analysis)

### Infrastructure
- [x] Docker Compose orchestration
- [x] PostgreSQL with pgvector extension
- [x] Redis for Celery task queue
- [x] CUDA GPU support
- [x] Thread-safe model loading

## Next Phase: Frontend Development

### Priority 1: Core Dashboard (2-3 weeks)

**Technology Stack:**
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- React Query for API state management
- Recharts for data visualization

**Features:**
1. **Dashboard Overview**
   - Total deer count
   - Recent sightings (last 24h, 7d, 30d)
   - Processing statistics
   - Active locations

2. **Deer Gallery**
   - Grid view of all deer profiles
   - Thumbnail images (best detection crop)
   - Basic info (name, sex, sighting count)
   - Click to view details

3. **Individual Deer View**
   - Profile header (name, sex, species, status)
   - Timeline chart (activity over time)
   - Location map/list (movement patterns)
   - Detection gallery (all sightings)
   - Confidence scores

4. **Image Management**
   - Upload interface (drag-drop, multi-file)
   - Processing status tracking
   - Filter by location/date/status
   - View detection results

### Priority 2: Advanced Features (1-2 weeks)

1. **Real-Time Updates**
   - WebSocket connection for live processing status
   - Auto-refresh on new detections
   - Progress bars for batch processing

2. **Advanced Filtering**
   - Date range picker
   - Location multi-select
   - Sex/age filters
   - Confidence threshold slider

3. **Data Visualization**
   - Activity heatmaps (time of day)
   - Location movement diagrams
   - Population trends over time
   - Sex distribution pie charts

4. **Deer Management**
   - Manual deer naming
   - Merge duplicate profiles
   - Mark as deceased
   - Add notes/observations

### Priority 3: Production Features (1 week)

1. **Authentication**
   - User login/logout
   - Role-based access (admin, viewer)
   - API key management

2. **Reporting**
   - PDF export (deer profiles)
   - CSV export (sightings data)
   - Daily/weekly email summaries
   - Custom date range reports

3. **Settings**
   - Camera location configuration
   - Detection thresholds
   - Re-ID sensitivity
   - Email notification preferences

## Optional Enhancements (Future)

### Machine Learning Improvements
- [ ] Fine-tune ResNet50 on deer dataset
- [ ] Multi-viewpoint embeddings (front, side, rear)
- [ ] Temporal smoothing (track over time)
- [ ] Active learning for threshold tuning
- [ ] Antler point counting model

### Advanced Analytics
- [ ] Population estimates (Lincoln-Petersen method)
- [ ] Home range analysis (kernel density estimation)
- [ ] Movement corridor detection
- [ ] Seasonal behavior patterns
- [ ] Doe-to-buck ratio tracking

### Integration Features
- [ ] GIS mapping integration (Google Maps, Leaflet)
- [ ] Weather data correlation
- [ ] Moon phase tracking
- [ ] Food plot monitoring
- [ ] Trail camera health monitoring

### Mobile App
- [ ] React Native mobile app
- [ ] Push notifications
- [ ] Photo upload from phone
- [ ] Offline mode
- [ ] Field data collection

## Frontend Development Plan

### Week 1: Setup & Core Components
**Goal:** Basic React app with routing and API integration

Tasks:
1. Initialize React + Vite + TypeScript project
2. Set up TailwindCSS and component library
3. Create API client with React Query
4. Implement routing (React Router)
5. Build basic layout (header, sidebar, content)
6. Create dashboard overview page

### Week 2: Deer Management UI
**Goal:** View and manage deer profiles

Tasks:
1. Build deer gallery with grid/list views
2. Create individual deer detail page
3. Implement timeline chart component
4. Add location list/map component
5. Build detection gallery viewer
6. Add deer editing form

### Week 3: Image & Batch Processing
**Goal:** Upload and process images

Tasks:
1. Create image upload interface
2. Build processing status monitor
3. Add batch processing controls
4. Implement image filtering
5. Create detection result viewer
6. Add progress indicators

### Week 4: Polish & Deploy
**Goal:** Production-ready frontend

Tasks:
1. Add authentication (if needed)
2. Implement error handling
3. Add loading states
4. Create responsive layouts
5. Write E2E tests (Playwright)
6. Deploy frontend (Vercel/Netlify)

## Technology Recommendations

### Frontend Stack
```javascript
// package.json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "recharts": "^2.10.0",
    "date-fns": "^2.30.0",
    "react-dropzone": "^14.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### Project Structure
```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── common/          # Buttons, inputs, cards
│   │   ├── deer/            # Deer-specific components
│   │   ├── images/          # Image viewer components
│   │   └── layout/          # Header, sidebar, footer
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── DeerGallery.tsx
│   │   ├── DeerDetail.tsx
│   │   ├── Images.tsx
│   │   └── Settings.tsx
│   ├── hooks/               # Custom React hooks
│   ├── api/                 # API client functions
│   ├── types/               # TypeScript types
│   ├── utils/               # Helper functions
│   └── App.tsx
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## Deployment Architecture

### Production Setup
```
┌─────────────────────────────────────────┐
│          Nginx Reverse Proxy            │
│  (SSL termination, static file serving) │
└────────────┬────────────────────────────┘
             │
     ┌───────┴────────┐
     │                │
┌────▼─────┐   ┌─────▼──────┐
│ Frontend │   │  Backend   │
│  (React) │   │  (FastAPI) │
│  Port 80 │   │ Port 8001  │
└──────────┘   └─────┬──────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐  ┌────▼───┐  ┌────▼────┐
   │ Worker │  │ Postgres│  │  Redis  │
   │ Celery │  │ pgvector│  │  Queue  │
   └────────┘  └─────────┘  └─────────┘
```

### Docker Compose Update
Add frontend service:
```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:3000"
  environment:
    - VITE_API_URL=http://localhost:8001
  depends_on:
    - backend
```

## Timeline Estimate

### Minimum Viable Product (MVP)
**Timeline:** 3-4 weeks
**Features:**
- Dashboard overview
- Deer gallery and detail views
- Image upload
- Basic filtering

### Full Feature Set
**Timeline:** 6-8 weeks
**Features:**
- All MVP features
- Advanced analytics
- Real-time updates
- Authentication
- Reporting

### Production Ready
**Timeline:** 8-10 weeks
**Features:**
- All features above
- E2E testing
- Documentation
- Performance optimization
- Security hardening

## Next Immediate Steps

1. **Create Frontend Branch**
   ```bash
   git checkout -b 005-frontend-dashboard
   git push -u origin 005-frontend-dashboard
   ```

2. **Initialize React Project**
   ```bash
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   npm install
   ```

3. **Install Dependencies**
   ```bash
   npm install react-router-dom @tanstack/react-query axios
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

4. **Set Up API Client**
   - Create axios instance
   - Configure base URL
   - Add request/response interceptors

5. **Build First Component**
   - Start with Dashboard.tsx
   - Fetch deer count from API
   - Display basic statistics

## Success Metrics

### Backend (Complete)
- [x] 100% API endpoint coverage
- [x] <50ms API response time
- [x] GPU-accelerated inference
- [x] Automatic pipeline working

### Frontend (To Be Measured)
- [ ] <2s page load time
- [ ] <100ms UI interaction response
- [ ] Mobile responsive (375px+)
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] 90+ Lighthouse score

## Questions to Answer

1. **Hosting:** Where will frontend be deployed? (Vercel, Netlify, self-hosted?)
2. **Authentication:** Is user login required? (Multi-user system?)
3. **Mobile:** Mobile app needed or just responsive web?
4. **Branding:** Any specific design preferences? (Colors, logo, etc.)
5. **Features:** Which priority features are must-have vs. nice-to-have?

---

**Ready to begin frontend development!**

The backend is fully functional and production-ready. All APIs are documented
and tested. The next logical step is building the React dashboard to visualize
the deer tracking data and provide a user-friendly interface for ranch management.
