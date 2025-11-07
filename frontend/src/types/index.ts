// TypeScript types for API responses

export enum DeerSex {
  MALE = 'male',
  FEMALE = 'female',
  UNKNOWN = 'unknown',
}

export enum DeerStatus {
  ALIVE = 'alive',
  DECEASED = 'deceased',
  UNKNOWN = 'unknown',
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface Location {
  id: string;
  name: string;
  description?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  image_count: number;
  created_at: string;
  updated_at: string;
}

export interface Deer {
  id: string;
  name?: string;
  sex: DeerSex;
  species: string;
  status: DeerStatus;
  first_seen: string;
  last_seen: string;
  sighting_count: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Detection {
  id: string;
  image_id: string;
  deer_id?: string;
  bbox_x1: number;
  bbox_y1: number;
  bbox_x2: number;
  bbox_y2: number;
  confidence: number;
  class_id: number;
  class_name: string;
  deer?: Deer;
  created_at: string;
}

export interface Image {
  id: string;
  filename: string;
  path: string;
  timestamp: string;
  location_id: string;
  location?: Location;
  processing_status: ProcessingStatus;
  exif_data?: Record<string, any>;
  detections?: Detection[];
  created_at: string;
  updated_at: string;
}

export interface ProcessingStatusResponse {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
}

export interface DashboardStats {
  total_deer: number;
  total_sightings: number;
  total_images: number;
  images_processed: number;
  images_pending: number;
  buck_count: number;
  doe_count: number;
  fawn_count: number;
  buck_breakdown: {
    young: number;
    mid: number;
    mature: number;
  };
}

export interface TimelineData {
  period: string;
  count: number;
}

export interface LocationVisit {
  location_id: string;
  location_name: string;
  visit_count: number;
  first_visit: string;
  last_visit: string;
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// API error response
export interface ApiError {
  detail: string;
  status_code: number;
}
