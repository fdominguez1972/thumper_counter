/**
 * Seasonal Analysis API Client
 * Feature: 008-rut-season-analysis
 */

import { apiClient } from './client';

/**
 * Seasonal filter options
 */
export type SeasonalFilter = 'RUT_SEASON' | 'SPRING' | 'SUMMER' | 'FALL';

export interface SeasonalImagesParams {
  season: SeasonalFilter;
  year: number;
  location_id?: string;
  status_filter?: string;
  has_detections?: boolean;
  page?: number;
  page_size?: number;
}

export interface SeasonalDetectionsParams {
  season: SeasonalFilter;
  year: number;
  classification?: string;
  min_confidence?: number;
  deer_id?: string;
  page?: number;
  page_size?: number;
}

export interface SeasonalActivityParams {
  season: SeasonalFilter;
  year: number;
  group_by?: 'day' | 'week' | 'month';
  compare_to_non_season?: boolean;
}

export interface ComparisonParams {
  periods: Array<{
    season: SeasonalFilter;
    year: number;
  }>;
  group_by?: 'day' | 'week' | 'month';
}

export interface PDFReportParams {
  report_type: 'seasonal_activity' | 'comparison' | 'custom';
  start_date: string;
  end_date: string;
  title?: string;
  group_by?: 'day' | 'week' | 'month';
  include_charts?: boolean;
  include_tables?: boolean;
  include_insights?: boolean;
  comparison_periods?: Array<{
    season: SeasonalFilter;
    year: number;
  }>;
}

export interface ZIPExportParams {
  detection_ids: string[];
  include_crops?: boolean;
  include_metadata_csv?: boolean;
  crop_size?: number;
}

/**
 * Get seasonal images with filters
 */
export const getSeasonalImages = async (params: SeasonalImagesParams) => {
  const response = await apiClient.get('/seasonal/images', { params });
  return response.data;
};

/**
 * Get seasonal detections with filters
 */
export const getSeasonalDetections = async (params: SeasonalDetectionsParams) => {
  const response = await apiClient.get('/seasonal/detections', { params });
  return response.data;
};

/**
 * Get seasonal activity report
 */
export const getSeasonalActivityReport = async (params: SeasonalActivityParams) => {
  const response = await apiClient.get('/reports/seasonal/activity', { params });
  return response.data;
};

/**
 * Get seasonal comparison report
 */
export const getSeasonalComparisonReport = async (params: ComparisonParams) => {
  const response = await apiClient.get('/reports/seasonal/comparison', { params });
  return response.data;
};

/**
 * Generate PDF report
 */
export const generatePDFReport = async (params: PDFReportParams) => {
  const response = await apiClient.post('/exports/pdf', params);
  return response.data;
};

/**
 * Check PDF report status
 */
export const checkPDFStatus = async (jobId: string) => {
  const response = await apiClient.get(`/exports/pdf/${jobId}`);
  return response.data;
};

/**
 * Generate ZIP export
 */
export const generateZIPExport = async (params: ZIPExportParams) => {
  const response = await apiClient.post('/exports/zip', params);
  return response.data;
};

/**
 * Check ZIP export status
 */
export const checkZIPStatus = async (jobId: string) => {
  const response = await apiClient.get(`/exports/zip/${jobId}`);
  return response.data;
};

/**
 * Delete export job
 */
export const deleteExportJob = async (jobId: string) => {
  await apiClient.delete(`/exports/${jobId}`);
};

/**
 * Get download URL for export file
 */
export const getExportDownloadUrl = (filename: string) => {
  return `${apiClient.defaults.baseURL}/static/exports/${filename}`;
};
