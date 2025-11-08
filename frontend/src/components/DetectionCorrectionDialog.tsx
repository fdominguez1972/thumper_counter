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
  Chip,
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';

interface DetectionCorrectionDialogProps {
  open: boolean;
  onClose: () => void;
  detection: {
    detection_id: string;
    classification: string;
    is_valid: boolean;
    corrected_classification?: string;
    correction_notes?: string;
    confidence: number;
  };
  imageName: string;
  deerName: string;
}

export default function DetectionCorrectionDialog({
  open,
  onClose,
  detection,
  imageName,
  deerName,
}: DetectionCorrectionDialogProps) {
  const queryClient = useQueryClient();

  const [isValid, setIsValid] = useState(detection.is_valid);
  const [correctedClassification, setCorrectedClassification] = useState(
    detection.corrected_classification || detection.classification
  );
  const [notes, setNotes] = useState(detection.correction_notes || '');
  const [error, setError] = useState<string | null>(null);

  const correctionMutation = useMutation({
    mutationFn: async (data: {
      is_valid?: boolean;
      corrected_classification?: string;
      correction_notes?: string;
    }) => {
      const response = await apiClient.patch(
        `/detections/${detection.detection_id}/correct`,
        {
          ...data,
          reviewed_by: 'user', // TODO: Get actual username
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deer'] });
      onClose();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to save correction');
    },
  });

  const handleSubmit = () => {
    setError(null);

    const hasChanges =
      isValid !== detection.is_valid ||
      correctedClassification !== (detection.corrected_classification || detection.classification) ||
      notes !== (detection.correction_notes || '');

    if (!hasChanges) {
      onClose();
      return;
    }

    correctionMutation.mutate({
      is_valid: isValid,
      corrected_classification:
        correctedClassification !== detection.classification
          ? correctedClassification
          : undefined,
      correction_notes: notes || undefined,
    });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Review Detection</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {/* Image Info */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Deer: <strong>{deerName}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Image: {imageName}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Confidence: {(detection.confidence * 100).toFixed(1)}%
            </Typography>
          </Box>

          {/* Original Classification */}
          <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary">
              ML Classification
            </Typography>
            <Chip
              label={detection.classification}
              color="primary"
              size="small"
              sx={{ mt: 0.5 }}
            />
          </Box>

          {/* Valid/Invalid Toggle */}
          <FormControlLabel
            control={
              <Checkbox
                checked={!isValid}
                onChange={(e) => setIsValid(!e.target.checked)}
                color="error"
              />
            }
            label="Mark as invalid/unusable"
            sx={{ mb: 2 }}
          />

          <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 3, ml: 4 }}>
            Check this if the detection is unusable (rear-end view, wrong species, poor quality, etc.)
          </Typography>

          {/* Corrected Classification */}
          <FormControl component="fieldset" sx={{ mb: 3 }} fullWidth>
            <FormLabel component="legend">Correct Classification</FormLabel>
            <RadioGroup
              value={correctedClassification}
              onChange={(e) => setCorrectedClassification(e.target.value)}
            >
              <FormControlLabel value="buck" control={<Radio />} label="Buck (Male)" />
              <FormControlLabel value="doe" control={<Radio />} label="Doe (Female)" />
              <FormControlLabel value="fawn" control={<Radio />} label="Fawn (Young)" />
              <FormControlLabel value="unknown" control={<Radio />} label="Unknown" />
              <FormControlLabel value="cattle" control={<Radio />} label="Cattle (Not Deer)" />
              <FormControlLabel value="pig" control={<Radio />} label="Pig / Feral Hog (Not Deer)" />
              <FormControlLabel value="raccoon" control={<Radio />} label="Raccoon (Not Deer)" />
            </RadioGroup>
          </FormControl>

          {/* Notes */}
          <TextField
            label="Notes (optional)"
            multiline
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            fullWidth
            placeholder="Explain the issue or correction..."
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
          disabled={correctionMutation.isPending}
        >
          {correctionMutation.isPending ? 'Saving...' : 'Save Review'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
