/**
 * Deer API endpoints
 */

import apiClient from './client';

export interface Deer {
  id: string;
  name: string | null;
  sex: 'buck' | 'doe' | 'fawn' | 'unknown';
  first_seen: string;
  last_seen: string;
  confidence: number;
  sighting_count: number;
}

export interface DeerListResponse {
  deer: Deer[];
  total: number;
  page: number;
  page_size: number;
}

export interface TimelineData {
  deer_id: string;
  group_by: string;
  total_sightings: number;
  date_range: {
    first: string;
    last: string;
  };
  timeline: Array<{
    period: string;
    count: number;
    avg_confidence: number;
  }>;
}

export interface LocationData {
  deer_id: string;
  total_sightings: number;
  unique_locations: number;
  locations: Array<{
    location_id: string;
    location_name: string;
    sighting_count: number;
    first_seen: string;
    last_seen: string;
    avg_confidence: number;
  }>;
}

/**
 * Get list of all deer
 */
export const getDeerList = async (params?: {
  page?: number;
  page_size?: number;
  sex?: string;
  sort_by?: string;
}): Promise<DeerListResponse> => {
  const response = await apiClient.get('/deer', { params });
  return response.data;
};

/**
 * Get specific deer by ID
 */
export const getDeer = async (id: string): Promise<Deer> => {
  const response = await apiClient.get(`/deer/${id}`);
  return response.data;
};

/**
 * Get deer timeline (activity over time)
 */
export const getDeerTimeline = async (
  id: string,
  groupBy: 'hour' | 'day' | 'week' | 'month' = 'day'
): Promise<TimelineData> => {
  const response = await apiClient.get(`/deer/${id}/timeline`, {
    params: { group_by: groupBy },
  });
  return response.data;
};

/**
 * Get deer locations (movement patterns)
 */
export const getDeerLocations = async (id: string): Promise<LocationData> => {
  const response = await apiClient.get(`/deer/${id}/locations`);
  return response.data;
};

/**
 * Update deer (name, notes, etc.)
 */
export const updateDeer = async (
  id: string,
  data: {
    name?: string;
    notes?: string;
    status?: string;
  }
): Promise<Deer> => {
  const response = await apiClient.put(`/deer/${id}`, data);
  return response.data;
};
