import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Typography,
  useTheme,
} from '@mui/material';
import {
  Pets as PetsIcon,
  Visibility as VisibilityIcon,
  Male as MaleIcon,
  Female as FemaleIcon,
} from '@mui/icons-material';
import { getDeerList } from '../api/deer';

export default function Dashboard() {
  const theme = useTheme();
  const navigate = useNavigate();

  const { data: deerData, isLoading } = useQuery({
    queryKey: ['deer', 'list'],
    queryFn: () => getDeerList({ page_size: 100, min_sightings: 1 }),
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  const stats = {
    totalDeer: deerData?.total || 0,
    totalSightings: deerData?.deer.reduce((sum, d) => sum + d.sighting_count, 0) || 0,
    bucks: deerData?.deer.filter(d => d.sex === 'buck').length || 0,
    does: deerData?.deer.filter(d => d.sex === 'doe').length || 0,
    fawns: deerData?.deer.filter(d => d.sex === 'fawn').length || 0,
  };

  const recentDeer = deerData?.deer.slice(0, 5) || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Dashboard Overview
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Deer"
            value={stats.totalDeer}
            icon={<PetsIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.primary.main}
            onClick={() => navigate('/deer?sort=sighting_count')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Sightings"
            value={stats.totalSightings}
            icon={<VisibilityIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.success.main}
            onClick={() => navigate('/images')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Bucks"
            value={stats.bucks}
            icon={<MaleIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.info.main}
            onClick={() => navigate('/deer?sex=buck&sort=sighting_count')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Does"
            value={stats.does}
            icon={<FemaleIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.secondary.main}
            onClick={() => navigate('/deer?sex=doe&sort=sighting_count')}
          />
        </Grid>
      </Grid>

      {/* Population Breakdown and Recent Deer */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Population Breakdown
              </Typography>
              <Box sx={{ mt: 3 }}>
                <PopulationBar
                  label="Bucks"
                  count={stats.bucks}
                  total={stats.totalDeer}
                  color={theme.palette.info.main}
                />
                <PopulationBar
                  label="Does"
                  count={stats.does}
                  total={stats.totalDeer}
                  color={theme.palette.secondary.main}
                />
                <PopulationBar
                  label="Fawns"
                  count={stats.fawns}
                  total={stats.totalDeer}
                  color={theme.palette.warning.main}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recently Seen Deer
              </Typography>
              <List>
                {recentDeer.map((deer) => (
                  <ListItem
                    key={deer.id}
                    sx={{
                      bgcolor: 'background.default',
                      borderRadius: 1,
                      mb: 1,
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                    onClick={() => navigate(`/deer/${deer.id}`)}
                  >
                    <ListItemText
                      primary={deer.name || `Deer ${deer.id.slice(0, 8)}`}
                      secondary={`${deer.sex} • ${deer.sighting_count} sightings`}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {new Date(deer.last_seen).toLocaleDateString()}
                    </Typography>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
}

function StatCard({ title, value, icon, color, onClick }: StatCardProps) {
  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s',
        '&:hover': onClick ? {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        } : {},
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" variant="body2" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h3" component="div" sx={{ fontWeight: 600 }}>
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              color,
              opacity: 0.8,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

interface PopulationBarProps {
  label: string;
  count: number;
  total: number;
  color: string;
}

function PopulationBar({ label, count, total, color }: PopulationBarProps) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" color="text.primary">
          {label}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {count} ({percentage.toFixed(1)}%)
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={percentage}
        sx={{
          height: 8,
          borderRadius: 4,
          bgcolor: 'grey.200',
          '& .MuiLinearProgress-bar': {
            bgcolor: color,
            borderRadius: 4,
          },
        }}
      />
    </Box>
  );
}
