import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Typography,
  useTheme,
} from '@mui/material';
import { getDeerList, Deer } from '../api/deer';

export default function DeerGallery() {
  const [sexFilter, setSexFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('last_seen');

  const { data, isLoading } = useQuery({
    queryKey: ['deer', 'list', sexFilter, sortBy],
    queryFn: () => getDeerList({
      page_size: 100,
      sex: sexFilter !== 'all' ? sexFilter : undefined,
      sort_by: sortBy,
      min_sightings: 1,
    }),
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  const filteredDeer = data?.deer.filter(deer => deer.sighting_count > 0) || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Deer Gallery
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {filteredDeer.length} deer with sightings
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Sex</InputLabel>
                <Select
                  value={sexFilter}
                  label="Filter by Sex"
                  onChange={(e) => setSexFilter(e.target.value)}
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="buck">Bucks</MenuItem>
                  <MenuItem value="doe">Does</MenuItem>
                  <MenuItem value="fawn">Fawns</MenuItem>
                  <MenuItem value="unknown">Unknown</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Sort By</InputLabel>
                <Select
                  value={sortBy}
                  label="Sort By"
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <MenuItem value="last_seen">Last Seen</MenuItem>
                  <MenuItem value="first_seen">First Seen</MenuItem>
                  <MenuItem value="sighting_count">Sighting Count</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Deer Grid */}
      <Grid container spacing={3}>
        {filteredDeer.map((deer) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={deer.id}>
            <DeerCard deer={deer} />
          </Grid>
        ))}
      </Grid>

      {filteredDeer.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <Typography variant="body1" color="text.secondary">
            No deer found matching your filters
          </Typography>
        </Box>
      )}
    </Box>
  );
}

interface DeerCardProps {
  deer: Deer;
}

function DeerCard({ deer }: DeerCardProps) {
  const navigate = useNavigate();
  const theme = useTheme();

  const sexColors: Record<string, { bg: string; color: string }> = {
    buck: { bg: theme.palette.info.light, color: theme.palette.info.dark },
    doe: { bg: theme.palette.secondary.light, color: theme.palette.secondary.dark },
    fawn: { bg: theme.palette.warning.light, color: theme.palette.warning.dark },
    unknown: { bg: theme.palette.grey[200], color: theme.palette.grey[700] },
  };

  const sexIcons: Record<string, string> = {
    buck: 'B',
    doe: 'D',
    fawn: 'F',
    unknown: '?',
  };

  const color = sexColors[deer.sex] || sexColors.unknown;

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        },
      }}
    >
      <CardActionArea onClick={() => navigate(`/deer/${deer.id}`)} sx={{ flexGrow: 1 }}>
        {deer.thumbnail_url ? (
          <CardMedia
            component="img"
            height="192"
            image={deer.thumbnail_url}
            alt={deer.name || 'Deer'}
            sx={{ height: 192, objectFit: 'cover' }}
          />
        ) : (
          <Box
            sx={{
              height: 192,
              background: `linear-gradient(135deg, ${theme.palette.primary.light} 0%, ${theme.palette.primary.dark} 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography variant="h1" sx={{ fontSize: 72, color: 'white' }}>
              {sexIcons[deer.sex]}
            </Typography>
          </Box>
        )}

        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Typography variant="h6" noWrap sx={{ flexGrow: 1, mr: 1 }}>
              {deer.name || `Deer ${deer.id.slice(0, 8)}`}
            </Typography>
            <Chip
              label={deer.sex}
              size="small"
              sx={{
                bgcolor: color.bg,
                color: color.color,
                fontWeight: 600,
              }}
            />
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Sightings:
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {deer.sighting_count}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Confidence:
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {(deer.confidence * 100).toFixed(1)}%
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Last seen:
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {new Date(deer.last_seen).toLocaleDateString()}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
