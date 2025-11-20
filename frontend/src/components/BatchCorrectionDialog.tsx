import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  FormControlLabel,
  FormLabel,
  RadioGroup,
  Radio,
  TextField,
  Checkbox,
  Box,
  Alert,
  Typography,
  Grid,
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';

interface BatchCorrectionDialogProps {
  open: boolean;
  onClose: () => void;
  detectionIds: string[];
  deerName: string;
}

export default function BatchCorrectionDialog({
  open,
  onClose,
  detectionIds,
  deerName,
}: BatchCorrectionDialogProps) {
  const queryClient = useQueryClient();

  const [isValid, setIsValid] = useState(true);
  const [correctedClassification, setCorrectedClassification] = useState('');
  const [customTag, setCustomTag] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  const batchMutation = useMutation({
    mutationFn: async (data: {
      detection_ids: string[];
      is_valid?: boolean;
      corrected_classification?: string;
      correction_notes?: string;
      reviewed_by: string;
    }) => {
      const response = await apiClient.patch('/detections/batch/correct', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['deer'] });
      queryClient.invalidateQueries({ queryKey: ['images'] });
      onClose();
      // Show success message
      alert(`Successfully corrected ${data.total_corrected} of ${data.total_requested} detections`);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to save batch correction');
    },
  });

  const handleSubmit = () => {
    setError(null);

    // Get final classification (use custom tag if selected)
    const finalClassification = correctedClassification === 'custom' ? customTag.trim().toLowerCase() : correctedClassification;

    // Validate custom tag
    if (correctedClassification === 'custom' && !customTag.trim()) {
      setError('Please enter a custom tag (e.g., human, vehicle, etc.)');
      return;
    }

    if (!finalClassification && isValid && !notes) {
      setError('Please make at least one change (mark as invalid, correct classification, or add notes)');
      return;
    }

    batchMutation.mutate({
      detection_ids: detectionIds,
      is_valid: isValid,
      corrected_classification: finalClassification || undefined,
      correction_notes: notes || undefined,
      reviewed_by: 'user', // TODO: Get actual username
    });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Batch Review {detectionIds.length} Detections</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {/* Summary */}
          <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Deer
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {deerName}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Selected Images
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {detectionIds.length}
                </Typography>
              </Grid>
            </Grid>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            Changes will be applied to all {detectionIds.length} selected images
          </Alert>

          {/* Valid/Invalid Toggle */}
          <FormControlLabel
            control={
              <Checkbox
                checked={!isValid}
                onChange={(e) => setIsValid(!e.target.checked)}
                color="error"
              />
            }
            label="Mark all as invalid/unusable"
            sx={{ mb: 2 }}
          />

          <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 3, ml: 4 }}>
            Check this if all selected are unusable (rear-end views, wrong species, poor quality)
          </Typography>

          {/* Classification Correction */}
          <FormControl component="fieldset" sx={{ mb: 3 }} fullWidth>
            <FormLabel component="legend">Apply Classification to All</FormLabel>
            <RadioGroup
              value={correctedClassification}
              onChange={(e) => setCorrectedClassification(e.target.value)}
            >
              <FormControlLabel value="" control={<Radio />} label="No change" />
              <FormControlLabel value="buck" control={<Radio />} label="Buck (Male)" />
              <FormControlLabel value="doe" control={<Radio />} label="Doe (Female)" />
              <FormControlLabel value="fawn" control={<Radio />} label="Fawn (Young)" />
              <FormControlLabel value="unknown" control={<Radio />} label="Unknown" />
              <FormControlLabel value="cattle" control={<Radio />} label="Cattle (Not Deer)" />
              <FormControlLabel value="pig" control={<Radio />} label="Pig / Feral Hog (Not Deer)" />
              <FormControlLabel value="raccoon" control={<Radio />} label="Raccoon (Not Deer)" />
              <FormControlLabel value="human" control={<Radio />} label="Human (Not Wildlife)" />
              <FormControlLabel value="vehicle" control={<Radio />} label="Vehicle (Not Wildlife)" />
              <FormControlLabel value="no animals" control={<Radio />} label="No Animals Detected" />
              <FormControlLabel value="custom" control={<Radio />} label="Other (Custom Tag)" />
            </RadioGroup>

            {/* Custom Tag Input */}
            {correctedClassification === 'custom' && (
              <TextField
                label="Enter custom tag"
                value={customTag}
                onChange={(e) => setCustomTag(e.target.value)}
                fullWidth
                sx={{ mt: 2, ml: 4 }}
                placeholder="e.g., human, vehicle, bird, etc."
                helperText="Common tags: human, vehicle, bird, coyote, bobcat, etc."
              />
            )}
          </FormControl>

          {/* Notes */}
          <TextField
            label="Notes (optional)"
            multiline
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            fullWidth
            placeholder="Explain the correction (applied to all selected)..."
            helperText={`${notes.length}/500 characters`}
            inputProps={{ maxLength: 500 }}
          />

          {/* Error Message */}
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={batchMutation.isPending}
          color="primary"
        >
          {batchMutation.isPending ? 'Saving...' : `Review ${detectionIds.length} Detections`}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
