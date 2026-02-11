export interface UploadedImage {
  id: string;
  file: File;
  url: string;
  cluster?: number;
}

export interface ClusterGroup {
  images: string[];
  tags: string[];
}

export interface ClusterResult {
  [clusterId: string]: ClusterGroup;
}
