import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardMedia,
  CircularProgress,
  Dialog,
  Grid,
  Typography,
  IconButton,
  Chip,
  Checkbox,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Close as CloseIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  Edit as EditIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import { getDeer } from '../api/deer';
import apiClient from '../api/client';
import DetectionCorrectionDialog from '../components/DetectionCorrectionDialog';
import BatchCorrectionDialog from '../components/BatchCorrectionDialog';

interface Detection {
  id: string;
  image_id: string;
  confidence: number;
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  created_at: string;
}

interface Image {
  id: string;
  filename: string;
  timestamp: string;
  location_name: string;
  detection_id: string;
  confidence: number;
  classification: string;
  is_reviewed: boolean;
  is_valid: boolean;
  corrected_classification?: string;
  correction_notes?: string;
}

export default function DeerImages() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [correctionDialogOpen, setCorrectionDialogOpen] = useState(false);
  const [selectedImages, setSelectedImages] = useState<Set<number>>(new Set());
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);

  // Get deer info
  const { data: deer, isLoading: deerLoading } = useQuery({
    queryKey: ['deer', id],
    queryFn: () => getDeer(id!),
    enabled: !!id,
  });

  // Get all images for this deer
  const { data: imagesData, isLoading: imagesLoading } = useQuery({
    queryKey: ['deer', id, 'images'],
    queryFn: async () => {
      const response = await apiClient.get(`/deer/${id}/images`);
      return response.data;
    },
    enabled: !!id,
  });

  const images: Image[] = imagesData?.images || [];

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

  if (deerLoading || imagesLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!deer) {
    return (
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <Typography variant="body1" color="text.secondary">
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

  const selectedImage = selectedIndex !== null ? images[selectedIndex] : null;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/deer/${id}`)}
          sx={{ mb: 2 }}
        >
          Back to {deer.name || 'Deer Profile'}
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          {deer.name || 'Unnamed Deer'} - All Sightings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {images.length} images found
        </Typography>
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

      {/* Image Grid */}
      <Grid container spacing={2}>
        {images.map((image, index) => (
          <Grid item xs={6} sm={4} md={3} lg={2} key={image.id}>
            <Card
              sx={{
                cursor: 'pointer',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'scale(1.05)',
                },
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
                image={`/api/static/images/${image.id}`}
                alt={`Sighting ${index + 1}`}
                sx={{
                  height: 200,
                  objectFit: 'cover',
                }}
              />
              <Box sx={{ p: 1 }}>
                <Typography variant="caption" display="block" noWrap>
                  {new Date(image.timestamp).toLocaleDateString()}
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" noWrap>
                  {image.location_name}
                </Typography>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Lightbox Dialog */}
      {selectedImage && (
        <Dialog
          open={selectedIndex !== null}
          onClose={handleClose}
          maxWidth="lg"
          fullWidth
        >
          <Box sx={{ position: 'relative', bgcolor: 'black' }}>
            {/* Close Button */}
            <IconButton
              onClick={handleClose}
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                color: 'white',
                bgcolor: 'rgba(0,0,0,0.5)',
                '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' },
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
                bgcolor: 'rgba(0,0,0,0.5)',
                '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' },
                zIndex: 1,
              }}
            >
              <EditIcon />
            </IconButton>

            {/* Previous Button */}
            {selectedIndex > 0 && (
              <IconButton
                onClick={handlePrevious}
                sx={{
                  position: 'absolute',
                  left: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'white',
                  bgcolor: 'rgba(0,0,0,0.5)',
                  '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' },
                  zIndex: 1,
                }}
              >
                <PrevIcon />
              </IconButton>
            )}

            {/* Next Button */}
            {selectedIndex < images.length - 1 && (
              <IconButton
                onClick={handleNext}
                sx={{
                  position: 'absolute',
                  right: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'white',
                  bgcolor: 'rgba(0,0,0,0.5)',
                  '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' },
                  zIndex: 1,
                }}
              >
                <NextIcon />
              </IconButton>
            )}

            {/* Image */}
            <Box
              component="img"
              src={`/api/static/images/${selectedImage.id}`}
              alt={`Sighting ${selectedIndex + 1}`}
              sx={{
                width: '100%',
                maxHeight: '80vh',
                objectFit: 'contain',
                display: 'block',
              }}
            />

            {/* Image Info */}
            <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Date
                  </Typography>
                  <Typography variant="body1">
                    {new Date(selectedImage.timestamp).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Location
                  </Typography>
                  <Typography variant="body1">
                    {selectedImage.location_name}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Image {selectedIndex + 1} of {images.length}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </Dialog>
      )}

      {/* Detection Correction Dialog */}
      {selectedImage && correctionDialogOpen && (
        <DetectionCorrectionDialog
          open={correctionDialogOpen}
          onClose={() => setCorrectionDialogOpen(false)}
          detection={{
            detection_id: selectedImage.detection_id,
            classification: selectedImage.classification,
            is_valid: selectedImage.is_valid,
            corrected_classification: selectedImage.corrected_classification,
            correction_notes: selectedImage.correction_notes,
            confidence: selectedImage.confidence,
          }}
          imageName={selectedImage.filename}
          deerName={deer?.name || 'Unknown'}
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
          detectionIds={Array.from(selectedImages).map(i => images[i].detection_id)}
          deerName={deer?.name || 'Unknown'}
        />
      )}
    </Box>
  );
}
