export default function Images() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Image Management</h2>

      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">[IMG]</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Image Upload & Management
          </h3>
          <p className="text-gray-600 mb-6">
            This feature is coming soon. You'll be able to:
          </p>
          <ul className="text-left max-w-md mx-auto space-y-2 text-gray-700">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">[OK]</span>
              Upload images via drag-and-drop
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">[OK]</span>
              View processing status in real-time
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">[OK]</span>
              Filter by location, date, and status
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">[OK]</span>
              View detection results and bounding boxes
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
