# Sprint 10: Frontend Dashboard Implementation

**Date:** November 7, 2025
**Sprint:** 10 (Frontend)
**Branch:** TBD (create: 006-frontend-dashboard)
**Status:** Planning
**Previous Sprint:** Sprint 9 - Re-ID GPU Optimization (Complete)

---

## Sprint Goal

Build a fully functional React-based dashboard for the Thumper Counter deer tracking system, providing wildlife managers with tools to monitor population, browse deer profiles, upload images, and manage camera locations.

---

## Prerequisites

**Completed Sprints:**
- [x] Sprint 1-2: Database + API foundation
- [x] Sprint 3: GPU acceleration + batch processing
- [x] Sprint 4: Multi-class YOLOv8 training (sex/age)
- [x] Sprint 5: Re-identification with ResNet50
- [x] Sprint 6: Pipeline integration
- [x] Sprint 7: OCR analysis (research)
- [x] Sprint 8: Database optimization + deduplication
- [x] Sprint 9: Re-ID GPU optimization

**System State:**
- Backend API: Operational at http://localhost:8001
- Database: 35,251 images, 29,735 detections, 14 deer profiles
- ML Pipeline: 13.5 images/second throughput
- Frontend: Basic scaffold exists, needs rebuild

**Current Frontend Status:**
- Docker container: thumper_frontend (running on port 3000)
- Framework: React 18+ with Vite
- Status: Basic scaffold, no functional pages yet

---

## Objectives

### Primary Goals
1. Build Dashboard page with population metrics
2. Implement Deer Gallery with filtering and sorting
3. Create Deer Profile detail page
4. Build Image Upload interface
5. Implement Image Browser with detection overlays
6. Create Location management page

### Secondary Goals
1. Integrate with all existing backend APIs
2. Implement real-time processing status updates
3. Add responsive design (desktop + tablet)
4. Implement proper error handling and loading states

### Success Criteria
- [ ] Dashboard displays accurate metrics (population, sightings, buck/doe breakdown)
- [ ] All metric cards are clickable and navigate to filtered views
- [ ] Deer Gallery shows all profiles with working filters
- [ ] Deer Profile page displays complete history and timeline
- [ ] Image Upload accepts files/archives with location selection
- [ ] Image Browser shows uploaded images with detection overlays
- [ ] Location CRUD operations working
- [ ] No console errors in production build
- [ ] Page load time < 2 seconds
- [ ] ASCII-only text throughout (no emojis/Unicode)

---

## Architecture Decisions

### Technology Stack

**Core:**
- React 18.2+ with TypeScript
- Vite 4+ (build tool)
- React Router 6 (navigation)

**UI Framework:**
- Material-UI (MUI) v5 - Selected for:
  - Comprehensive component library
  - Excellent documentation
  - Built-in theming
  - Good TypeScript support
  - Suitable for data-heavy applications

**State Management:**
- React Query v4 (API calls, caching, background refetch)
- Context API (global UI state - theme, user prefs)
- Local useState/useReducer (component state)

**HTTP Client:**
- Axios with interceptors
- Base URL: http://localhost:8001

**Charts/Visualizations:**
- Recharts (React-native charts, good MUI integration)

**Image Viewer:**
- React Image Gallery or custom lightbox with detection overlays

**Form Validation:**
- React Hook Form + Yup

**Date Handling:**
- date-fns (lighter than moment.js)

### API Integration Strategy

**React Query Configuration:**
```typescript
// Cache API responses for 5 minutes
// Automatic background refetch when stale
// Optimistic updates for mutations
// Error retry with exponential backoff
```

**Endpoints to Integrate:**
- GET /api/deer - Deer profiles list
- GET /api/deer/{id} - Deer detail
- GET /api/deer/{id}/timeline - Activity timeline
- GET /api/deer/{id}/locations - Movement patterns
- POST /api/deer - Create manual profile
- PUT /api/deer/{id} - Update deer
- DELETE /api/deer/{id} - Delete deer
- GET /api/images - Image list with filters
- GET /api/images/{id} - Image detail
- POST /api/images - Upload images
- GET /api/locations - Location list
- POST /api/locations - Create location
- PUT /api/locations/{id} - Update location
- DELETE /api/locations/{id} - Delete location
- GET /api/processing/status - Queue status
- POST /api/processing/batch - Queue batch processing

**New Endpoints Needed (to create in this sprint):**
- GET /api/stats/population - Population breakdown by sex/age
- GET /api/stats/dashboard - Dashboard metrics (total deer, sightings, etc.)

### Component Architecture

**Page Components:**
- Dashboard - Top-level metrics and activity feed
- DeerGallery - Grid of deer profile cards
- DeerDetail - Individual deer profile page
- ImageBrowser - Grid of uploaded images
- ImageUpload - Upload interface
- Locations - Location management

**Shared Components:**
- MetricCard - Clickable stat card with large number
- ImageGallery - Thumbnail grid with lightbox
- LoadingSpinner - Loading indicator
- ErrorMessage - Error display with retry
- FilterPanel - Reusable filter/sort UI
- Pagination - Page navigation

**Layout Components:**
- AppLayout - Navigation bar + content area
- Sidebar - Navigation menu (optional)
- TopBar - Header with breadcrumbs

### Routing Structure

```
/ - Dashboard
/deer - Deer Gallery
/deer/:id - Deer Profile Detail
/images - Image Browser
/upload - Image Upload
/locations - Location Management
```

### Styling Approach

**MUI Theming:**
- Custom theme with earth tones (nature-appropriate)
- Light mode primary (dark mode future)
- Consistent spacing and typography
- Responsive breakpoints: 600/900/1200/1536

**Custom CSS:**
- Minimal custom CSS (leverage MUI components)
- CSS modules for component-specific styles
- No global styles (except CSS reset)

---

## Tasks Breakdown

### Task 1: Project Setup & Configuration
**Estimated Time:** 2 hours

**Steps:**
1. Verify current frontend scaffold state
2. Install dependencies:
   - @mui/material @mui/icons-material
   - @tanstack/react-query
   - axios
   - react-router-dom
   - recharts
   - react-hook-form
   - yup
   - date-fns
3. Configure Vite for TypeScript + MUI
4. Set up React Query client
5. Configure Axios base client with interceptors
6. Create directory structure:
   - components/, pages/, hooks/, services/, types/, utils/
7. Set up routing with React Router
8. Create base layout component

**Acceptance:**
- [ ] All dependencies installed
- [ ] TypeScript configured
- [ ] Routing working (empty pages)
- [ ] Layout renders correctly
- [ ] No build errors

---

### Task 2: Dashboard Page
**Estimated Time:** 6 hours

**Components to Build:**
1. **MetricCard** (shared component)
   - Display large number with label
   - Clickable with navigation
   - Loading skeleton state
   - Props: title, value, subtitle, onClick, loading

2. **DashboardMetrics** (container)
   - Top row: 5 metric cards
   - API calls to get data:
     - Total deer count
     - Total sightings count
     - Buck count with age breakdown
     - Population breakdown chart
   - Handle click navigation to filtered views

3. **RecentActivityFeed**
   - List recent 20 detections
   - Show thumbnail, deer name, location, timestamp
   - Click to view image or deer profile
   - Auto-refresh every 30 seconds

4. **ProcessingQueueStatus**
   - Real-time queue stats from /api/processing/status
   - Progress bar
   - Polling every 5 seconds
   - Show: pending, processing, completed counts

5. **LocationStatusList**
   - List camera locations with activity stats
   - Show: name, last image, images today, detections today
   - Click to view images from that location

**API Integration:**
- GET /api/deer?has_vector=true (count for total population)
- GET /api/detections?has_deer=true (count for total sightings)
- GET /api/stats/dashboard (new endpoint - create in backend)
- GET /api/processing/status (queue stats)
- GET /api/images?limit=20&sort=timestamp_desc (recent activity)
- GET /api/locations (location list with stats)

**Acceptance:**
- [ ] All 5 metric cards display correct data
- [ ] Cards navigate to correct filtered views on click
- [ ] Recent activity feed shows last 20 detections
- [ ] Processing queue status updates in real-time
- [ ] Location status list displays all cameras
- [ ] Responsive layout (desktop + tablet)
- [ ] Loading states for all async data
- [ ] Error handling with retry option

---

### Task 3: Deer Gallery Page
**Estimated Time:** 5 hours

**Components to Build:**
1. **DeerCard** (individual deer card)
   - Primary photo thumbnail
   - Deer name or UUID
   - Sex badge (buck/doe/fawn/unknown)
   - Sighting count
   - Last seen timestamp
   - Most frequent location
   - Click to navigate to detail page
   - Hover for quick stats preview

2. **DeerGallery** (grid container)
   - Grid layout (4-6 cards per row, responsive)
   - Pagination (24 deer per page)
   - Empty state if no deer found

3. **DeerFilters** (filter panel)
   - Sex filter: All / Bucks / Does / Fawns / Unknown
   - Age filter (bucks only): All / Young / Mid / Mature
   - Location filter: Dropdown of all locations
   - Activity filter: All / Active (30 days) / Inactive
   - Sort dropdown: Most seen / Recently seen / Least recent / First discovered / Alphabetical
   - Search input: Filter by name or UUID
   - Clear filters button

**API Integration:**
- GET /api/deer with query params:
  - sex (filter by sex)
  - location_id (filter by location)
  - min_sightings (activity filter)
  - sort (sort option)
  - search (text search)
  - page, page_size (pagination)
- GET /api/locations (for location dropdown)

**State Management:**
- URL query params for filters (shareable links)
- React Query for API calls with caching
- Debounced search input

**Acceptance:**
- [ ] Gallery displays all deer profiles in grid
- [ ] All filters work correctly
- [ ] Sort options apply correctly
- [ ] Search filters by name/UUID
- [ ] Pagination works (prev/next, page numbers)
- [ ] Cards navigate to detail page on click
- [ ] Responsive grid (adjusts to screen size)
- [ ] Loading skeletons while fetching
- [ ] Empty state if no results

---

### Task 4: Deer Profile Detail Page
**Estimated Time:** 7 hours

**Components to Build:**
1. **DeerProfileHeader**
   - Left: Primary photo + thumbnail strip
   - Right: Deer info card
     - Name (editable inline)
     - UUID (read-only)
     - Sex badge
     - Species badge
     - Status dropdown (alive/deceased/unknown)
     - Notes textarea (editable)
     - Save button
   - Edit mode toggle

2. **DeerMetrics** (stats grid)
   - Total sightings
   - First seen (date + days ago)
   - Last seen (date + days ago)
   - Most active location
   - Activity score (sightings per day)

3. **DeerImageGallery**
   - Grid of all detection crops for this deer
   - Thumbnail click opens lightbox
   - Show metadata on hover: timestamp, location, confidence
   - Filter by location
   - Sort by date (newest/oldest)
   - Pagination or lazy load

4. **ActivityTimeline**
   - Chart showing sightings over time
   - Grouping options: Hour / Day / Week / Month
   - Line chart or bar chart
   - API: GET /api/deer/{id}/timeline

5. **LocationMovement**
   - List or chart of locations visited
   - Show: location name, visit count, first/last visit
   - API: GET /api/deer/{id}/locations

6. **DeerProfileActions**
   - Edit button (toggle edit mode)
   - Delete button (confirmation modal)

**API Integration:**
- GET /api/deer/{id} - Deer details
- GET /api/deer/{id}/timeline - Activity timeline
- GET /api/deer/{id}/locations - Movement patterns
- PUT /api/deer/{id} - Update deer (name, status, notes)
- DELETE /api/deer/{id} - Delete deer

**State Management:**
- React Query for data fetching
- Local state for edit mode
- Form state with React Hook Form
- Optimistic updates for mutations

**Acceptance:**
- [ ] Header displays deer info correctly
- [ ] Name editable inline with save button
- [ ] Status and notes editable
- [ ] All metrics display correctly
- [ ] Image gallery shows all detection crops
- [ ] Lightbox works with navigation
- [ ] Activity timeline chart renders correctly
- [ ] Location movement data displays
- [ ] Grouping options work for timeline
- [ ] Delete button shows confirmation modal
- [ ] Updates save correctly to backend
- [ ] Responsive layout

---

### Task 5: Image Upload Page
**Estimated Time:** 6 hours

**Components to Build:**
1. **UploadZone** (drag-drop area)
   - Large drop zone with "Drag files here or click to browse"
   - Accept: .jpg, .png, .zip
   - Multiple file selection
   - Visual feedback on drag over
   - Show error if invalid file type

2. **FileList** (selected files display)
   - Thumbnail preview for each file
   - Show filename, size
   - Remove button (X icon)
   - Total count and size summary

3. **UploadConfig** (configuration panel)
   - Location dropdown (required)
   - "Process Immediately" checkbox (default true)
   - Advanced options (collapsible):
     - Override timestamp (date/time picker)
     - Batch notes/tags input

4. **UploadProgress** (during upload)
   - Overall progress bar (0-100%)
   - Current file progress (X of Y)
   - Upload speed (MB/s)
   - Estimated time remaining
   - Cancel button

5. **UploadResults** (after upload)
   - Success count
   - Failed count (with error messages)
   - Link to view uploaded images
   - Link to processing queue
   - Upload more button

**API Integration:**
- GET /api/locations (for location dropdown)
- POST /api/images (multipart/form-data upload)
  - files: File[] (images or ZIP archive)
  - location_id: UUID (selected location)
  - process_immediately: boolean
- GET /api/processing/status (if queued for processing)

**File Handling:**
- Client-side validation:
  - File type (image/jpeg, image/png, application/zip)
  - File size (max 50MB per file)
  - Total batch size (suggest max 1000 images)
- Chunk upload for large files (optional)
- Progress tracking with Axios onUploadProgress

**Acceptance:**
- [ ] Drag-drop works for files
- [ ] Click to browse works
- [ ] File type validation (reject non-images/zips)
- [ ] File size validation (max 50MB)
- [ ] Preview thumbnails for selected files
- [ ] Remove file button works
- [ ] Location dropdown populated from API
- [ ] Process immediately checkbox toggles
- [ ] Upload progress bar updates accurately
- [ ] Success/error messages display correctly
- [ ] Link to uploaded images works
- [ ] Responsive layout

---

### Task 6: Image Browser Page
**Estimated Time:** 6 hours

**Components to Build:**
1. **ImageGrid**
   - Masonry or fixed grid layout
   - Thumbnail for each image (300x200px)
   - Detection count badge (if > 0)
   - Location badge
   - Timestamp
   - Processing status indicator
   - Lazy load images
   - Click to open viewer

2. **ImageViewer** (lightbox)
   - Full-resolution image display
   - Detection bounding boxes overlay (toggle on/off)
   - Bounding box labels:
     - Sex/age class
     - Confidence score
     - Deer name (if matched)
   - Click box to navigate to deer profile
   - Previous/Next navigation arrows
   - Metadata panel (expandable):
     - Filename
     - Timestamp
     - Location
     - Dimensions
     - EXIF data
     - Processing status

3. **ImageFilters** (filter panel)
   - Location dropdown
   - Date range picker (start/end)
   - Quick date filters: Today / Last 7 days / Last 30 days / This month / All
   - Processing status: All / Pending / Processing / Completed / Failed
   - Detection filter: All / With detections / Without detections / Multiple detections
   - Sex/class filter: All / Does / Bucks / Fawns
   - Sort: Newest / Oldest / Most detections / By location

4. **Pagination**
   - Page numbers
   - Prev/Next buttons
   - Page size selector (25/50/100)
   - Total count display

**API Integration:**
- GET /api/images with query params:
  - location_id
  - start_date, end_date
  - status (processing status)
  - has_detections (boolean)
  - detection_count_min (for multiple detections)
  - sort
  - page, page_size
- GET /api/images/{id} (for full details in viewer)

**State Management:**
- URL query params for filters
- React Query for API calls
- Local state for viewer open/close
- Preload next/previous images

**Acceptance:**
- [ ] Grid displays all images with thumbnails
- [ ] All filters work correctly
- [ ] Date range picker functional
- [ ] Sort options apply correctly
- [ ] Click image opens viewer
- [ ] Viewer shows full-size image
- [ ] Detection bounding boxes overlay correctly
- [ ] Box labels show sex/class/confidence
- [ ] Click box navigates to deer profile
- [ ] Previous/Next navigation works
- [ ] Metadata panel shows all info
- [ ] Toggle detection overlay works
- [ ] Pagination works correctly
- [ ] Lazy loading works (no loading all images at once)
- [ ] Responsive grid

---

### Task 7: Location Management Page
**Estimated Time:** 4 hours

**Components to Build:**
1. **LocationList** (table or card grid)
   - Columns:
     - Location Name
     - Description
     - Coordinates (lat/long if available)
     - Total Images
     - Last Image Received
     - Detections Count
     - Actions (Edit, Delete, View Images)
   - Sort by any column
   - Click row to view images from location

2. **LocationForm** (modal or slide-in panel)
   - Name input (required)
   - Description textarea (optional)
   - Coordinates inputs (lat/long, optional)
   - Notes textarea (optional)
   - Save/Cancel buttons
   - Validation with React Hook Form + Yup

3. **LocationDeleteConfirmation** (modal)
   - Warning message (especially if images exist)
   - Confirm/Cancel buttons

4. **AddLocationButton**
   - Floating action button or header button
   - Opens LocationForm in create mode

**API Integration:**
- GET /api/locations - List all locations
- POST /api/locations - Create new location
- PUT /api/locations/{id} - Update location
- DELETE /api/locations/{id} - Delete location

**State Management:**
- React Query for CRUD operations
- Optimistic updates for better UX
- Cache invalidation after mutations

**Acceptance:**
- [ ] List displays all locations
- [ ] Sort by columns works
- [ ] Add location button opens form
- [ ] Create location works
- [ ] Edit location works
- [ ] Delete location shows confirmation
- [ ] Delete location works
- [ ] View images link navigates to Image Browser filtered by location
- [ ] Form validation works (name required)
- [ ] Success/error messages display
- [ ] Responsive layout

---

### Task 8: Backend API Endpoints (New)
**Estimated Time:** 3 hours

**Endpoints to Create:**

1. **GET /api/stats/dashboard**
   - Returns dashboard metrics:
     - total_deer: Count of unique deer with feature vectors
     - total_sightings: Count of detections with deer_id
     - total_images: Count of all images
     - images_processed: Count of completed images
     - images_pending: Count of pending images
     - buck_count: Count of male deer
     - doe_count: Count of female deer
     - fawn_count: Count of fawn deer
     - buck_breakdown: { young: X, mid: Y, mature: Z }
   - Cache for 5 minutes

2. **GET /api/stats/population**
   - Returns population breakdown by sex and age class
   - Group by sex: male, female, unknown
   - Group male by age: young, mid, mature
   - Include detection counts and percentages

**Implementation:**
- File: src/backend/api/stats.py (new)
- Use SQLAlchemy queries with joins
- Add to router in main.py
- Document in OpenAPI schema

**Acceptance:**
- [ ] /api/stats/dashboard returns correct metrics
- [ ] /api/stats/population returns breakdown
- [ ] Responses cached appropriately
- [ ] OpenAPI docs updated
- [ ] Tested with curl or Postman

---

### Task 9: Testing & Polish
**Estimated Time:** 4 hours

**Testing:**
1. Manual testing of all pages
2. Test with real data (35,000 images, 14 deer)
3. Test edge cases:
   - No deer profiles yet
   - No images uploaded
   - No detections on image
   - Failed processing status
4. Browser compatibility (Chrome, Firefox, Edge)
5. Responsive testing (desktop, tablet, mobile)

**Polish:**
1. Add loading skeletons for all async content
2. Improve error messages (user-friendly)
3. Add empty states ("No deer found", etc.)
4. Verify ASCII-only text (no emojis)
5. Optimize images (lazy loading, responsive sizes)
6. Reduce console warnings/errors
7. Test performance (page load < 2s)
8. Add keyboard navigation support
9. Verify accessibility (ARIA labels, alt text)

**Documentation:**
1. Update README with frontend setup instructions
2. Document component architecture
3. Create API integration guide
4. Add troubleshooting section

**Acceptance:**
- [ ] All pages tested with real data
- [ ] Edge cases handled gracefully
- [ ] Works in Chrome, Firefox, Edge
- [ ] Responsive on desktop and tablet
- [ ] Loading states everywhere
- [ ] Error handling with retry
- [ ] Empty states where needed
- [ ] No emojis or Unicode characters in UI
- [ ] Page load < 2 seconds
- [ ] No console errors in production build
- [ ] Documentation updated

---

## Technical Challenges & Solutions

### Challenge 1: Real-Time Processing Updates

**Problem:** Need to show processing queue status in real-time without overwhelming backend

**Solution:**
- Use React Query with refetchInterval (5 seconds)
- Only poll when Dashboard page is active (Page Visibility API)
- Use staleTime and cacheTime to reduce unnecessary requests
- Consider WebSocket in Sprint 11 for true real-time

### Challenge 2: Large Image Dataset Performance

**Problem:** 35,000+ images could be slow to browse/filter

**Solution:**
- Backend pagination (not client-side filtering)
- Lazy load images in grid (IntersectionObserver)
- Thumbnail generation on backend (serve 300x200 instead of full-size)
- Virtual scrolling for very long lists (react-window)
- Index database columns used in filters

### Challenge 3: Detection Overlay Rendering

**Problem:** Drawing bounding boxes on images in browser

**Solution:**
- Use HTML5 Canvas or SVG overlay
- Calculate box positions relative to displayed image size
- Handle image scaling (full-size vs thumbnail)
- Make boxes interactive (click to navigate)

### Challenge 4: Metric Card Click-Through Navigation

**Problem:** Clicking metric card should navigate to filtered view (e.g., "Does" card -> Deer Gallery showing only does)

**Solution:**
- Use React Router with URL query params
- MetricCard component accepts `onClick` with navigation
- Dashboard passes navigation functions to cards
- Example: `navigate('/deer?sex=female')`
- DeerGallery reads URL params on mount
- URL params preserved for shareable links

### Challenge 5: File Upload with Progress

**Problem:** Need accurate progress for multi-file and ZIP uploads

**Solution:**
- Axios onUploadProgress callback
- Track per-file and overall progress
- For ZIP: Show extraction progress (backend needs to support streaming updates)
- Cancel upload: Axios CancelToken

---

## Performance Targets

**Page Load Times:**
- Dashboard: < 1.5s
- Deer Gallery: < 2s
- Deer Profile: < 1.5s
- Image Browser: < 2s
- Image Upload: < 1s
- Locations: < 1s

**API Response Times (Backend):**
- List endpoints: < 200ms
- Detail endpoints: < 100ms
- Stats endpoints: < 500ms (cached)
- Image upload: Variable (depends on size)

**Bundle Sizes:**
- Initial bundle: < 500KB gzipped
- Per-route chunks: < 200KB gzipped
- Total (all routes loaded): < 1.5MB gzipped

**Optimization Strategies:**
- Code splitting by route
- Lazy load components not needed immediately
- Tree-shaking (Vite does this automatically)
- Image optimization (serve thumbnails, lazy load)
- Memoization for expensive computations
- React Query caching to reduce API calls

---

## Rollout Plan

### Phase 1: Core Pages (Week 1)
- Dashboard with basic metrics
- Deer Gallery with filtering
- Image Upload interface
- Locations management

### Phase 2: Advanced Features (Week 2)
- Deer Profile detail page
- Image Browser with detection overlay
- Activity timeline charts
- Location movement analysis

### Phase 3: Polish & Testing (Week 3)
- Responsive design refinement
- Error handling improvement
- Performance optimization
- User testing and feedback
- Documentation

---

## Success Metrics

**Functionality:**
- [ ] All 6 pages functional and accessible
- [ ] All API endpoints integrated
- [ ] All user actions working (CRUD operations)
- [ ] Real-time updates for processing queue

**Performance:**
- [ ] Page load < 2 seconds
- [ ] No lag when browsing 35k images (paginated)
- [ ] Smooth scrolling and interactions
- [ ] < 500KB initial bundle size

**Quality:**
- [ ] No console errors in production
- [ ] Proper error handling everywhere
- [ ] Loading states for all async operations
- [ ] Empty states where appropriate
- [ ] ASCII-only text (no Unicode/emojis)

**User Experience:**
- [ ] Intuitive navigation
- [ ] Clear visual hierarchy
- [ ] Responsive design (desktop + tablet)
- [ ] Keyboard accessible
- [ ] Helpful error messages with recovery actions

---

## Risks & Mitigations

**Risk 1: Timeline Overrun**
- **Likelihood:** Medium
- **Impact:** High
- **Mitigation:** Prioritize core pages (Dashboard, Deer Gallery, Image Upload) first; defer advanced features (activity timeline charts) to Sprint 11 if needed

**Risk 2: Performance Issues with Large Dataset**
- **Likelihood:** Low (proper pagination implemented)
- **Impact:** Medium
- **Mitigation:** Backend pagination, lazy loading, thumbnail serving, virtual scrolling if needed

**Risk 3: Detection Overlay Complexity**
- **Likelihood:** Medium
- **Impact:** Low
- **Mitigation:** Use Canvas for drawing, test with various image sizes, fallback to simple overlay if performance issues

**Risk 4: Scope Creep**
- **Likelihood:** High (user may request additional features)
- **Impact:** Medium
- **Mitigation:** Strict adherence to Sprint 10 scope; document additional requests for Sprint 11+

---

## Next Sprint Preview (Sprint 11)

**Potential Features:**
1. OCR pipeline integration for trail camera metadata extraction
2. Advanced analytics (activity heatmaps, territory analysis)
3. WebSocket for true real-time updates
4. Map view for camera locations (if coordinates available)
5. Export functionality (CSV, PDF reports)
6. Notification system (alerts for new deer, rare sightings)
7. User authentication and multi-user support
8. Batch actions in Image Browser (reprocess, delete, tag)
9. Image comparison view (side-by-side deer profiles)
10. Mobile responsive improvements

---

## Dependencies

**External Services:**
- Backend API at http://localhost:8001 (must be running)
- PostgreSQL database (must have data)
- Redis (for API caching - optional)

**Team Dependencies:**
- None (solo development with Claude Code)

**Hardware Requirements:**
- Development machine: 8GB+ RAM, modern CPU
- GPU not required for frontend (backend uses GPU for ML)

---

## Deliverables

**Code:**
- [ ] Fully functional React frontend
- [ ] All 6 pages implemented
- [ ] Component library and shared components
- [ ] API integration layer
- [ ] TypeScript types for all API responses
- [ ] Responsive styling with MUI theming

**Documentation:**
- [ ] README with setup instructions
- [ ] Component architecture document
- [ ] API integration guide
- [ ] Troubleshooting guide
- [ ] Sprint 10 summary document (post-completion)

**Testing:**
- [ ] Manual testing completed
- [ ] Edge cases handled
- [ ] Browser compatibility verified
- [ ] Performance benchmarks met

**Deployment:**
- [ ] Docker container updated and tested
- [ ] Production build verified
- [ ] Port 3000 accessible

---

## Open Questions

1. **Component Library Confirmation:** Is Material-UI (MUI) acceptable, or prefer alternative (Ant Design, Tailwind)?
   - Recommendation: MUI for rapid development

2. **Dark Mode:** Implement dark mode in Sprint 10 or defer to Sprint 11?
   - Recommendation: Defer to Sprint 11 (light mode only for now)

3. **Statistics Endpoints:** Create dedicated /api/stats/* endpoints or compute client-side?
   - Recommendation: Create backend endpoints for better performance

4. **OCR Integration Timing:** Implement OCR in Sprint 10 or defer to Sprint 11?
   - Recommendation: Defer to Sprint 11 (core frontend first)

5. **Map View for Locations:** Use map library (Leaflet, Google Maps) or simple list view?
   - Recommendation: List view for Sprint 10, map in Sprint 11 if coordinates available

---

## Sprint Retrospective (Post-Sprint)

To be completed after Sprint 10:
- What went well?
- What challenges did we face?
- What would we do differently?
- What did we learn?
- Performance metrics achieved
- User feedback (if applicable)

---

**Author:** User + Claude Code
**Date:** November 7, 2025
**Status:** Planning Document
**Estimated Duration:** 2-3 weeks
**Target Completion:** November 28, 2025
