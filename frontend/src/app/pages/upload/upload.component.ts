import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss',
})
export class UploadComponent {
  selectedFiles: File[] = [];
  previews: string[] = [];
  boardName = '';
  nClusters = 3;
  uploading = false;
  clustering = false;
  jobId = '';
  statusMessage = '';
  dragOver = false;

  constructor(private api: ApiService, private router: Router) {}

  onFilesSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.addFiles(Array.from(input.files));
    }
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.dragOver = false;
    if (event.dataTransfer?.files) {
      this.addFiles(Array.from(event.dataTransfer.files));
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.dragOver = true;
  }

  onDragLeave() {
    this.dragOver = false;
  }

  private addFiles(files: File[]) {
    const imageFiles = files.filter((f) => f.type.startsWith('image/'));
    this.selectedFiles.push(...imageFiles);
    for (const f of imageFiles) {
      const reader = new FileReader();
      reader.onload = (e) => this.previews.push(e.target?.result as string);
      reader.readAsDataURL(f);
    }
  }

  removeFile(index: number) {
    this.selectedFiles.splice(index, 1);
    this.previews.splice(index, 1);
  }

  generate() {
    if (this.selectedFiles.length === 0) return;

    this.uploading = true;
    this.statusMessage = 'Uploading images...';

    this.api.upload(this.selectedFiles).subscribe({
      next: (res) => {
        this.uploading = false;
        this.clustering = true;
        this.statusMessage = 'Clustering images and generating tags...';

        const name = this.boardName || 'My Moodboard';
        this.api.cluster(res.image_urls, this.nClusters, name).subscribe({
          next: (clusterRes) => {
            this.jobId = clusterRes.job_id;
            this.pollJob();
          },
          error: () => {
            this.clustering = false;
            this.statusMessage = 'Failed to start clustering.';
          },
        });
      },
      error: () => {
        this.uploading = false;
        this.statusMessage = 'Upload failed. Check your connection.';
      },
    });
  }

  private pollJob() {
    const interval = setInterval(() => {
      this.api.jobStatus(this.jobId).subscribe({
        next: (job) => {
          if (job.status === 'SUCCESS') {
            clearInterval(interval);
            this.clustering = false;
            this.statusMessage = 'Moodboards created!';
            setTimeout(() => this.router.navigate(['/boards']), 1200);
          } else if (job.status === 'FAILURE') {
            clearInterval(interval);
            this.clustering = false;
            this.statusMessage = 'Clustering failed. Please try again.';
          }
        },
      });
    }, 2000);
  }
}
