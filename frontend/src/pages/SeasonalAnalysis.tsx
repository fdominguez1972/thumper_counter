/**
 * Seasonal Analysis Page
 * Feature: 008-rut-season-analysis
 *
 * Provides interface for analyzing wildlife activity patterns during specific seasons,
 * with focus on Texas whitetail deer rut season (September 1 - January 31).
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Chip,
  Stack,
} from '@mui/material';
import {
  Download as DownloadIcon,
  FilterList as FilterIcon,
  PictureAsPdf as PdfIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import {
  getSeasonalActivityReport,
  generatePDFReport,
  checkPDFStatus,
  SeasonalFilter,
} from '../api/seasonal';

export const SeasonalAnalysis: React.FC = () => {
  // State for filters
  const [season, setSeason] = useState<SeasonalFilter>('RUT_SEASON');
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [groupBy, setGroupBy] = useState<'day' | 'week' | 'month'>('month');
  const [compareToNonSeason, setCompareToNonSeason] = useState(false);

  // State for PDF export
  const [pdfJobId, setPdfJobId] = useState<string | null>(null);
  const [pdfGenerating, setPdfGenerating] = useState(false);

  // Fetch seasonal activity report
  const { data: report, isLoading, error, refetch } = useQuery({
    queryKey: ['seasonal-activity', season, year, groupBy, compareToNonSeason],
    queryFn: () => getSeasonalActivityReport({
      season,
      year,
      group_by: groupBy,
      compare_to_non_season: compareToNonSeason,
    }),
    enabled: true,
  });

  // Poll PDF status
  const { data: pdfStatus } = useQuery({
    queryKey: ['pdf-status', pdfJobId],
    queryFn: () => checkPDFStatus(pdfJobId!),
    enabled: !!pdfJobId,
    refetchInterval: (data) => {
      if ((data as any)?.status === 'completed' || (data as any)?.status === 'failed') {
        setPdfGenerating(false);
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });

  // Handle PDF generation
  const handleGeneratePDF = async () => {
    try {
      setPdfGenerating(true);
      const startDate = season === 'RUT_SEASON' && year
        ? `${year}-09-01`
        : `${year}-01-01`;
      const endDate = season === 'RUT_SEASON' && year
        ? `${year + 1}-01-31`
        : `${year}-12-31`;

      const response = await generatePDFReport({
        report_type: 'seasonal_activity',
        start_date: startDate,
        end_date: endDate,
        title: `${season.replace('_', ' ')} Activity Report ${year}`,
        group_by: groupBy,
        include_charts: true,
        include_tables: true,
        include_insights: true,
      });

      setPdfJobId(response.job_id);
    } catch (err) {
      console.error('PDF generation error:', err);
      setPdfGenerating(false);
    }
  };

  // Handle PDF download
  const handleDownloadPDF = () => {
    if (pdfStatus?.download_url) {
      const url = `http://localhost:8001${pdfStatus.download_url}`;
      window.open(url, '_blank');
    }
  };

  // Generate year options (current year and 5 years back)
  const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
          Seasonal Analysis
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Analyze wildlife activity patterns during specific seasons. Focus on Texas whitetail deer rut season.
        </Typography>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterIcon sx={{ mr: 1, color: 'text.secondary' }} />
          <Typography variant="h6">Filters</Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Season</InputLabel>
              <Select
                value={season}
                label="Season"
                onChange={(e) => setSeason(e.target.value as SeasonalFilter)}
              >
                <MenuItem value="RUT_SEASON">Rut Season (Sept-Jan)</MenuItem>
                <MenuItem value="SPRING">Spring (Mar-May)</MenuItem>
                <MenuItem value="SUMMER">Summer (Jun-Aug)</MenuItem>
                <MenuItem value="FALL">Fall (Sept-Nov)</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Year</InputLabel>
              <Select
                value={year}
                label="Year"
                onChange={(e) => setYear(Number(e.target.value))}
              >
                {yearOptions.map((y) => (
                  <MenuItem key={y} value={y}>{y}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Group By</InputLabel>
              <Select
                value={groupBy}
                label="Group By"
                onChange={(e) => setGroupBy(e.target.value as 'day' | 'week' | 'month')}
              >
                <MenuItem value="day">Day</MenuItem>
                <MenuItem value="week">Week</MenuItem>
                <MenuItem value="month">Month</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={3}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ height: '56px' }}
              onClick={() => setCompareToNonSeason(!compareToNonSeason)}
            >
              {compareToNonSeason ? 'Hide' : 'Show'} Comparison
            </Button>
          </Grid>

          <Grid item xs={12} md={2}>
            <Button
              variant="contained"
              fullWidth
              sx={{ height: '56px' }}
              onClick={() => refetch()}
              disabled={isLoading}
            >
              Apply Filters
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load seasonal data. Please try again.
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Report Data */}
      {report && !isLoading && (
        <>
          {/* Summary Statistics */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Detections
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {report.summary?.total_detections || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {report.summary?.unique_deer || 0} unique deer
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Buck Detections
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                    {report.summary?.buck_count || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {report.summary?.buck_percentage?.toFixed(1) || 0}% of total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Doe Detections
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                    {report.summary?.doe_count || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {report.summary?.doe_percentage?.toFixed(1) || 0}% of total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Sex Ratio
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {report.summary?.sex_ratio?.toFixed(2) || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Bucks per doe
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Classification Breakdown */}
          {report.summary?.classification_breakdown && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Classification Breakdown
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1 }}>
                {Object.entries(report.summary.classification_breakdown).map(([classification, count]) => (
                  <Chip
                    key={classification}
                    label={`${classification}: ${count}`}
                    variant="outlined"
                  />
                ))}
              </Stack>
            </Paper>
          )}

          {/* Comparison Data */}
          {compareToNonSeason && report.comparison && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Seasonal Comparison
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Season Period
                  </Typography>
                  <Typography variant="h6">
                    {report.comparison.season?.total_detections || 0} detections
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Non-Season Period
                  </Typography>
                  <Typography variant="h6">
                    {report.comparison.non_season?.total_detections || 0} detections
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          )}

          {/* Export Actions */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Export Report
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                startIcon={pdfGenerating ? <CircularProgress size={20} /> : <PdfIcon />}
                onClick={handleGeneratePDF}
                disabled={pdfGenerating}
              >
                {pdfGenerating ? 'Generating PDF...' : 'Generate PDF Report'}
              </Button>

              {pdfStatus?.status === 'completed' && (
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadPDF}
                >
                  Download PDF
                </Button>
              )}
            </Stack>

            {pdfStatus?.status === 'failed' && (
              <Alert severity="error" sx={{ mt: 2 }}>
                PDF generation failed. Please try again.
              </Alert>
            )}
          </Paper>
        </>
      )}
    </Container>
  );
};

export default SeasonalAnalysis;
