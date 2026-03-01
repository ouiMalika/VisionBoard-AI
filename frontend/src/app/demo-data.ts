import { ClusterResult } from './models/image.model';

/**
 * Pre-computed clustering result used for the "Try Demo" feature.
 * Images are from Lorem Picsum (stable public CDN, no API key needed).
 * Cluster groups simulate what the CLIP + KMeans pipeline would produce
 * for a curated set of 15 images across three visual themes.
 */
export const DEMO_RESULT: ClusterResult = {
  '0': {
    images: [
      'https://picsum.photos/id/10/400/300',
      'https://picsum.photos/id/11/400/300',
      'https://picsum.photos/id/13/400/300',
      'https://picsum.photos/id/15/400/300',
      'https://picsum.photos/id/28/400/300',
    ],
    tags: ['nature', 'landscape', 'outdoors'],
  },
  '1': {
    images: [
      'https://picsum.photos/id/42/400/300',
      'https://picsum.photos/id/43/400/300',
      'https://picsum.photos/id/44/400/300',
      'https://picsum.photos/id/106/400/300',
      'https://picsum.photos/id/107/400/300',
    ],
    tags: ['architecture', 'minimalist', 'urban'],
  },
  '2': {
    images: [
      'https://picsum.photos/id/26/400/300',
      'https://picsum.photos/id/48/400/300',
      'https://picsum.photos/id/64/400/300',
      'https://picsum.photos/id/65/400/300',
      'https://picsum.photos/id/91/400/300',
    ],
    tags: ['lifestyle', 'warm tones', 'portrait'],
  },
};
