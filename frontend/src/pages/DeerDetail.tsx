import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getDeer, getDeerTimeline, getDeerLocations } from '../api/deer'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function DeerDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: deer, isLoading: deerLoading } = useQuery({
    queryKey: ['deer', id],
    queryFn: () => getDeer(id!),
    enabled: !!id,
  })

  const { data: timeline } = useQuery({
    queryKey: ['deer', id, 'timeline'],
    queryFn: () => getDeerTimeline(id!, 'day'),
    enabled: !!id,
  })

  const { data: locations } = useQuery({
    queryKey: ['deer', id, 'locations'],
    queryFn: () => getDeerLocations(id!),
    enabled: !!id,
  })

  if (deerLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading deer details...</div>
      </div>
    )
  }

  if (!deer) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Deer not found</div>
        <Link to="/deer" className="text-blue-600 hover:underline mt-4 inline-block">
          Back to gallery
        </Link>
      </div>
    )
  }

  const sexColors = {
    buck: 'bg-amber-100 text-amber-800',
    doe: 'bg-pink-100 text-pink-800',
    fawn: 'bg-blue-100 text-blue-800',
    unknown: 'bg-gray-100 text-gray-800',
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link to="/deer" className="text-blue-600 hover:underline text-sm mb-2 inline-block">
          ← Back to gallery
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">
              {deer.name || `Deer ${deer.id.slice(0, 8)}`}
            </h2>
            <div className="flex items-center gap-2 mt-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${sexColors[deer.sex]}`}>
                {deer.sex}
              </span>
              <span className="text-gray-500 text-sm">
                ID: {deer.id.slice(0, 16)}...
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total Sightings"
          value={deer.sighting_count}
        />
        <StatCard
          label="Average Confidence"
          value={`${(deer.confidence * 100).toFixed(1)}%`}
        />
        <StatCard
          label="First Seen"
          value={new Date(deer.first_seen).toLocaleDateString()}
        />
        <StatCard
          label="Last Seen"
          value={new Date(deer.last_seen).toLocaleDateString()}
        />
      </div>

      {/* Timeline Chart */}
      {timeline && timeline.timeline.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Activity Timeline
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeline.timeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="period"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => new Date(value as string).toLocaleDateString()}
                  formatter={(value: number) => [value, 'Sightings']}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Locations */}
      {locations && locations.locations.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Location Patterns
          </h3>
          <div className="space-y-3">
            {locations.locations.map((location) => (
              <div
                key={location.location_id}
                className="p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">
                    {location.location_name}
                  </h4>
                  <span className="text-sm font-semibold text-blue-600">
                    {location.sighting_count} sightings
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="text-gray-500">First seen:</span>{' '}
                    {new Date(location.first_seen).toLocaleDateString()}
                  </div>
                  <div>
                    <span className="text-gray-500">Last seen:</span>{' '}
                    {new Date(location.last_seen).toLocaleDateString()}
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-500">Avg confidence:</span>{' '}
                    {(location.avg_confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
}

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
    </div>
  )
}
