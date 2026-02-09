import { Component } from '@angular/core';
import { UploadComponent } from './components/upload/upload.component';
import { ClusterBoardComponent } from './components/cluster-board/cluster-board.component';
import { ApiService } from './services/api.service';
import { ClusterResult } from './models/image.model';
import { switchMap } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [UploadComponent, ClusterBoardComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  files: File[] = [];
  clusterCount = 3;
  showBoard = false;
  uploading = false;
  error = '';
  clusterResult: ClusterResult = {};

  constructor(private api: ApiService) {}

  onFilesAdded(newFiles: File[]): void {
    this.files = [...this.files, ...newFiles];
  }

  onClusterCountChange(n: number): void {
    this.clusterCount = n;
  }

  onCreateBoard(): void {
    if (this.files.length === 0) {
      this.error = 'Please upload some images first.';
      return;
    }

    if (this.clusterCount < 1 || this.clusterCount > this.files.length) {
      this.error = `Please enter a valid number of groups (1-${this.files.length}).`;
      return;
    }

    this.error = '';
    this.uploading = true;

    this.api.uploadImages(this.files).pipe(
      switchMap((uploadRes) =>
        this.api.startClustering(uploadRes.image_urls, this.clusterCount)
      ),
      switchMap((clusterRes) =>
        this.api.pollJobStatus(clusterRes.job_id)
      ),
    ).subscribe({
      next: (jobRes) => {
        this.uploading = false;
        if (jobRes.status === 'SUCCESS' && jobRes.result) {
          this.clusterResult = jobRes.result;
          this.showBoard = true;
        } else {
          this.error = 'Clustering failed. Please try again.';
        }
      },
      error: (err) => {
        this.uploading = false;
        this.error = 'Something went wrong. Please try again.';
        console.error(err);
      },
    });
  }

  onBackToUpload(): void {
    this.showBoard = false;
  }
}
