import { useQuery } from '@tanstack/react-query'
import { getDeerList } from '../api/deer'

export default function Dashboard() {
  const { data: deerData, isLoading } = useQuery({
    queryKey: ['deer', 'list'],
    queryFn: () => getDeerList({ page_size: 100 }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  const stats = {
    totalDeer: deerData?.total || 0,
    totalSightings: deerData?.deer.reduce((sum, d) => sum + d.sighting_count, 0) || 0,
    bucks: deerData?.deer.filter(d => d.sex === 'buck').length || 0,
    does: deerData?.deer.filter(d => d.sex === 'doe').length || 0,
    fawns: deerData?.deer.filter(d => d.sex === 'fawn').length || 0,
  }

  const recentDeer = deerData?.deer.slice(0, 5) || []

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard Overview</h2>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Deer"
          value={stats.totalDeer}
          icon="🦌"
          color="blue"
        />
        <StatCard
          title="Total Sightings"
          value={stats.totalSightings}
          icon="👁️"
          color="green"
        />
        <StatCard
          title="Bucks"
          value={stats.bucks}
          icon="🦌"
          color="amber"
        />
        <StatCard
          title="Does"
          value={stats.does}
          icon="🦌"
          color="pink"
        />
      </div>

      {/* Population Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Population Breakdown
          </h3>
          <div className="space-y-3">
            <PopulationBar label="Bucks" count={stats.bucks} total={stats.totalDeer} color="bg-amber-500" />
            <PopulationBar label="Does" count={stats.does} total={stats.totalDeer} color="bg-pink-500" />
            <PopulationBar label="Fawns" count={stats.fawns} total={stats.totalDeer} color="bg-blue-500" />
          </div>
        </div>

        {/* Recent Deer */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Recently Seen Deer
          </h3>
          <div className="space-y-3">
            {recentDeer.map((deer) => (
              <div
                key={deer.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div>
                  <div className="font-medium text-gray-900">
                    {deer.name || `Deer ${deer.id.slice(0, 8)}`}
                  </div>
                  <div className="text-sm text-gray-500">
                    {deer.sex} • {deer.sighting_count} sightings
                  </div>
                </div>
                <div className="text-sm text-gray-400">
                  {new Date(deer.last_seen).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: number
  icon: string
  color: string
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    amber: 'bg-amber-50 text-amber-700',
    pink: 'bg-pink-50 text-pink-700',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className={`text-4xl p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

interface PopulationBarProps {
  label: string
  count: number
  total: number
  color: string
}

function PopulationBar({ label, count, total, color }: PopulationBarProps) {
  const percentage = total > 0 ? (count / total) * 100 : 0

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="text-gray-500">
          {count} ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
