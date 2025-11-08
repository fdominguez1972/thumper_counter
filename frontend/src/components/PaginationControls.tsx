import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  IconButton,
  TextField,
  Typography,
} from '@mui/material';
import {
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
} from '@mui/icons-material';

interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function PaginationControls({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationControlsProps) {
  const [pageInput, setPageInput] = useState(currentPage.toString());

  useEffect(() => {
    setPageInput(currentPage.toString());
  }, [currentPage]);

  const handlePageJump = (e: React.FormEvent) => {
    e.preventDefault();
    const pageNum = parseInt(pageInput);
    if (pageNum >= 1 && pageNum <= totalPages) {
      onPageChange(pageNum);
    } else {
      setPageInput(currentPage.toString());
    }
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
      <IconButton
        onClick={() => onPageChange(1)}
        disabled={currentPage === 1}
        title="First Page"
      >
        <FirstPageIcon />
      </IconButton>
      <Button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        startIcon={<PrevIcon />}
      >
        Previous
      </Button>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="body2">Page</Typography>
        <form onSubmit={handlePageJump}>
          <TextField
            value={pageInput}
            onChange={(e) => setPageInput(e.target.value)}
            type="number"
            size="small"
            sx={{ width: '80px' }}
            inputProps={{ min: 1, max: totalPages }}
          />
        </form>
        <Typography variant="body2">of {totalPages}</Typography>
      </Box>

      <Button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        endIcon={<NextIcon />}
      >
        Next
      </Button>
      <IconButton
        onClick={() => onPageChange(totalPages)}
        disabled={currentPage === totalPages}
        title="Last Page"
      >
        <LastPageIcon />
      </IconButton>
    </Box>
  );
}
