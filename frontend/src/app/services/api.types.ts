export interface UploadResponse {
  image_urls: string[];
}

export interface ClusterResponse {
  job_id: string;
  board_name: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE';
  result: any;
}
