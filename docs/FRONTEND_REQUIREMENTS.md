# Frontend Requirements - Deer Tracking Dashboard

**Project:** Thumper Counter
**Sprint:** 10 (Frontend Dashboard)
**Date:** November 7, 2025
**Status:** Planning

---

## Executive Summary

Build a React-based web dashboard for the Thumper Counter deer tracking system. The frontend should provide real-time monitoring, population analytics, individual deer profiles, and image upload capabilities.

**Current System State (Post-Sprint 9):**
- Backend API: Fully operational at http://localhost:8001
- Database: PostgreSQL with pgvector for Re-ID
- ML Pipeline: YOLOv8 detection + ResNet50 Re-ID (GPU-accelerated)
- Processing Speed: 13.5 images/second
- Frontend: Basic React scaffold exists, needs complete rebuild

---

## Technology Stack

**Core Framework:**
- React 18+ with TypeScript
- Vite (build tool)
- React Router (navigation)

**UI Components:**
- Component library: TBD (Material-UI / Ant Design / Tailwind + Headless UI)
- Charts: Recharts or Chart.js
- Image viewer: React Image Gallery

**State Management:**
- React Query (API calls + caching)
- Context API (global state)

**HTTP Client:**
- Axios with base URL: http://localhost:8001

**Development:**
- Port: 3000
- Docker container: thumper_frontend (already exists)

---

## Page Structure

### 1. Dashboard (Home) - `/`

**Purpose:** High-level population metrics and quick insights

#### Top Metrics Cards (Clickable)

**Card 1: Total Population**
- **Metric:** Count of unique individual deer identified by Re-ID
- **Source:** `COUNT(DISTINCT id) FROM deer WHERE feature_vector IS NOT NULL`
- **Click Action:** Navigate to Deer Gallery filtered by "all"
- **Layout:** Large number with subtitle "Unique Deer Identified"

**Card 2: Total Sightings**
- **Metric:** Count of all deer detections across all images
- **Source:** `COUNT(*) FROM detections WHERE deer_id IS NOT NULL`
- **Click Action:** Navigate to Image Browser showing images with detections
- **Layout:** Large number with subtitle "Total Deer Sightings"

**Card 3: Bucks (Male Deer)**
- **Metric:** Count of male deer with breakdown by age class
- **Source:** `COUNT(DISTINCT deer_id) FROM detections WHERE sex IN ('young', 'mid', 'mature')`
- **Breakdown Display:**
  - Young Bucks: Class 10 detections
  - Mid Bucks: Class 6 detections
  - Mature Bucks: Class 5 detections
- **Click Action:** Navigate to Deer Gallery filtered by sex="male"
- **Layout:** Large number with expandable breakdown chart

**Card 4: Population Breakdown (Does vs Bucks)**
- **Metric:** Pie chart or bar chart showing doe vs buck ratio
- **Source:** Aggregate detection counts by sex
- **Calculation:**
  - Does: Class 3 detections
  - Bucks: Classes 5, 6, 10 combined
  - Fawns: Class 4 detections (shown separately or excluded)
- **Click Action:** Click segment to filter Deer Gallery by that sex
- **Layout:** Visual chart with percentages

**Card 5: Buck Age Distribution**
- **Metric:** Breakdown of buck population by age category
- **Source:** Detection counts grouped by young/mid/mature classes
- **Visualization:** Horizontal bar chart or donut chart
- **Click Action:** Click segment to view bucks of that age class
- **Layout:** Chart with counts and percentages

#### Sortable Options for Click-Through Views
When clicking any card, the resulting gallery/list should be sortable by:
- Most Frequently Seen (sighting_count DESC)
- Most Recently Seen (last_seen DESC)
- Last Seen (oldest first - last_seen ASC)
- First Discovered (first_seen ASC)
- Alphabetical (name ASC)

#### Additional Dashboard Sections

**Recent Activity Feed**
- Last 20 detections with thumbnails
- Show: deer name (if known), location, timestamp, confidence
- Click to view full image or deer profile

**Camera Location Status**
- List of camera locations with activity status
- Show: location name, last image received, images processed, detections today

**Processing Queue Status**
- Real-time stats from `GET /api/processing/status`
- Show: pending, processing, completed counts
- Progress bar for current batch

---

### 2. Deer Gallery - `/deer`

**Purpose:** Browse individual deer profiles (population members)

#### Gallery View

**Layout:** Grid of cards (4-6 per row, responsive)

**Each Card Contains:**
- Primary photo: Best/most recent detection crop
- Deer unique identifier (UUID or friendly name if set)
- Sex icon/badge (buck/doe/fawn/unknown)
- Sighting count: Number of detections
- Last seen: Timestamp of most recent sighting
- Location badge: Most frequented camera location

**Card Interaction:**
- Click card to open detailed profile page
- Hover to show quick stats preview

#### Filtering Options

**Sex Filter:**
- All
- Bucks (male)
- Does (female)
- Fawns (unknown sex)
- Unknown

**Age Class Filter (Bucks only):**
- All Bucks
- Young
- Mid
- Mature

**Location Filter:**
- All Locations
- [List of camera locations from database]

**Activity Filter:**
- All
- Active (seen in last 30 days)
- Inactive (not seen in 30+ days)

**Sort Options:**
- Most Frequently Seen (sighting_count DESC)
- Most Recently Seen (last_seen DESC)
- Least Recently Seen (last_seen ASC)
- First Discovered (first_seen ASC)
- Alphabetical

#### Search
- Text search by deer name or UUID

#### Pagination
- 24 deer per page
- Load more / infinite scroll option

---

### 3. Deer Profile Detail - `/deer/:id`

**Purpose:** Detailed view of individual deer's history and activity

#### Header Section

**Left Side:**
- Primary photo (largest detection crop or user-selected favorite)
- Photo gallery thumbnail strip (click to change primary)

**Right Side:**
- Deer Name (editable inline with pencil icon)
- UUID (read-only)
- Sex Badge (detected from ML model)
- Species Badge (default: "White-tailed Deer")
- Status Badge (alive/deceased/unknown - editable)
- Notes section (editable textarea for user observations)

#### Metrics Section

**Key Statistics (Cards or Grid):**
- Total Sightings: Detection count
- First Seen: Timestamp and days ago
- Last Seen: Timestamp and days ago
- Most Active Location: Camera location with highest detection count
- Activity Score: Detections per day average

#### Image Gallery

**Layout:** Grid view of all detection crops for this deer

**Features:**
- Thumbnail grid (6-12 per row)
- Click to view full-size in lightbox
- Show timestamp, location, confidence on hover
- Filter by location
- Sort by date (newest/oldest)
- Pagination or lazy load

**Display Info:**
- Detection bounding box (show on hover or permanently)
- Confidence score
- Timestamp
- Camera location name

#### Activity Timeline

**Visualization:** Timeline chart or grouped list

**Data Source:** `GET /api/deer/{id}/timeline`

**Grouping Options:**
- By Hour (24-hour activity pattern)
- By Day (activity over days)
- By Week (weekly patterns)
- By Month (seasonal patterns)

**Chart Type:**
- Line chart showing sightings over time
- Bar chart showing sightings per time unit
- Heatmap for hour-of-day analysis

#### Location Movement Map

**Data Source:** `GET /api/deer/{id}/locations`

**Visualization:**
- List view: Location name, visit count, first/last visit
- Map view (if coordinates available): Markers for each location
- Chart view: Bar chart of location frequency

**Features:**
- Click location to see images from that site
- Show movement patterns (sequence of locations over time)

#### Edit Controls

**Actions:**
- Edit Name: Inline text input
- Update Status: Dropdown (alive/deceased/unknown)
- Add/Edit Notes: Textarea (save button)
- Delete Profile: Confirmation modal (danger action)

**API Endpoints Used:**
- `PUT /api/deer/{id}` - Update deer information
- `DELETE /api/deer/{id}` - Delete deer profile

---

### 4. Image Upload - `/upload`

**Purpose:** Upload trail camera images for processing

#### Upload Interface

**Primary Upload Area:**
- Large drag-and-drop zone
- "Click to select files" button as alternative
- Support for:
  - Individual images (JPG, PNG)
  - Multiple file selection (multi-select)
  - ZIP archives containing images
- No folder upload support
- No cloud storage connections

**Visual Feedback:**
- Show file thumbnails as they're selected
- Display file count and total size
- Remove file option (X button on each thumbnail)

#### Upload Configuration

**Location Selection (Required):**
- Dropdown menu to select camera location
- Source: `GET /api/locations`
- Display: Location name
- Allow "Create New Location" option (opens modal)

**Processing Options:**
- Checkbox: "Process Immediately" (default: true)
  - If checked: Queue for detection pipeline immediately
  - If unchecked: Store images only, process later via batch API

**Advanced Options (Collapsible):**
- Override timestamp (manual date/time input)
- Add batch notes/tags

#### Metadata Extraction

**Automatic EXIF Extraction:**
Currently implemented in backend:
- Camera timestamp (EXIF DateTimeOriginal)
- Image dimensions
- Camera make/model
- GPS coordinates (if available)

**OCR Pipeline Enhancement (Future Feature):**

Question: Can we insert an OCR pipeline to extract metadata from trail camera footer overlays?

**Desired OCR Extraction:**
- Camera location name (from footer text)
- Date/time stamp (from footer overlay)
- Moon phase icon/text
- Temperature reading
- Camera ID/serial number

**Implementation Considerations:**
- Apply to both single images and batch uploads (ZIP files)
- Use extracted data for automatic filename generation
- Store OCR results in image metadata (exif_data JSON column)
- Fallback to EXIF if OCR fails

**Suggested Libraries:**
- Tesseract OCR (pytesseract)
- EasyOCR (for better accuracy with specialized fonts)
- OpenCV for image preprocessing (enhance footer region)

**Architecture:**
1. Backend receives image
2. Crop footer region (bottom 10% of image)
3. Preprocess for OCR (contrast enhancement, grayscale)
4. Extract text using OCR
5. Parse structured data (regex patterns for date/time/temp)
6. Store in exif_data JSON
7. Use for filename: `{location}_{YYYYMMDD}_{HHMMSS}.jpg`

**API Endpoint Enhancement:**
- Existing: `POST /api/images` (handles uploads)
- Add parameter: `extract_ocr=true` (default false for Sprint 10)
- Response includes: `ocr_data` field with extracted metadata

#### Upload Progress

**During Upload:**
- Progress bar for file upload (0-100%)
- Current file being uploaded (X of Y)
- Upload speed (MB/s)
- Estimated time remaining

**After Upload:**
- Success message with count of images uploaded
- Link to view uploaded images
- Option to upload more
- If "Process Immediately" checked:
  - Link to processing queue status
  - Show queued job ID

#### Error Handling

**Client-Side Validation:**
- File type check (reject non-images)
- File size limit (max 50MB per file, as per backend)
- Total batch size limit (suggest max 1000 images per upload)

**Server-Side Errors:**
- Display error messages from API
- Show which files failed (with reason)
- Allow retry for failed files
- Continue uploading successful files

#### Batch Upload (ZIP Files)

**Special Handling:**
- Upload ZIP file to backend
- Backend extracts and processes each image
- Frontend shows "Extracting archive..." status
- After extraction, show count of images found
- Process each image with same location/settings

**API Endpoint:**
- Same `POST /api/images` with `Content-Type: multipart/form-data`
- Backend detects ZIP by file extension
- Returns array of image records after extraction

---

### 5. Image Browser - `/images`

**Purpose:** Browse all uploaded trail camera images

#### Gallery View

**Layout:** Masonry grid or fixed grid (configurable)

**Each Thumbnail Shows:**
- Image thumbnail (300x200px)
- Detection count badge (if detections exist)
- Location badge
- Timestamp
- Processing status indicator (pending/processing/completed/failed)

**Interaction:**
- Click to open full-size viewer with detection overlays
- Multi-select for batch actions (future)

#### Full-Size Viewer (Lightbox)

**Features:**
- Full-resolution image display
- Detection bounding boxes overlaid (toggle on/off)
- Each bounding box labeled with:
  - Sex/age class (doe, young buck, etc.)
  - Confidence score
  - Deer name/ID if matched
- Click bounding box to navigate to deer profile
- Navigation arrows (prev/next image)
- Image metadata panel:
  - Filename
  - Timestamp
  - Location
  - Dimensions
  - EXIF data (expandable)
  - Processing status

#### Filtering Options

**Location Filter:**
- Dropdown: All locations or specific location
- Source: `GET /api/locations`

**Date Range Filter:**
- Start date picker
- End date picker
- Quick filters: Today, Last 7 days, Last 30 days, This month, All time

**Processing Status Filter:**
- All
- Pending (queued but not processed)
- Processing (currently running)
- Completed (processed successfully)
- Failed (processing errors)

**Detection Filter:**
- All Images
- With Detections (has_detections=true)
- Without Detections (has_detections=false)
- Multiple Detections (detection_count > 1)

**Sex/Class Filter:**
- All
- Images with Does
- Images with Bucks
- Images with Fawns

#### Sort Options
- Newest First (timestamp DESC)
- Oldest First (timestamp ASC)
- Most Detections (detection_count DESC)
- By Location (alphabetical)

#### Pagination
- 50 images per page (configurable)
- Page navigation
- Load more / infinite scroll option

#### Bulk Actions (Future)
- Select multiple images
- Batch reprocess
- Batch delete
- Export selection

---

### 6. Locations Management - `/locations`

**Purpose:** Manage camera locations

#### List View

**Table or Card Layout:**

**Columns/Fields:**
- Location Name
- Description
- Coordinates (if available)
- Total Images
- Last Image Received
- Detections Count
- Actions (Edit, Delete, View Images)

#### Actions

**Add New Location:**
- Button: "Add Location"
- Modal form:
  - Name (required)
  - Description (optional)
  - GPS Coordinates (optional - lat/long inputs)
  - Notes (optional)
- API: `POST /api/locations`

**Edit Location:**
- Click Edit icon
- Modal with same fields as Add
- API: `PUT /api/locations/{id}`

**Delete Location:**
- Click Delete icon
- Confirmation modal (warn if images exist)
- API: `DELETE /api/locations/{id}`

**View Images:**
- Click location name or "View Images" button
- Navigate to Image Browser filtered by this location

#### Map View (Future Enhancement)

If coordinates are available:
- Interactive map showing all camera locations
- Markers with location names
- Click marker to see location details
- Show deer movement paths between locations

---

## API Integration Summary

### Endpoints to Implement (Frontend)

**Dashboard:**
- `GET /api/deer?has_vector=true` - Count unique deer
- `GET /api/detections?has_deer=true` - Count total sightings
- Database aggregation queries for sex/age breakdown (may need new endpoint)
- `GET /api/processing/status` - Queue status

**Deer Gallery:**
- `GET /api/deer` - List deer with filters and pagination
- Query params: `sex`, `location_id`, `min_sightings`, `page`, `page_size`, `sort`

**Deer Profile:**
- `GET /api/deer/{id}` - Get deer details
- `GET /api/deer/{id}/timeline` - Activity timeline
- `GET /api/deer/{id}/locations` - Movement patterns
- `PUT /api/deer/{id}` - Update deer information
- `DELETE /api/deer/{id}` - Delete deer profile

**Image Upload:**
- `POST /api/images` - Upload images (multipart/form-data)
- `GET /api/locations` - Get locations for dropdown

**Image Browser:**
- `GET /api/images` - List images with filters
- Query params: `location_id`, `status`, `start_date`, `end_date`, `has_detections`, `page`, `page_size`
- `GET /api/images/{id}` - Get image details with detections

**Locations:**
- `GET /api/locations` - List all locations
- `POST /api/locations` - Create location
- `PUT /api/locations/{id}` - Update location
- `DELETE /api/locations/{id}` - Delete location

### Endpoints That May Need Creation

**Statistics Aggregation:**
- `GET /api/stats/population` - Population breakdown by sex/age
- `GET /api/stats/activity` - Activity metrics over time
- `GET /api/stats/locations` - Location statistics

These may be computed client-side from existing endpoints or require new backend endpoints.

---

## Design Requirements

### ASCII-Only Output (Critical)

**All UI text must use ASCII characters only:**
- NO Unicode symbols (checkmarks ✓, crosses ✗, arrows →)
- NO Emojis (deer 🦌, charts 📊)
- NO Smart quotes (use straight quotes: ' and ")
- NO Special dashes (use regular hyphen: -)
- NO Box-drawing characters

**Allowed for Status Indicators:**
- [OK], [FAIL], [WARN], [INFO] in console/logs
- Use CSS icons or SVG icons (not text characters)
- Use icon fonts (Material Icons, Font Awesome) for UI

### Responsive Design

**Breakpoints:**
- Desktop: 1200px+ (primary use case)
- Tablet: 768px - 1199px
- Mobile: < 768px (basic support)

**Priority:** Desktop first (wildlife managers will use computers)

### Loading States

**Always show loading indicators for:**
- Initial page load
- API requests
- Image loading

**Use:**
- Skeleton screens for content
- Spinners for actions
- Progress bars for uploads

### Error Handling

**User-Friendly Messages:**
- Clear explanation of what went wrong
- Suggested actions to resolve
- Retry buttons where applicable
- Contact support option (future)

**Examples:**
- "Failed to load deer profiles. Check your connection and try again."
- "Upload failed: Maximum file size is 50MB"
- "No detections found in this image"

### Real-Time Updates

**Use polling or WebSocket for:**
- Processing queue status (refresh every 5s)
- Recent activity feed (refresh every 30s)
- Detection completion notifications

**Avoid:**
- Excessive API calls
- Unnecessary re-renders
- Polling when page is not visible (use Page Visibility API)

---

## Performance Requirements

### Image Optimization

**Thumbnails:**
- Backend should serve resized thumbnails (300x200)
- Lazy load images as user scrolls
- Use `loading="lazy"` attribute

**Full-Size Images:**
- Progressive JPEG loading
- Preload next/previous images in viewer

### Data Pagination

**All Lists:**
- 20-50 items per page (configurable)
- Backend pagination (not client-side filtering of all data)
- Total count displayed

### Caching

**React Query Configuration:**
- Cache API responses for 5 minutes
- Invalidate cache on mutations (create/update/delete)
- Background refetch for stale data

### Bundle Size

**Optimization:**
- Code splitting by route
- Lazy load components
- Tree-shaking
- Minification in production

**Target:**
- Initial bundle: < 500KB gzipped
- Per-route bundles: < 200KB gzipped

---

## Accessibility

**Keyboard Navigation:**
- All actions accessible via keyboard
- Logical tab order
- Focus indicators

**Screen Reader Support:**
- Semantic HTML (nav, main, article, etc.)
- Alt text for images
- ARIA labels for complex components

**Color Contrast:**
- WCAG AA compliance minimum
- Test with contrast checker tools

---

## Development Phases

### Phase 1: Core Pages (Sprint 10)
1. Dashboard with metrics cards
2. Deer Gallery with filtering
3. Basic Deer Profile page
4. Image Upload interface
5. Locations management

### Phase 2: Enhanced Features (Sprint 11)
1. Advanced filtering and search
2. Activity timeline visualizations
3. Location movement analysis
4. Real-time processing updates
5. Bulk actions

### Phase 3: Polish & Optimization (Sprint 12)
1. Performance optimization
2. Accessibility improvements
3. Error handling refinement
4. User testing and feedback
5. Documentation

### Phase 4: Advanced Features (Future)
1. OCR pipeline integration
2. Map view for locations
3. Export functionality
4. Multi-user authentication
5. Notification system

---

## Testing Requirements

### Unit Tests
- Component rendering
- User interactions
- State management
- Utility functions

### Integration Tests
- API integration
- Navigation flows
- Form submissions
- Error scenarios

### E2E Tests (Future)
- Critical user journeys
- Upload workflow
- Deer profile management

### Browser Support
- Chrome/Edge (primary)
- Firefox
- Safari (if possible)

---

## Documentation Needs

### Developer Documentation
- Component architecture
- State management patterns
- API integration guide
- Styling conventions

### User Documentation (Future)
- Getting started guide
- Feature tutorials
- FAQ
- Troubleshooting

---

## Success Criteria

**Sprint 10 Complete When:**
- [ ] Dashboard displays accurate population metrics
- [ ] All metric cards are clickable and navigate correctly
- [ ] Deer Gallery shows all profiles with filtering and sorting
- [ ] Deer Profile page displays complete deer history
- [ ] Image Upload accepts files and archives with location selection
- [ ] Image Browser displays uploaded images with detections
- [ ] Locations can be created, edited, and deleted
- [ ] All pages are responsive (desktop + tablet)
- [ ] Loading states and error handling implemented
- [ ] ASCII-only text throughout UI
- [ ] Docker container runs successfully on port 3000

**Quality Gates:**
- No console errors in production build
- Page load time < 2s
- API response time < 500ms (backend responsibility)
- All links and navigation working
- No broken images
- Forms validate correctly

---

## Open Questions

### 1. OCR Pipeline for Trail Camera Metadata

**Question:** Should we implement OCR to extract metadata from trail camera footer overlays?

**Use Case:**
- Trail cameras overlay date/time/temp/moon phase on image bottom
- Extract this data automatically for better metadata
- Use for filename generation and searchability

**Considerations:**
- OCR accuracy varies by camera model and font
- Preprocessing required (crop footer, enhance contrast)
- Processing time added to upload workflow
- Fallback to EXIF data if OCR fails

**Recommendation:**
- Implement in Sprint 11 (after core frontend complete)
- Make it optional/configurable
- Test with representative sample images first
- Document supported camera models

### 2. Component Library Choice

**Options:**
- **Material-UI (MUI):** Comprehensive, well-documented, React-optimized
- **Ant Design:** Rich components, good for data-heavy apps
- **Tailwind + Headless UI:** Maximum flexibility, smaller bundle

**Recommendation:** Material-UI for rapid development and consistent design

### 3. Real-Time Updates Method

**Options:**
- **Polling:** Simple, works with current backend (use for Sprint 10)
- **WebSocket:** True real-time, requires backend changes (future)
- **Server-Sent Events (SSE):** One-way real-time, simpler than WebSocket

**Recommendation:** Polling for Sprint 10, consider WebSocket in Sprint 11

### 4. Statistics Endpoint Design

**Question:** Should we create dedicated `/api/stats/*` endpoints or compute client-side?

**Considerations:**
- Client-side: More flexible, but slower for large datasets
- Server-side: Faster, but requires endpoint for each metric
- Current dataset: 35,000+ images, 14 deer profiles (small enough for client-side)
- Future: May grow to 100,000+ images (need server-side aggregation)

**Recommendation:**
- Sprint 10: Compute stats client-side from `/api/deer` and `/api/detections`
- Sprint 11: Create dedicated stats endpoints if performance issues arise

---

## File Structure (Proposed)

```
src/frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Reusable components
│   │   │   ├── MetricCard.tsx
│   │   │   ├── ImageGallery.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ErrorMessage.tsx
│   │   ├── dashboard/       # Dashboard-specific
│   │   │   ├── PopulationMetrics.tsx
│   │   │   ├── RecentActivity.tsx
│   │   │   └── LocationStatus.tsx
│   │   ├── deer/           # Deer gallery/profile
│   │   │   ├── DeerCard.tsx
│   │   │   ├── DeerGallery.tsx
│   │   │   ├── DeerProfile.tsx
│   │   │   ├── ActivityTimeline.tsx
│   │   │   └── LocationMovement.tsx
│   │   ├── images/         # Image browser
│   │   │   ├── ImageGrid.tsx
│   │   │   ├── ImageViewer.tsx
│   │   │   └── DetectionOverlay.tsx
│   │   ├── upload/         # Upload interface
│   │   │   ├── UploadZone.tsx
│   │   │   ├── FileList.tsx
│   │   │   └── UploadProgress.tsx
│   │   └── locations/      # Location management
│   │       ├── LocationList.tsx
│   │       ├── LocationForm.tsx
│   │       └── LocationMap.tsx (future)
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── DeerGallery.tsx
│   │   ├── DeerDetail.tsx
│   │   ├── ImageBrowser.tsx
│   │   ├── ImageUpload.tsx
│   │   └── Locations.tsx
│   ├── hooks/
│   │   ├── useApi.ts
│   │   ├── useDeer.ts
│   │   ├── useImages.ts
│   │   └── useLocations.ts
│   ├── services/
│   │   └── api.ts          # Axios client + endpoint functions
│   ├── types/
│   │   └── index.ts        # TypeScript interfaces
│   ├── utils/
│   │   ├── formatters.ts   # Date, number formatting
│   │   └── validators.ts   # Form validation
│   ├── App.tsx
│   ├── main.tsx
│   └── routes.tsx
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

**Author:** User + Claude Code
**Date:** November 7, 2025
**Status:** Planning Document
**Next Sprint:** 10 - Frontend Implementation
