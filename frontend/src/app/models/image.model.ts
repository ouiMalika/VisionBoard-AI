export interface UploadedImage {
  id: string;
  file: File;
  url: string;
  cluster?: number;
}

export interface ClusterResult {
  [clusterId: string]: string[];
}
