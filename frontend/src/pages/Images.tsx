import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardMedia,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import {
  Close as CloseIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  FilterList as FilterIcon,
  Edit as EditIcon,
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
  Sort as SortIcon,
} from '@mui/icons-material';
import apiClient from '../api/client';
import DetectionCorrectionDialog from '../components/DetectionCorrectionDialog';
import BatchCorrectionDialog from '../components/BatchCorrectionDialog';
import PaginationControls from '../components/PaginationControls';

interface Detection {
  id: string;
  classification: string;
  corrected_classification?: string;
  confidence: number;
  is_valid: boolean;
  is_reviewed: boolean;
}

interface Image {
  id: string;
  filename: string;
  timestamp: string;
  location_name: string;
  detection_count?: number;
  detections?: Detection[];
}

interface Location {
  id: string;
  name: string;
}

export default function Images() {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [locationFilter, setLocationFilter] = useState<string>('all');
  const [classificationFilter, setClassificationFilter] = useState<string>('all');
  const [duplicateFilter, setDuplicateFilter] = useState<string>('all'); // all, only, exclude
  const [sortBy, setSortBy] = useState<string>('timestamp_desc'); // timestamp_desc, timestamp_asc, filename_asc, filename_desc
  const [page, setPage] = useState(1);
  const pageSize = 50;
  const [correctionDialogOpen, setCorrectionDialogOpen] = useState(false);
  const [selectedImages, setSelectedImages] = useState<Set<number>>(new Set());
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);

  // Fetch locations for filter
  const { data: locationsData } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      const response = await apiClient.get('/locations');
      return response.data;
    },
  });

  const locations: Location[] = locationsData?.locations || [];

  // Fetch classifications for filter
  const { data: classificationsData } = useQuery({
    queryKey: ['classifications'],
    queryFn: async () => {
      const response = await apiClient.get('/images/classifications');
      return response.data;
    },
  });

  const classifications: string[] = classificationsData?.classifications || [];

  const { data: imagesData, isLoading } = useQuery({
    queryKey: ['images', locationFilter, classificationFilter, duplicateFilter, page],
    queryFn: async () => {
      const params: any = {
        page,
        page_size: pageSize,
      };

      if (locationFilter && locationFilter !== 'all') {
        params.location_id = locationFilter;
      }

      if (classificationFilter && classificationFilter !== 'all') {
        params.classification = classificationFilter;
      }

      if (duplicateFilter === 'only') {
        params.show_duplicates = true;
      } else if (duplicateFilter === 'exclude') {
        params.show_duplicates = false;
      }

      const response = await apiClient.get('/images', { params });
      return response.data;
    },
  });

  let images: Image[] = (imagesData?.images || []).filter((img: Image) => img.is_valid !== false);

  // Apply client-side sorting
  images = [...images].sort((a, b) => {
    switch (sortBy) {
      case 'timestamp_desc':
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      case 'timestamp_asc':
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      case 'filename_asc':
        return a.filename.localeCompare(b.filename);
      case 'filename_desc':
        return b.filename.localeCompare(a.filename);
      case 'confidence_desc': {
        const aConf = a.detections?.[0]?.confidence || 0;
        const bConf = b.detections?.[0]?.confidence || 0;
        return bConf - aConf;
      }
      case 'confidence_asc': {
        const aConf = a.detections?.[0]?.confidence || 0;
        const bConf = b.detections?.[0]?.confidence || 0;
        return aConf - bConf;
      }
      default:
        return 0;
    }
  });

  const totalImages = imagesData?.total || 0;
  const totalPages = Math.ceil(totalImages / pageSize);

  const handleImageClick = (index: number) => {
    setSelectedIndex(index);
  };

  const handleClose = () => {
    setSelectedIndex(null);
  };

  const handlePrevious = () => {
    if (selectedIndex !== null && selectedIndex > 0) {
      setSelectedIndex(selectedIndex - 1);
    }
  };

  const handleNext = () => {
    if (selectedIndex !== null && selectedIndex < images.length - 1) {
      setSelectedIndex(selectedIndex + 1);
    }
  };

  const handleLocationFilterChange = (value: string) => {
    setLocationFilter(value);
    setPage(1); // Reset to first page when filter changes
  };

  const handleClassificationFilterChange = (value: string) => {
    setClassificationFilter(value);
    setPage(1); // Reset to first page when filter changes
  };

  const handleToggleSelect = (index: number) => {
    setSelectedImages(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    setSelectedImages(new Set(images.map((_, i) => i)));
  };

  const handleClearSelection = () => {
    setSelectedImages(new Set());
  };

  if (isLoading && images.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  const selectedImage = selectedIndex !== null ? images[selectedIndex] : null;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Image Browser
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {totalImages} images total
          </Typography>
        </Box>
      </Box>

      {/* Selection Controls */}
      {selectedImages.size > 0 && (
        <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label={`${selectedImages.size} selected`}
            color="primary"
            onDelete={handleClearSelection}
          />
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => setBatchDialogOpen(true)}
          >
            Edit Selected
          </Button>
        </Box>
      )}

      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <Button
          size="small"
          onClick={handleSelectAll}
          disabled={selectedImages.size === images.length}
        >
          Select All
        </Button>
        <Button
          size="small"
          onClick={handleClearSelection}
          disabled={selectedImages.size === 0}
        >
          Clear Selection
        </Button>
      </Box>

      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <FilterIcon color="action" />

        {/* Location Filter */}
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Location</InputLabel>
          <Select
            value={locationFilter}
            onChange={(e) => handleLocationFilterChange(e.target.value)}
            label="Location"
          >
            <MenuItem value="all">All Locations</MenuItem>
            {locations.map(location => (
              <MenuItem key={location.id} value={location.id}>
                {location.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Classification Filter */}
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Classification</InputLabel>
          <Select
            value={classificationFilter}
            onChange={(e) => handleClassificationFilterChange(e.target.value)}
            label="Classification"
          >
            <MenuItem value="all">All Classifications</MenuItem>
            {classifications.map(classification => (
              <MenuItem key={classification} value={classification}>
                {classification.charAt(0).toUpperCase() + classification.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Duplicate Filter */}
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Duplicates</InputLabel>
          <Select
            value={duplicateFilter}
            onChange={(e) => { setDuplicateFilter(e.target.value); setPage(1); }}
            label="Duplicates"
          >
            <MenuItem value="all">All Images</MenuItem>
            <MenuItem value="only">Only Duplicates</MenuItem>
            <MenuItem value="exclude">Exclude Duplicates</MenuItem>
          </Select>
        </FormControl>

        {/* Sort Dropdown */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <SortIcon color="action" />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Sort By</InputLabel>
            <Select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              label="Sort By"
            >
              <MenuItem value="timestamp_desc">Newest First</MenuItem>
              <MenuItem value="timestamp_asc">Oldest First</MenuItem>
              <MenuItem value="confidence_desc">Highest Confidence</MenuItem>
              <MenuItem value="confidence_asc">Lowest Confidence</MenuItem>
              <MenuItem value="filename_asc">Filename (A-Z)</MenuItem>
              <MenuItem value="filename_desc">Filename (Z-A)</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Active Filter Chips */}
      <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {locationFilter !== 'all' && (
          <Chip
            label={`Location: ${locations.find(l => l.id === locationFilter)?.name || locationFilter}`}
            onDelete={() => handleLocationFilterChange('all')}
            color="primary"
          />
        )}
        {classificationFilter !== 'all' && (
          <Chip
            label={`Class: ${classificationFilter}`}
            onDelete={() => handleClassificationFilterChange('all')}
            color="primary"
          />
        )}
        {duplicateFilter !== 'all' && (
          <Chip
            label={duplicateFilter === 'only' ? 'Showing: Only Duplicates' : 'Showing: No Duplicates'}
            onDelete={() => setDuplicateFilter('all')}
            color="secondary"
          />
        )}
      </Box>

      {/* Image Grid */}
      {images.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No images found with selected filters
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {images.map((image, index) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={image.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'transform 0.2s',
                  '&:hover': { transform: 'scale(1.05)' },
                  position: 'relative',
                }}
                onClick={() => handleImageClick(index)}
              >
                <Checkbox
                  checked={selectedImages.has(index)}
                  onChange={() => handleToggleSelect(index)}
                  onClick={(e) => e.stopPropagation()}
                  sx={{
                    position: 'absolute',
                    top: 4,
                    left: 4,
                    bgcolor: 'white',
                    borderRadius: '50%',
                    '&:hover': { bgcolor: 'white' },
                    zIndex: 1,
                  }}
                />
                <CardMedia
                  component="img"
                  height="200"
                  image={`/api/static/images/${image.id}`}
                  alt={image.filename}
                  sx={{ objectFit: 'cover' }}
                />
                <Box sx={{ p: 1 }}>
                  <Typography variant="caption" display="block" noWrap>
                    {image.filename}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {image.location_name}
                  </Typography>
                  {image.detections && image.detections.length > 0 && (
                    <Chip
                      label={image.detections[0].corrected_classification || image.detections[0].classification}
                      size="small"
                      color={image.detections[0].is_reviewed ? 'success' : 'default'}
                      sx={{ mt: 0.5 }}
                    />
                  )}
                  {image.detections && image.detections.length > 1 && (
                    <Chip
                      label={`+${image.detections.length - 1} more`}
                      size="small"
                      variant="outlined"
                      sx={{ mt: 0.5, ml: 0.5 }}
                    />
                  )}
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Pagination */}
      <PaginationControls
        currentPage={page}
        totalPages={totalPages}
        onPageChange={setPage}
      />

      {/* Lightbox Dialog */}
      {selectedImage && (
        <Dialog open={selectedIndex !== null} onClose={handleClose} maxWidth="lg" fullWidth>
          <Box sx={{ position: 'relative', bgcolor: 'black' }}>
            {/* Close Button */}
            <IconButton
              onClick={handleClose}
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                color: 'white',
                bgcolor: 'rgba(0, 0, 0, 0.5)',
                '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                zIndex: 1,
              }}
            >
              <CloseIcon />
            </IconButton>

            {/* Edit Button */}
            <IconButton
              onClick={(e) => {
                e.stopPropagation();
                setCorrectionDialogOpen(true);
              }}
              sx={{
                position: 'absolute',
                top: 8,
                right: 56,
                color: 'white',
                bgcolor: 'rgba(0, 0, 0, 0.5)',
                '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                zIndex: 1,
              }}
            >
              <EditIcon />
            </IconButton>

            {selectedIndex !== null && selectedIndex > 0 && (
              <IconButton
                onClick={handlePrevious}
                sx={{
                  position: 'absolute',
                  left: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'white',
                  bgcolor: 'rgba(0, 0, 0, 0.5)',
                  '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                  zIndex: 1,
                }}
              >
                <PrevIcon />
              </IconButton>
            )}

            {selectedIndex !== null && selectedIndex < images.length - 1 && (
              <IconButton
                onClick={handleNext}
                sx={{
                  position: 'absolute',
                  right: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'white',
                  bgcolor: 'rgba(0, 0, 0, 0.5)',
                  '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
                  zIndex: 1,
                }}
              >
                <NextIcon />
              </IconButton>
            )}

            <Box sx={{ p: 2 }}>
              <img
                src={`/api/static/images/${selectedImage.id}`}
                alt={selectedImage.filename}
                style={{
                  width: '100%',
                  height: 'auto',
                  maxHeight: '80vh',
                  objectFit: 'contain',
                }}
              />
              <Box sx={{ mt: 2, color: 'white' }}>
                <Typography variant="h6">{selectedImage.filename}</Typography>
                <Typography variant="body2" color="grey.400">
                  Location: {selectedImage.location_name}
                </Typography>
                <Typography variant="body2" color="grey.400">
                  Timestamp: {new Date(selectedImage.timestamp).toLocaleString()}
                </Typography>
                {selectedImage.detections && selectedImage.detections.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    {selectedImage.detections.map((det, idx) => (
                      <Box key={det.id} sx={{ mb: 1 }}>
                        <Chip
                          label={det.corrected_classification || det.classification}
                          color={det.is_reviewed ? 'success' : 'default'}
                          sx={{ mr: 1 }}
                        />
                        <Chip
                          label={`Confidence: ${(det.confidence * 100).toFixed(1)}%`}
                          variant="outlined"
                          sx={{ color: 'white', borderColor: 'white' }}
                        />
                      </Box>
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
          </Box>
        </Dialog>
      )}

      {/* Detection Correction Dialog */}
      {selectedImage && correctionDialogOpen && selectedImage.detections && selectedImage.detections.length > 0 && (
        <DetectionCorrectionDialog
          open={correctionDialogOpen}
          onClose={() => setCorrectionDialogOpen(false)}
          detection={{
            detection_id: selectedImage.detections[0].id,
            classification: selectedImage.detections[0].classification,
            is_valid: selectedImage.detections[0].is_valid,
            corrected_classification: selectedImage.detections[0].corrected_classification,
            correction_notes: undefined,
            confidence: selectedImage.detections[0].confidence,
          }}
          imageName={selectedImage.filename}
          deerName="Unknown"
        />
      )}

      {/* Batch Correction Dialog */}
      {batchDialogOpen && (
        <BatchCorrectionDialog
          open={batchDialogOpen}
          onClose={() => {
            setBatchDialogOpen(false);
            setSelectedImages(new Set());
          }}
          detectionIds={Array.from(selectedImages)
            .flatMap(i => images[i]?.detections?.map(d => d.id) || [])
            .filter((id): id is string => !!id)}
          deerName="Multiple Images"
        />
      )}
    </Box>
  );
}
