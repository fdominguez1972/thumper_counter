import { useEffect, useRef, useState } from 'react';
import { Box, IconButton, Tooltip } from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';

interface Detection {
  id: string;
  classification: string;
  corrected_classification?: string;
  confidence: number;
  is_valid: boolean;
  is_reviewed: boolean;
  bbox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

interface BoundingBoxCanvasProps {
  imageUrl: string;
  detections: Detection[];
  alt?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
  title?: string;
}

const CLASSIFICATION_COLORS: { [key: string]: string } = {
  buck: '#2196F3',      // Blue
  doe: '#E91E63',       // Pink
  fawn: '#FF9800',      // Orange
  unknown: '#9E9E9E',   // Gray
  cattle: '#8BC34A',    // Green
  pig: '#FF5722',       // Deep Orange
  raccoon: '#795548',   // Brown
  human: '#F44336',     // Red
  vehicle: '#607D8B',   // Blue Gray
  default: '#FFFFFF',   // White
};

export default function BoundingBoxCanvas({
  imageUrl,
  detections,
  alt = 'Image',
  onClick,
  style,
  title,
}: BoundingBoxCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const [showBoxes, setShowBoxes] = useState(true);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      setImageDimensions({ width: img.width, height: img.height });
      setImageLoaded(true);
      imageRef.current = img;
      if (showBoxes) {
        drawBoundingBoxes();
      }
    };
    img.src = imageUrl;
  }, [imageUrl]);

  useEffect(() => {
    if (imageLoaded) {
      drawBoundingBoxes();
    }
  }, [showBoxes, imageLoaded, detections]);

  const drawBoundingBoxes = () => {
    const canvas = canvasRef.current;
    const img = imageRef.current;

    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match image natural size
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;

    // Draw image
    ctx.drawImage(img, 0, 0);

    // Draw bounding boxes if enabled
    if (showBoxes && detections && detections.length > 0) {
      detections.forEach((detection) => {
        if (!detection.bbox) return;

        const { x, y, width, height } = detection.bbox;
        const classification = detection.corrected_classification || detection.classification;
        const color = CLASSIFICATION_COLORS[classification.toLowerCase()] || CLASSIFICATION_COLORS.default;

        // Draw bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.strokeRect(x, y, width, height);

        // Draw label background
        const label = `${classification} (${(detection.confidence * 100).toFixed(0)}%)`;
        ctx.font = '20px Arial';
        const textMetrics = ctx.measureText(label);
        const textHeight = 24;
        const padding = 6;
        const labelWidth = textMetrics.width + padding * 2;
        const labelHeight = textHeight + padding;

        ctx.fillStyle = color;
        ctx.fillRect(x, y - labelHeight, labelWidth, labelHeight);

        // Draw label text
        ctx.fillStyle = '#000000';
        ctx.fillText(label, x + padding, y - padding);

        // Add reviewed indicator if reviewed
        if (detection.is_reviewed) {
          ctx.fillStyle = '#4CAF50';
          ctx.beginPath();
          ctx.arc(x + width - 15, y + 15, 10, 0, 2 * Math.PI);
          ctx.fill();

          // Draw checkmark
          ctx.strokeStyle = '#FFFFFF';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(x + width - 18, y + 15);
          ctx.lineTo(x + width - 15, y + 18);
          ctx.lineTo(x + width - 10, y + 10);
          ctx.stroke();
        }
      });
    }
  };

  const toggleBoxes = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowBoxes(!showBoxes);
  };

  return (
    <Box sx={{ position: 'relative', display: 'inline-block' }}>
      {/* Toggle Button */}
      <IconButton
        onClick={toggleBoxes}
        sx={{
          position: 'absolute',
          top: 8,
          left: 8,
          color: 'white',
          bgcolor: 'rgba(0, 0, 0, 0.5)',
          '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.7)' },
          zIndex: 2,
        }}
      >
        <Tooltip title={showBoxes ? 'Hide bounding boxes' : 'Show bounding boxes'}>
          {showBoxes ? <Visibility /> : <VisibilityOff />}
        </Tooltip>
      </IconButton>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        onClick={onClick}
        style={{
          width: '100%',
          height: 'auto',
          maxHeight: '90vh',
          objectFit: 'contain',
          cursor: onClick ? 'zoom-in' : 'default',
          display: imageLoaded ? 'block' : 'none',
          ...style,
        }}
        title={title}
      />

      {/* Fallback image while loading */}
      {!imageLoaded && (
        <img
          src={imageUrl}
          alt={alt}
          style={{
            width: '100%',
            height: 'auto',
            maxHeight: '90vh',
            objectFit: 'contain',
            ...style,
          }}
        />
      )}
    </Box>
  );
}
