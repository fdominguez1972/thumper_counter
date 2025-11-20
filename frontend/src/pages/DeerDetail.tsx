import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Typography,
  useTheme,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDeer, getDeerTimeline, getDeerLocations } from '../api/deer';

export default function DeerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const theme = useTheme();

  const { data: deer, isLoading: deerLoading } = useQuery({
    queryKey: ['deer', id],
    queryFn: () => getDeer(id!),
    enabled: !!id,
  });

  const { data: timeline } = useQuery({
    queryKey: ['deer', id, 'timeline'],
    queryFn: () => getDeerTimeline(id!, 'day'),
    enabled: !!id,
  });

  const { data: locations } = useQuery({
    queryKey: ['deer', id, 'locations'],
    queryFn: () => getDeerLocations(id!),
    enabled: !!id,
  });

  if (deerLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!deer) {
    return (
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Deer not found
        </Typography>
        <Button
          variant="text"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/deer')}
          sx={{ mt: 2 }}
        >
          Back to gallery
        </Button>
      </Box>
    );
  }

  const sexColors: Record<string, { bg: string; color: string }> = {
    buck: { bg: theme.palette.info.light, color: theme.palette.info.dark },
    doe: { bg: theme.palette.secondary.light, color: theme.palette.secondary.dark },
    fawn: { bg: theme.palette.warning.light, color: theme.palette.warning.dark },
    unknown: { bg: theme.palette.grey[200], color: theme.palette.grey[700] },
  };

  const color = sexColors[deer.sex] || sexColors.unknown;

  return (
    <Box>
      {/* Back Button */}
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/deer')}
        sx={{ mb: 2 }}
      >
        Back to gallery
      </Button>

      {/* Hero Image */}
      <Card sx={{ mb: 3, overflow: 'hidden' }}>
        {deer.photo_url ? (
          <Box
            component="img"
            src={deer.photo_url}
            alt={deer.name || 'Deer'}
            sx={{
              width: '100%',
              maxHeight: { xs: 300, sm: 400, md: 500 },
              objectFit: 'cover',
              display: 'block',
            }}
          />
        ) : (
          <Box
            sx={{
              width: '100%',
              height: { xs: 300, sm: 400, md: 500 },
              background: `linear-gradient(135deg, ${theme.palette.primary.light} 0%, ${theme.palette.primary.dark} 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography variant="h1" sx={{ fontSize: { xs: 80, sm: 120, md: 160 }, color: 'white', opacity: 0.5 }}>
              {deer.sex === 'buck' ? 'B' : deer.sex === 'doe' ? 'D' : deer.sex === 'fawn' ? 'F' : '?'}
            </Typography>
          </Box>
        )}
      </Card>

      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 600, mb: 1 }}>
            {deer.name || `Deer ${deer.id.slice(0, 8)}`}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              label={deer.sex}
              sx={{
                bgcolor: color.bg,
                color: color.color,
                fontWeight: 600,
              }}
            />
            <Typography variant="body2" color="text.secondary">
              ID: {deer.id.slice(0, 16)}...
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={6} md={3}>
          <StatCard
            label="Total Sightings"
            value={deer.sighting_count}
            onClick={() => navigate(`/deer/${id}/images`)}
            clickable
          />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard
            label="Average Confidence"
            value={`${(deer.confidence * 100).toFixed(1)}%`}
          />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard
            label="First Seen"
            value={new Date(deer.first_seen).toLocaleDateString()}
          />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard
            label="Last Seen"
            value={new Date(deer.last_seen).toLocaleDateString()}
          />
        </Grid>
      </Grid>

      {/* Timeline Chart */}
      {timeline && timeline.timeline.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Activity Timeline
            </Typography>
            <Box sx={{ height: 300, mt: 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeline.timeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="period"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => new Date(value as string).toLocaleDateString()}
                    formatter={(value: number) => [value, 'Sightings']}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke={theme.palette.primary.main}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Locations */}
      {locations && locations.locations.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Location Patterns
            </Typography>
            <Box sx={{ mt: 2 }}>
              {locations.locations.map((location, index) => (
                <Box key={location.location_id}>
                  {index > 0 && <Divider sx={{ my: 2 }} />}
                  <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {location.location_name}
                      </Typography>
                      <Chip
                        label={`${location.sighting_count} sightings`}
                        color="primary"
                        size="small"
                      />
                    </Box>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          First seen
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {new Date(location.first_seen).toLocaleDateString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Last seen
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {new Date(location.last_seen).toLocaleDateString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary">
                          Avg confidence
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {(location.avg_confidence * 100).toFixed(1)}%
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  onClick?: () => void;
  clickable?: boolean;
}

function StatCard({ label, value, onClick, clickable }: StatCardProps) {
  return (
    <Card
      sx={{
        cursor: clickable ? 'pointer' : 'default',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': clickable ? {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        } : {},
      }}
      onClick={onClick}
    >
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {label}
        </Typography>
        <Typography variant="h4" fontWeight={600}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}
