# UI Specification
# Version: 1.0.0
# Date: 2025-11-04

## Overview

React-based dashboard for visualizing and managing the deer tracking system. Optimized for desktop use by ranch personnel with varying technical expertise.

## Design Principles

1. **Information Density**
   - WHY: Users need to see multiple data points at once
   - Grid layouts for efficient space usage
   - Minimal whitespace, maximum content

2. **Real-time Updates**
   - WHY: Processing happens continuously
   - WebSocket for live updates
   - Optimistic UI for responsiveness

3. **Progressive Disclosure**
   - WHY: Don't overwhelm new users
   - Basic view by default
   - Advanced features on demand

4. **Mobile-Last NOT Mobile-First**
   - WHY: Primary use is desktop monitoring
   - Optimize for 1920x1080 displays
   - Mobile as convenience, not primary

## Application Structure

```
Dashboard (/)
├── Overview (/dashboard)
├── Images (/images)
│   ├── Gallery View
│   ├── List View
│   └── Detail Modal
├── Deer (/deer)
│   ├── Profile Grid
│   ├── Individual Profile (/deer/:id)
│   └── Family Groups
├── Locations (/locations)
│   ├── Map View
│   ├── Location Stats (/locations/:id)
│   └── Camera Health
├── Analytics (/analytics)
│   ├── Population
│   ├── Movement
│   └── Activity
└── Settings (/settings)
    ├── Processing Config
    ├── API Keys
    └── Notifications
```

## Core Components

### 1. Dashboard Overview

**Layout:**
```
+------------------+------------------+
|  Active Summary  | Processing Queue |
+------------------+------------------+
|  Recent Activity Feed               |
+-------------------------------------+
|  Location Heat Map                  |
+-------------------------------------+
|  Population Chart  | Sex Distribution|
+------------------+------------------+
```

**Components:**
- **ActiveSummary**: Key metrics at a glance
- **ProcessingQueue**: Real-time queue status
- **ActivityFeed**: Last 20 detections
- **LocationHeatMap**: Activity by location
- **PopulationChart**: 30-day trend
- **SexDistribution**: Pie chart breakdown

### 2. Image Gallery

**Features:**
- Infinite scroll with virtualization
- Thumbnail grid (6 columns desktop)
- Overlay detection boxes
- Quick filters (location, date, has_deer)

**Image Card:**
```jsx
<ImageCard>
  <Thumbnail src={image.thumbnail_url} />
  <DetectionOverlay count={image.detection_count} />
  <Metadata>
    <Location>{image.location_name}</Location>
    <Timestamp>{formatRelative(image.timestamp)}</Timestamp>
  </Metadata>
</ImageCard>
```

**Detail Modal:**
- Full resolution image
- Bounding boxes with labels
- Detection confidence scores
- Manual verification controls
- Navigation to prev/next

### 3. Deer Profiles

**Grid View:**
```jsx
<DeerGrid>
  {deer.map(d => (
    <DeerCard key={d.id}>
      <BestPhoto src={d.best_photo_url} />
      <Name>{d.name || `Deer #${d.id.slice(0,6)}`}</Name>
      <Stats>
        <Sex icon={getSexIcon(d.sex)}>{d.sex}</Sex>
        <Sightings>{d.sighting_count} sightings</Sightings>
        <LastSeen>{formatDate(d.last_seen)}</LastSeen>
      </Stats>
    </DeerCard>
  ))}
</DeerGrid>
```

**Individual Profile:**
- Photo gallery (all sightings)
- Movement timeline map
- Sighting calendar heatmap
- Associated deer (frequently seen with)
- Edit capabilities (name, notes)

### 4. Location Management

**Map View:**
- Interactive map with camera markers
- Click for location details
- Activity heat overlay
- Trail paths between cameras

**Location Statistics:**
- Activity by hour of day
- Day of week patterns  
- Monthly trends
- Most frequent visitors
- Camera health status

### 5. Analytics Dashboard

**Population Analytics:**
```jsx
<PopulationDashboard>
  <MetricCard title="Total Unique" value={stats.total} />
  <MetricCard title="Buck:Doe Ratio" value={stats.ratio} />
  <MetricCard title="Fawn Recruitment" value={stats.recruitment} />
  <TrendChart data={stats.timeline} />
  <LocationBreakdown data={stats.by_location} />
</PopulationDashboard>
```

**Movement Patterns:**
- Sankey diagram for location transitions
- Time-based movement animations
- Individual deer tracking paths

**Activity Patterns:**
- 24-hour activity chart
- Lunar phase correlation
- Weather impact (if available)

## State Management

### Redux Store Structure
```javascript
{
  auth: {
    apiKey: string,
    permissions: string[]
  },
  images: {
    items: Image[],
    loading: boolean,
    filters: FilterState,
    pagination: PaginationState
  },
  deer: {
    profiles: Map<id, DeerProfile>,
    selected: string | null
  },
  processing: {
    queue: QueueItem[],
    active: ProcessingJob[],
    stats: ProcessingStats
  },
  ui: {
    theme: 'light' | 'dark',
    sidebarOpen: boolean,
    activeModal: string | null
  },
  realtime: {
    connected: boolean,
    lastUpdate: timestamp
  }
}
```

### Data Flow
1. **Initial Load**: Fetch core data on app mount
2. **Pagination**: Load more as needed
3. **Real-time**: WebSocket updates merged
4. **Optimistic Updates**: Immediate UI response
5. **Error Recovery**: Retry with exponential backoff

## UI Components Library

### Design System
```yaml
library: Material-UI v5
theme:
  primary: "#4A5D3F"     # Camo green
  secondary: "#8B4513"   # Saddle brown
  error: "#D32F2F"
  warning: "#F57C00"
  info: "#0288D1"
  success: "#388E3C"
  
typography:
  fontFamily: "Roboto, Arial, sans-serif"
  h1: 32px bold
  h2: 24px semibold
  h3: 20px semibold
  body1: 14px regular
  caption: 12px regular
  
spacing:
  unit: 8px
  compact: 4px
  normal: 8px
  comfortable: 16px
  
breakpoints:
  mobile: 640px
  tablet: 1024px
  desktop: 1920px
```

### Common Components

**DataTable:**
```jsx
<DataTable
  columns={[
    { field: 'id', header: 'ID', width: 100 },
    { field: 'name', header: 'Name', sortable: true },
    { field: 'sightings', header: 'Sightings', sortable: true }
  ]}
  data={deer}
  onSort={handleSort}
  onRowClick={handleRowClick}
  pagination={{
    page: 0,
    rowsPerPage: 25
  }}
/>
```

**FilterBar:**
```jsx
<FilterBar>
  <DateRangePicker />
  <LocationSelect multiple />
  <SexFilter />
  <ConfidenceSlider min={0.5} max={1.0} />
  <SearchInput placeholder="Search..." />
  <ClearFiltersButton />
</FilterBar>
```

**MetricCard:**
```jsx
<MetricCard
  title="Active Deer"
  value={47}
  change={+5}
  period="vs last week"
  icon={<DeerIcon />}
  color="success"
/>
```

## Interactions & Animations

### Transitions
```css
.card-enter {
  opacity: 0;
  transform: translateY(20px);
}
.card-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 300ms ease-out;
}
```

### Loading States
- Skeleton screens for initial loads
- Progress bars for processing
- Spinning indicators for actions
- Shimmer effects for updating data

### User Feedback
- Toast notifications for actions
- Inline validation messages
- Confirmation dialogs for destructive actions
- Success animations for completions

## Performance Optimizations

### Code Splitting
```javascript
const Analytics = lazy(() => import('./pages/Analytics'));
const DeerProfile = lazy(() => import('./pages/DeerProfile'));
```

### Image Optimization
- Lazy loading with Intersection Observer
- Progressive JPEG loading
- Thumbnail generation (server-side)
- CDN caching for processed images

### Data Virtualization
```jsx
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={800}
  itemCount={images.length}
  itemSize={200}
  width="100%"
>
  {({ index, style }) => (
    <ImageCard style={style} image={images[index]} />
  )}
</FixedSizeList>
```

### Memoization
```jsx
const expensiveChart = useMemo(
  () => generateChart(data),
  [data]
);

const DeerCard = React.memo(({ deer }) => {
  // Component only re-renders if deer prop changes
});
```

## Accessibility

### WCAG 2.1 AA Compliance
- Keyboard navigation for all interactive elements
- ARIA labels for screen readers
- Color contrast ratio >= 4.5:1
- Focus indicators visible

### Keyboard Shortcuts
```yaml
shortcuts:
  "/": Focus search
  "g d": Go to dashboard
  "g i": Go to images
  "g a": Go to analytics
  "?": Show keyboard shortcuts
  "Esc": Close modal
  "←/→": Navigate gallery
```

## Error Handling

### Error Boundaries
```jsx
<ErrorBoundary fallback={<ErrorPage />}>
  <App />
</ErrorBoundary>
```

### Network Errors
- Automatic retry with backoff
- Offline mode with cached data
- Queue actions for when online
- Clear error messages

### Validation
- Client-side validation before submit
- Server error display inline
- Field-level error messages
- Form-level error summary

## Testing Requirements

### Unit Tests
- Component rendering
- User interactions
- State management
- Utility functions

### Integration Tests
- API communication
- WebSocket connections
- Router navigation
- Form submissions

### E2E Tests
```javascript
// Cypress example
describe('Image Processing', () => {
  it('uploads and processes image', () => {
    cy.visit('/images');
    cy.get('[data-testid=upload-btn]').click();
    cy.get('input[type=file]').selectFile('test.jpg');
    cy.get('[data-testid=process-btn]').click();
    cy.contains('Processing...').should('be.visible');
    cy.contains('Completed', { timeout: 10000 });
  });
});
```

## Browser Support

### Minimum Requirements
```yaml
browsers:
  Chrome: 90+
  Firefox: 88+
  Safari: 14+
  Edge: 90+
  
features_required:
  - WebSocket
  - IntersectionObserver
  - CSS Grid
  - ES2020
```

## Deployment

### Build Configuration
```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10
        }
      }
    }
  },
  output: {
    filename: '[name].[contenthash].js',
    path: path.resolve(__dirname, 'dist')
  }
};
```

### Environment Variables
```javascript
// .env.production
REACT_APP_API_URL=http://api.thumper-counter.local
REACT_APP_WS_URL=ws://api.thumper-counter.local/ws
REACT_APP_VERSION=1.0.0
```

### Docker Configuration
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

## Future Enhancements

1. **Mobile App**
   - React Native version
   - Push notifications
   - Offline sync

2. **Advanced Visualizations**
   - 3D movement paths
   - AR camera overlay
   - VR exploration mode

3. **Collaboration**
   - Multi-user support
   - Comments on sightings
   - Shared collections

4. **AI Assistant**
   - Natural language queries
   - Anomaly alerts
   - Predictive insights

---

**Specification Status**: DRAFT
**Dependencies**: api.spec
**Next Review**: After UI implementation
