# Research: Technology Decisions for Rut Season Analysis

**Feature**: 008-rut-season-analysis
**Phase**: Phase 0 (Research)
**Date**: 2025-11-08
**Status**: Decisions Finalized

## Purpose

This document records technology selection decisions for the rut season analysis feature. Each decision includes evaluation criteria, alternatives considered, and rationale for final choice.

---

## Decision 1: PDF Generation Library

### Question
Which Python library should we use for generating seasonal analysis PDF reports?

### Requirement Context
- Generate multi-page reports with embedded charts (PNG images)
- Include statistical tables and plain language insights
- Target file size: <5MB for 50 charts + 1000 rows of data
- Output must be readable by non-technical wildlife researchers

### Alternatives Considered

#### Option A: ReportLab
**Pros:**
- Low-level control over PDF layout and styling
- Excellent for programmatic PDF generation
- Small file sizes (optimized PDF compression)
- Mature library with extensive documentation
- Direct chart image embedding (PNG/JPEG)
- No external dependencies (pure Python)

**Cons:**
- Steeper learning curve (manual positioning)
- More code required for complex layouts
- No HTML-to-PDF conversion

**File Size Estimate:**
- 50 charts (PNG, 800x600, optimized): ~15MB raw, ~3MB compressed
- 1000 rows table: ~500KB
- **Total: ~3.5MB** (within 5MB constraint)

#### Option B: WeasyPrint
**Pros:**
- HTML/CSS to PDF conversion (easier styling)
- Familiar web development workflow
- Good for complex layouts with CSS Grid/Flexbox
- Automatic pagination

**Cons:**
- Requires external dependencies (Cairo, Pango)
- Larger file sizes (less optimized compression)
- HTML rendering overhead increases generation time
- Docker image size increases significantly

**File Size Estimate:**
- Same content as ReportLab: **~5-7MB** (less optimized compression)
- Risk of exceeding 5MB constraint

### Decision: ReportLab

**Rationale:**
1. **File Size**: Consistently produces smaller PDFs (3.5MB vs 5-7MB)
2. **Dependencies**: No external C libraries required (simpler Docker setup)
3. **Performance**: Faster generation (<10 seconds vs 15-20 seconds for WeasyPrint)
4. **Control**: Low-level control allows file size optimization (image compression, font embedding)
5. **Project Fit**: Statistical reports have structured layouts (tables, charts) that don't require complex HTML/CSS

**Implementation Plan:**
- Use `reportlab.platypus` for document flow (Paragraph, Table, Image, PageBreak)
- Embed Recharts output as PNG images (pre-rendered in frontend or backend)
- Apply image compression: JPEG quality=85 for charts
- Use standard fonts (no custom font embedding)

**Risk Mitigation:**
- If file size exceeds 5MB: reduce chart count per report or paginate into multiple PDFs
- Test with real 50-chart report during implementation to validate estimate

---

## Decision 2: Frontend Chart Library

### Question
Which React charting library should we use for interactive timeline visualizations?

### Requirement Context
- Display timeline charts with 5,000+ data points (detection counts by month/week/day)
- Render time: <1 second for 5,000 points
- Interactive drill-down (click chart to filter image gallery)
- Responsive design (desktop: 1280x720 minimum)
- Existing project already uses Material-UI v5

### Alternatives Considered

#### Option A: Recharts
**Pros:**
- Built for React (component-based, declarative API)
- Excellent documentation and examples
- Responsive by default
- Smooth animations
- Good performance with 5,000 data points
- Already used in project (Sprint 10 - Deer Profile timeline)
- MIT license (permissive)

**Cons:**
- Limited customization compared to D3.js
- Some advanced chart types not available

**Performance:**
- 5,000 data points (line chart): **~300-500ms** render time
- Meets <1 second requirement with margin

#### Option B: Chart.js (via react-chartjs-2)
**Pros:**
- Very popular (widely used)
- Canvas-based (potentially faster for large datasets)
- More chart types available
- Good documentation

**Cons:**
- Not React-native (requires wrapper library)
- Less declarative API (imperative chart configuration)
- Harder to integrate with React state updates
- Performance similar to Recharts for 5,000 points (~400-600ms)

**Performance:**
- 5,000 data points (line chart): **~400-600ms** render time
- Meets requirement but no significant advantage over Recharts

### Decision: Recharts

**Rationale:**
1. **Consistency**: Already used in project (Sprint 10 Deer Profile timeline)
2. **React Integration**: Declarative component-based API fits React paradigm
3. **Performance**: Meets <1 second requirement (300-500ms for 5,000 points)
4. **Developer Experience**: Team familiarity from Sprint 10
5. **Maintainability**: Single charting library across entire frontend

**Implementation Plan:**
- Use `<LineChart>` for activity timeline (detections over time)
- Use `<BarChart>` for comparison views (side-by-side periods)
- Implement drill-down via `onClick` event on chart elements
- Apply data sampling if >10,000 points (show every Nth point)

**Performance Optimization:**
- Debounce chart updates on filter changes (300ms delay)
- Use `React.memo` to prevent unnecessary re-renders
- Lazy load chart data (fetch on demand, not on page load)

---

## Decision 3: Date Picker Component

### Question
Which React date picker component should we use for visual calendar selection?

### Requirement Context
- Date range selection (start date + end date)
- Visual calendar interface (no manual text entry)
- Month-level granularity sufficient
- Minimum screen resolution: 1280x720 (desktop)
- Must integrate with existing Material-UI v5 theme

### Alternatives Considered

#### Option A: Material-UI DatePicker (MUI X)
**Pros:**
- Native MUI integration (matches existing UI design)
- Consistent theme styling (olive green, saddle brown)
- Accessible (keyboard navigation, screen reader support)
- Built-in range selection (`DateRangePicker` component)
- Responsive mobile calendar view
- Already installed in project (`@mui/x-date-pickers`)

**Cons:**
- Requires additional peer dependency (`dayjs` or `date-fns`)
- Larger bundle size than standalone pickers

**Bundle Size:**
- `@mui/x-date-pickers`: ~45KB gzipped
- `dayjs`: ~7KB gzipped
- **Total: ~52KB** (acceptable for date functionality)

#### Option B: react-date-picker
**Pros:**
- Lightweight (~15KB gzipped)
- Standalone component (no framework dependency)
- Simple API

**Cons:**
- Requires custom styling to match MUI theme
- No built-in range selection (need to manage two pickers)
- Less accessible than MUI (no keyboard navigation)
- Doesn't match existing UI design language

**Bundle Size:**
- `react-date-picker`: ~15KB gzipped
- Custom styling effort: **significant**

### Decision: Material-UI DatePicker (MUI X)

**Rationale:**
1. **Consistency**: Matches existing Material-UI v5 design system
2. **Accessibility**: Built-in keyboard navigation and screen reader support
3. **Range Selection**: Native `DateRangePicker` component for start/end dates
4. **Maintainability**: Single UI framework reduces styling complexity
5. **User Experience**: Familiar MUI interactions for wildlife researchers

**Implementation Plan:**
- Use `<DateRangePicker>` from `@mui/x-date-pickers`
- Configure with `dayjs` adapter (smaller than `date-fns`)
- Apply custom theme colors (olive green for selected dates)
- Set `minDate` and `maxDate` to constrain selection to dataset bounds
- Display selected range preview with estimated image count

**Bundle Impact:**
- Total bundle size increase: ~52KB gzipped (acceptable trade-off for UX)

---

## Decision 4: Aggregation Strategy

### Question
Which approach should we use for date range queries and statistical aggregation?

### Requirement Context
- Query images by date range (Sept 1 - Jan 31)
- Aggregate detection counts by month/week/day
- Calculate average confidence per classification per period
- Compute sex ratios (bucks to does)
- Performance target: <5 seconds for full-year aggregation
- Dataset: 35,251 images, ~8,500 detections during rut season

### Alternatives Considered

#### Option A: Raw SQL (PostgreSQL)
**Pros:**
- Fastest query execution (database-optimized aggregations)
- Leverages PostgreSQL GROUP BY, AVG(), COUNT() efficiently
- Database indexes provide O(log N) date filtering
- No data transfer overhead (aggregation in database)

**Cons:**
- SQL queries harder to test and maintain
- Type safety lost (manual result mapping)
- Complex queries get verbose

**Performance:**
- Date range query (6,115 images): **<500ms**
- Monthly aggregation (5 months, 8,500 detections): **<1 second**
- **Total: ~1.5 seconds** (well within 5-second limit)

**Example:**
```sql
SELECT
  DATE_TRUNC('month', i.timestamp) AS period,
  d.classification,
  COUNT(*) AS detection_count,
  AVG(d.confidence) AS avg_confidence
FROM images i
JOIN detections d ON i.id = d.image_id
WHERE i.timestamp BETWEEN '2024-09-01' AND '2025-01-31'
GROUP BY period, d.classification
ORDER BY period, d.classification;
```

#### Option B: Pandas (in Python)
**Pros:**
- Familiar data analysis API (groupby, agg, pivot)
- Easy to test (dataframes are inspectable)
- Flexible transformations

**Cons:**
- Requires loading all data into memory
- 8,500 detections + metadata: ~5-10MB in-memory
- Slower than database aggregation (data transfer + processing)
- Higher memory usage (Python objects > SQL rows)

**Performance:**
- Data load (8,500 rows): **~1-2 seconds**
- Pandas groupby/agg: **~500ms - 1 second**
- **Total: ~2-3 seconds** (within 5-second limit but slower than SQL)

**Example:**
```python
df = pd.DataFrame(detections)
monthly_stats = df.groupby(['month', 'classification']).agg({
    'id': 'count',
    'confidence': 'mean'
}).reset_index()
```

#### Option C: SQLAlchemy ORM
**Pros:**
- Type-safe queries (Python objects, IDE autocomplete)
- Testable with mocked models
- Consistent with existing codebase

**Cons:**
- Slower than raw SQL (ORM overhead)
- Complex aggregations require `func.count()`, `func.avg()` syntax
- Less readable than raw SQL for complex queries

**Performance:**
- Date range query: **~800ms - 1 second** (ORM overhead)
- Aggregation: **~1-2 seconds**
- **Total: ~2-3 seconds** (within limit but slower than raw SQL)

**Example:**
```python
from sqlalchemy import func

results = (
    session.query(
        func.date_trunc('month', Image.timestamp).label('period'),
        Detection.classification,
        func.count(Detection.id).label('count'),
        func.avg(Detection.confidence).label('avg_confidence')
    )
    .join(Detection, Image.id == Detection.image_id)
    .filter(Image.timestamp.between('2024-09-01', '2025-01-31'))
    .group_by('period', Detection.classification)
    .all()
)
```

### Decision: Raw SQL with Type-Safe Wrappers

**Rationale:**
1. **Performance**: Fastest option (~1.5 seconds vs 2-3 seconds)
2. **Scalability**: Database aggregation scales better than in-memory processing
3. **Efficiency**: No data transfer overhead (only aggregated results returned)
4. **Indexing**: Leverages existing database indexes on `timestamp` and `classification`
5. **Maintainability**: Wrap SQL in service layer functions with type hints

**Implementation Plan:**
- Write raw SQL queries in `src/backend/services/seasonal_analysis.py`
- Use SQLAlchemy `text()` for parameterized queries (SQL injection protection)
- Return Pydantic models for type safety (SeasonalReport, ComparisonResult)
- Add unit tests with fixture data
- Document SQL queries with inline comments

**Example Service Function:**
```python
from sqlalchemy import text
from typing import List
from ..schemas.report import SeasonalReport

async def get_seasonal_activity(
    start_date: str,
    end_date: str,
    group_by: str = "month"
) -> SeasonalReport:
    """
    Generate seasonal activity report with detection counts and confidence stats.

    Args:
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
        group_by: 'month', 'week', or 'day'

    Returns:
        SeasonalReport with aggregated statistics
    """
    query = text("""
        SELECT
          DATE_TRUNC(:group_by, i.timestamp) AS period,
          d.classification,
          COUNT(*) AS detection_count,
          AVG(d.confidence) AS avg_confidence
        FROM images i
        JOIN detections d ON i.id = d.image_id
        WHERE i.timestamp BETWEEN :start_date AND :end_date
        GROUP BY period, d.classification
        ORDER BY period, d.classification
    """)

    result = await session.execute(
        query,
        {"start_date": start_date, "end_date": end_date, "group_by": group_by}
    )

    # Map SQL results to Pydantic model
    return SeasonalReport.from_sql_results(result.fetchall())
```

**Type Safety Strategy:**
- Raw SQL in service layer (performance)
- Pydantic schemas for request/response (type safety)
- Comprehensive unit tests (correctness)

---

## Summary of Decisions

| Decision | Chosen Technology | Primary Reason |
|----------|------------------|----------------|
| PDF Generation | ReportLab | Smallest file size (3.5MB vs 5-7MB) |
| Chart Library | Recharts | Existing project usage, React-native API |
| Date Picker | MUI DatePicker | Consistency with Material-UI v5 theme |
| Aggregation | Raw SQL + Pydantic | Fastest performance (1.5s vs 2-3s) |

## Dependencies to Add

**Backend (requirements.txt):**
```
reportlab>=4.0.0        # PDF generation
pillow>=10.0.0          # Image manipulation (already installed)
```

**Frontend (package.json):**
```json
{
  "dependencies": {
    "@mui/x-date-pickers": "^6.18.0",
    "dayjs": "^1.11.10",
    "recharts": "^2.10.0"
  }
}
```

Note: Recharts and MUI X already installed in Sprint 10.

## Next Steps

1. Install ReportLab in backend Docker container
2. Verify existing Recharts and MUI DatePicker versions
3. Create SQL query service layer (`seasonal_analysis.py`)
4. Implement Pydantic response schemas
5. Write unit tests for aggregation logic

---

**Phase 0 Complete**: Technology decisions documented and justified.
**Next Phase**: Phase 1 (Design - data model, contracts, quickstart)
