import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClientProvider } from '@tanstack/react-query';
import { theme } from './theme';
import { queryClient } from './api/queryClient';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import DeerGallery from './pages/DeerGallery';
import DeerDetail from './pages/DeerDetail';
import DeerImages from './pages/DeerImages';
import Images from './pages/Images';
import Upload from './pages/Upload';
import Locations from './pages/Locations';
import SeasonalAnalysis from './pages/SeasonalAnalysis';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/deer" element={<DeerGallery />} />
              <Route path="/deer/:id" element={<DeerDetail />} />
              <Route path="/deer/:id/images" element={<DeerImages />} />
              <Route path="/images" element={<Images />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/locations" element={<Locations />} />
              <Route path="/seasonal" element={<SeasonalAnalysis />} />
            </Routes>
          </Layout>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
