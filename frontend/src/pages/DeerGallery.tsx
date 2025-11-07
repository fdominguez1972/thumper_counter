import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getDeerList, Deer } from '../api/deer'

export default function DeerGallery() {
  const [sexFilter, setSexFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('last_seen')

  const { data, isLoading } = useQuery({
    queryKey: ['deer', 'list', sexFilter, sortBy],
    queryFn: () => getDeerList({
      page_size: 100,
      sex: sexFilter !== 'all' ? sexFilter : undefined,
      sort_by: sortBy,
    }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading deer...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Deer Gallery</h2>
        <div className="text-sm text-gray-600">
          {data?.total || 0} deer total
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Sex
            </label>
            <select
              value={sexFilter}
              onChange={(e) => setSexFilter(e.target.value)}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="all">All</option>
              <option value="buck">Bucks</option>
              <option value="doe">Does</option>
              <option value="fawn">Fawns</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="last_seen">Last Seen</option>
              <option value="first_seen">First Seen</option>
              <option value="sighting_count">Sighting Count</option>
            </select>
          </div>
        </div>
      </div>

      {/* Deer Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {data?.deer.map((deer) => (
          <DeerCard key={deer.id} deer={deer} />
        ))}
      </div>

      {data?.deer.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No deer found matching your filters
        </div>
      )}
    </div>
  )
}

interface DeerCardProps {
  deer: Deer
}

function DeerCard({ deer }: DeerCardProps) {
  const sexColors = {
    buck: 'bg-amber-100 text-amber-800',
    doe: 'bg-pink-100 text-pink-800',
    fawn: 'bg-blue-100 text-blue-800',
    unknown: 'bg-gray-100 text-gray-800',
  }

  const sexIcons = {
    buck: '🦌',
    doe: '🦌',
    fawn: '🦌',
    unknown: '❓',
  }

  return (
    <Link
      to={`/deer/${deer.id}`}
      className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden"
    >
      {/* Placeholder image */}
      <div className="h-48 bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
        <span className="text-6xl">{sexIcons[deer.sex]}</span>
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {deer.name || `Deer ${deer.id.slice(0, 8)}`}
          </h3>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${sexColors[deer.sex]}`}>
            {deer.sex}
          </span>
        </div>

        <div className="space-y-1 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Sightings:</span>
            <span className="font-medium">{deer.sighting_count}</span>
          </div>
          <div className="flex justify-between">
            <span>Confidence:</span>
            <span className="font-medium">{(deer.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span>Last seen:</span>
            <span className="font-medium">
              {new Date(deer.last_seen).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>
    </Link>
  )
}
