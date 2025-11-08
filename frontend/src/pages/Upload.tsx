import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  FormControlLabel,
  InputLabel,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Switch,
  Typography,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import apiClient from '../api/client';

interface Location {
  id: string;
  name: string;
}

interface UploadFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

export default function Upload() {
  const queryClient = useQueryClient();
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const [processImmediately, setProcessImmediately] = useState(false);
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  // Fetch locations
  const { data: locationsData, isLoading: locationsLoading } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      const response = await apiClient.get('/locations');
      return response.data;
    },
  });

  const locations: Location[] = locationsData?.locations || [];

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async ({ files, locationName, processImmediately }: { files: File[], locationName: string, processImmediately: boolean }) => {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      formData.append('location_name', locationName);
      formData.append('process_immediately', processImmediately.toString());

      const response = await apiClient.post('/images', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] });
    },
  });

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    const imageFiles = droppedFiles.filter(file => file.type.startsWith('image/'));

    const newFiles: UploadFile[] = imageFiles.map(file => ({
      file,
      status: 'pending',
      progress: 0,
    }));

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      const newFiles: UploadFile[] = selectedFiles.map(file => ({
        file,
        status: 'pending',
        progress: 0,
      }));

      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleRemoveFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (!selectedLocation || files.length === 0) {
      return;
    }

    setFiles(prev => prev.map(f => ({ ...f, status: 'uploading', progress: 0 })));

    const filesToUpload = files.map(f => f.file);
    const locationName = locations.find(l => l.id === selectedLocation)?.name || '';

    try {
      await uploadMutation.mutateAsync({
        files: filesToUpload,
        locationName,
        processImmediately,
      });

      setFiles(prev => prev.map(f => ({ ...f, status: 'success', progress: 100 })));

      // Clear files after 2 seconds
      setTimeout(() => {
        setFiles([]);
      }, 2000);
    } catch (error: any) {
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'error',
        progress: 0,
        error: error.response?.data?.detail || 'Upload failed',
      })));
    }
  };

  const handleClearAll = () => {
    setFiles([]);
  };

  const pendingFiles = files.filter(f => f.status === 'pending');
  const successFiles = files.filter(f => f.status === 'success');
  const errorFiles = files.filter(f => f.status === 'error');
  const uploadingFiles = files.filter(f => f.status === 'uploading');

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 3 }}>
        Image Upload
      </Typography>

      {/* Location Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            1. Select Location
          </Typography>
          <FormControl fullWidth disabled={locationsLoading}>
            <InputLabel>Camera Location</InputLabel>
            <Select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              label="Camera Location"
            >
              {locations.map(location => (
                <MenuItem key={location.id} value={location.id}>
                  {location.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={processImmediately}
                onChange={(e) => setProcessImmediately(e.target.checked)}
              />
            }
            label="Process images immediately after upload"
            sx={{ mt: 2 }}
          />
          <Typography variant="caption" display="block" color="text.secondary" sx={{ ml: 4 }}>
            If enabled, images will be queued for ML processing right away
          </Typography>
        </CardContent>
      </Card>

      {/* File Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            2. Select Images
          </Typography>

          <Box
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            sx={{
              border: '2px dashed',
              borderColor: isDragging ? 'primary.main' : 'divider',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              bgcolor: isDragging ? 'action.hover' : 'background.paper',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <CloudUploadIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Drag and drop images here
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              or
            </Typography>
            <Button
              variant="contained"
              component="label"
            >
              Browse Files
              <input
                type="file"
                hidden
                multiple
                accept="image/*"
                onChange={handleFileSelect}
              />
            </Button>
            <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 2 }}>
              Supported formats: JPG, PNG, JPEG (max 50MB per file)
            </Typography>
          </Box>

          {/* File List */}
          {files.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1">
                  Selected Files ({files.length})
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {pendingFiles.length > 0 && (
                    <Chip label={`${pendingFiles.length} pending`} size="small" />
                  )}
                  {uploadingFiles.length > 0 && (
                    <Chip label={`${uploadingFiles.length} uploading`} color="primary" size="small" />
                  )}
                  {successFiles.length > 0 && (
                    <Chip label={`${successFiles.length} uploaded`} color="success" size="small" />
                  )}
                  {errorFiles.length > 0 && (
                    <Chip label={`${errorFiles.length} failed`} color="error" size="small" />
                  )}
                  <Button size="small" onClick={handleClearAll}>Clear All</Button>
                </Box>
              </Box>

              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {files.map((uploadFile, index) => (
                  <ListItem
                    key={index}
                    secondaryAction={
                      uploadFile.status === 'pending' && (
                        <Button
                          size="small"
                          startIcon={<DeleteIcon />}
                          onClick={() => handleRemoveFile(index)}
                        >
                          Remove
                        </Button>
                      )
                    }
                  >
                    <ListItemText
                      primary={uploadFile.file.name}
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            {(uploadFile.file.size / 1024 / 1024).toFixed(2)} MB
                          </Typography>
                          {uploadFile.status === 'uploading' && (
                            <LinearProgress variant="indeterminate" sx={{ mt: 1 }} />
                          )}
                          {uploadFile.error && (
                            <Typography variant="caption" color="error" display="block">
                              {uploadFile.error}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    {uploadFile.status === 'success' && <CheckCircleIcon color="success" />}
                    {uploadFile.status === 'error' && <ErrorIcon color="error" />}
                    {uploadFile.status === 'uploading' && <CircularProgress size={24} />}
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Upload Button */}
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<CloudUploadIcon />}
          onClick={handleUpload}
          disabled={!selectedLocation || files.length === 0 || uploadMutation.isPending}
        >
          {uploadMutation.isPending ? 'Uploading...' : `Upload ${files.length} Image${files.length !== 1 ? 's' : ''}`}
        </Button>
      </Box>
    </Box>
  );
}
