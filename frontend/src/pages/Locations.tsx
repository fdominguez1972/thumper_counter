import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  LocationOn as LocationOnIcon,
  PhotoLibrary as PhotoLibraryIcon,
  TrendingUp as TrendingUpIcon,
  Map as MapIcon,
} from '@mui/icons-material';
import apiClient from '../api/client';

interface Location {
  id: string;
  name: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  image_count: number;
  created_at: string;
}

interface LocationStats {
  location_id: string;
  location_name: string;
  total_images: number;
  total_detections: number;
  unique_deer: number;
  last_activity: string;
}

export default function Locations() {
  // Fetch locations
  const { data: locationsData, isLoading: locationsLoading } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      const response = await apiClient.get('/locations');
      return response.data;
    },
  });

  // Fetch location stats
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['location-stats'],
    queryFn: async () => {
      // Fetch all images and count by location
      const response = await apiClient.get('/images', {
        params: { page_size: 10000 },
      });
      const images = response.data.images || [];

      const locationStatsMap = new Map<string, LocationStats>();

      images.forEach((img: any) => {
        const locationId = img.location_id || 'unknown';
        const locationName = img.location_name || 'Unknown';

        if (!locationStatsMap.has(locationId)) {
          locationStatsMap.set(locationId, {
            location_id: locationId,
            location_name: locationName,
            total_images: 0,
            total_detections: 0,
            unique_deer: 0,
            last_activity: img.timestamp,
          });
        }

        const stats = locationStatsMap.get(locationId)!;
        stats.total_images += 1;
        if (img.detection_id) {
          stats.total_detections += 1;
        }
        if (new Date(img.timestamp) > new Date(stats.last_activity)) {
          stats.last_activity = img.timestamp;
        }
      });

      return Array.from(locationStatsMap.values());
    },
  });

  const locations: Location[] = locationsData?.locations || [];
  const locationStats: LocationStats[] = statsData || [];

  if (locationsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Calculate center coordinates for map view
  const validCoords = locations.filter(l => l.latitude && l.longitude);
  const centerLat = validCoords.length > 0
    ? validCoords.reduce((sum, l) => sum + (l.latitude || 0), 0) / validCoords.length
    : 0;
  const centerLng = validCoords.length > 0
    ? validCoords.reduce((sum, l) => sum + (l.longitude || 0), 0) / validCoords.length
    : 0;

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 3 }}>
        Camera Locations
      </Typography>

      {/* Map Visualization Placeholder */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <MapIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Location Map</Typography>
          </Box>

          {/* Placeholder for future map integration */}
          <Box
            sx={{
              height: 400,
              bgcolor: 'grey.100',
              borderRadius: 2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px dashed',
              borderColor: 'divider',
            }}
          >
            <LocationOnIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Map Visualization
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Interactive map showing camera locations and activity heat maps
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Map center: {centerLat.toFixed(6)}, {centerLng.toFixed(6)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              ({validCoords.length} locations with GPS coordinates)
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Location Cards */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Camera Sites
      </Typography>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {locations.map(location => {
          const stats = locationStats.find(s => s.location_name === location.name);

          return (
            <Grid item xs={12} md={6} lg={4} key={location.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <LocationOnIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">{location.name}</Typography>
                  </Box>

                  {location.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {location.description}
                    </Typography>
                  )}

                  {location.latitude && location.longitude && (
                    <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 2 }}>
                      Coordinates: {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
                    <Chip
                      icon={<PhotoLibraryIcon />}
                      label={`${stats?.total_images || 0} images`}
                      size="small"
                      variant="outlined"
                    />
                    {stats && stats.total_detections > 0 && (
                      <Chip
                        label={`${stats.total_detections} detections`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    )}
                  </Box>

                  {stats && stats.last_activity && (
                    <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
                      Last activity: {new Date(stats.last_activity).toLocaleString()}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Activity Statistics */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <TrendingUpIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Location Activity</Typography>
          </Box>

          {statsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Location</TableCell>
                    <TableCell align="right">Images</TableCell>
                    <TableCell align="right">Detections</TableCell>
                    <TableCell align="right">Detection Rate</TableCell>
                    <TableCell>Last Activity</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {locationStats.map(stat => (
                    <TableRow key={stat.location_id}>
                      <TableCell component="th" scope="row">
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <LocationOnIcon sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
                          {stat.location_name}
                        </Box>
                      </TableCell>
                      <TableCell align="right">{stat.total_images}</TableCell>
                      <TableCell align="right">{stat.total_detections}</TableCell>
                      <TableCell align="right">
                        {stat.total_images > 0
                          ? `${((stat.total_detections / stat.total_images) * 100).toFixed(1)}%`
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {new Date(stat.last_activity).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          <Box sx={{ mt: 3, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary">
              <strong>Future Enhancements:</strong> This page will include:
            </Typography>
            <Typography variant="body2" color="text.secondary" component="ul" sx={{ mt: 1, pl: 2 }}>
              <li>Interactive map with clickable camera locations</li>
              <li>Heat maps showing temporal usage patterns (hourly/daily/seasonal)</li>
              <li>Deer migration paths between camera sites</li>
              <li>Time-slider to see activity changes over time</li>
              <li>Population density visualizations</li>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
