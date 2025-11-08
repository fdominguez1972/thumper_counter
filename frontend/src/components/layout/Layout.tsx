import { ReactNode, useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Pets as PetsIcon,
  PhotoLibrary as PhotoLibraryIcon,
  CloudUpload as UploadIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import apiClient from '../../api/client';

interface LayoutProps {
  children: ReactNode;
}

const DRAWER_WIDTH = 240;

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: <DashboardIcon /> },
  { name: 'Deer Gallery', href: '/deer', icon: <PetsIcon /> },
  { name: 'Images', href: '/images', icon: <PhotoLibraryIcon /> },
  { name: 'Upload', href: '/upload', icon: <UploadIcon /> },
  { name: 'Locations', href: '/locations', icon: <LocationIcon /> },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const theme = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Fetch review count for progress tracking
  const { data: reviewStats } = useQuery({
    queryKey: ['review-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/detections/stats/reviewed');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const reviewCount = reviewStats?.reviewed_count || 0;
  const reviewProgress = Math.min((reviewCount / 500) * 100, 100);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 600 }}>
          Thumper Counter
        </Typography>
      </Toolbar>
      <List>
        {navigation.map((item) => {
          const isActive = location.pathname === item.href ||
            (item.href !== '/dashboard' && location.pathname.startsWith(item.href));

          return (
            <ListItem key={item.name} disablePadding>
              <ListItemButton
                component={RouterLink}
                to={item.href}
                selected={isActive}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: theme.palette.primary.light,
                    color: theme.palette.primary.contrastText,
                    '&:hover': {
                      backgroundColor: theme.palette.primary.main,
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ color: isActive ? theme.palette.primary.contrastText : 'inherit' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.name} />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Deer Tracking Dashboard
          </Typography>
          <Box sx={{ display: { xs: 'none', sm: 'block' }, textAlign: 'right' }}>
            <Typography variant="body2">
              Hopkins Ranch
            </Typography>
            <Tooltip title={`${reviewCount} of 500 reviews completed. Review images to improve AI accuracy.`}>
              <Box sx={{ minWidth: 150 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                    Reviews: {reviewCount}/500
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 'bold' }}>
                    {reviewProgress.toFixed(0)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={reviewProgress}
                  sx={{
                    height: 4,
                    borderRadius: 2,
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: reviewCount >= 500 ? '#4caf50' : '#fff',
                    },
                  }}
                />
              </Box>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: 8,
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
