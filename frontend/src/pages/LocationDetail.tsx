import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Container,
  Typography,
  Box,
  Paper,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Chip,
  Button,
  Stack,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

interface DeerAtLocation {
  deer_id: string;
  deer_name: string;
  sex: string;
  sighting_count: number;
  first_seen: string;
  last_seen: string;
  avg_confidence: number;
}

interface LocationData {
  id: string;
  name: string;
  description: string | null;
  coordinates: { lat: number; lon: number } | null;
  image_count: number;
}

type SortField = 'deer_name' | 'sex' | 'sighting_count' | 'last_seen';
type SortDirection = 'asc' | 'desc';

export const LocationDetail: React.FC = () => {
  const { locationId } = useParams<{ locationId: string }>();
  const navigate = useNavigate();

  const [sortField, setSortField] = useState<SortField>('sighting_count');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Fetch location info
  const { data: location, isLoading: loadingLocation } = useQuery<LocationData>({
    queryKey: ['location', locationId],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/locations/${locationId}`);
      return response.data;
    },
  });

  // Fetch deer at this location
  const { data: deer, isLoading: loadingDeer, error } = useQuery<DeerAtLocation[]>({
    queryKey: ['location-deer', locationId],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/locations/${locationId}/deer`);
      return response.data;
    },
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedDeer = React.useMemo(() => {
    if (!deer) return [];

    return [...deer].sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'last_seen' || sortField === 'first_seen') {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [deer, sortField, sortDirection]);

  const getSexColor = (sex: string) => {
    switch (sex.toLowerCase()) {
      case 'buck': return 'primary';
      case 'doe': return 'secondary';
      case 'fawn': return 'success';
      default: return 'default';
    }
  };

  if (loadingLocation || loadingDeer) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">Failed to load location data</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Box>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/locations')}
            sx={{ mb: 2 }}
          >
            Back to Locations
          </Button>

          <Typography variant="h4" gutterBottom>
            {location?.name}
          </Typography>

          {location?.description && (
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {location.description}
            </Typography>
          )}

          <Box sx={{ mt: 1 }}>
            <Chip label={`${deer?.length || 0} Unique Deer`} sx={{ mr: 1 }} />
            <Chip label={`${location?.image_count || 0} Images`} />
          </Box>
        </Box>

        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          <TableContainer>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <TableSortLabel
                      active={sortField === 'deer_name'}
                      direction={sortField === 'deer_name' ? sortDirection : 'asc'}
                      onClick={() => handleSort('deer_name')}
                    >
                      Deer ID
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortField === 'sex'}
                      direction={sortField === 'sex' ? sortDirection : 'asc'}
                      onClick={() => handleSort('sex')}
                    >
                      Sex
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="right">
                    <TableSortLabel
                      active={sortField === 'sighting_count'}
                      direction={sortField === 'sighting_count' ? sortDirection : 'asc'}
                      onClick={() => handleSort('sighting_count')}
                    >
                      Sightings
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>First Seen</TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortField === 'last_seen'}
                      direction={sortField === 'last_seen' ? sortDirection : 'asc'}
                      onClick={() => handleSort('last_seen')}
                    >
                      Last Seen
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="right">Avg Confidence</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedDeer.map((deerData) => (
                  <TableRow
                    key={deerData.deer_id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/deer/${deerData.deer_id}`)}
                  >
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {deerData.deer_name || deerData.deer_id.slice(0, 8)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={deerData.sex}
                        color={getSexColor(deerData.sex)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <strong>{deerData.sighting_count}</strong>
                    </TableCell>
                    <TableCell>
                      {new Date(deerData.first_seen).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {new Date(deerData.last_seen).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      {(deerData.avg_confidence * 100).toFixed(1)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {deer && deer.length === 0 && (
          <Alert severity="info">
            No deer have been sighted at this location yet.
          </Alert>
        )}
      </Stack>
    </Container>
  );
};
