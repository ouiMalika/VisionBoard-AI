import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
//import { ApiService, BoardData } from './services/api.service';
import { ApiService, BoardData } from './app/services/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  template: `
    <h1>VisionBoard Demo</h1>

    <input type="file" multiple (change)="onFiles($event)" />
    <button (click)="run()" [disabled]="files.length === 0">
      Upload & Cluster
    </button>

    <p *ngIf="status">Status: {{ status }}</p>

    <div class="boards" *ngIf="boards.length">
      <div class="board" *ngFor="let board of boards">
        <h3>{{ board.name }}</h3>

        <div class="images">
          <img *ngFor="let img of board.images" [src]="img.url" />
        </div>

        <div class="tags">
          <span *ngFor="let tag of board.tags">#{{ tag }}</span>
        </div>
      </div>
    </div>
  `,
})
export class AppComponent implements OnInit {
  files: File[] = [];
  status = '';
  boards: BoardData[] = [];

  constructor(private api: ApiService) {}

  async ngOnInit() {
    await this.api.ensureAnonymousToken();
    this.loadBoards();
  }

  onFiles(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files) this.files = Array.from(input.files);
  }

  run() {
    this.api.upload(this.files).subscribe(upload => {
      this.api.cluster(upload.image_urls, 'Portfolio Demo').subscribe(job => {
        this.poll(job.job_id);
      });
    });
  }

  poll(jobId: string) {
    const timer = setInterval(() => {
      this.api.jobStatus(jobId).subscribe(res => {
        this.status = res.status;
        if (res.status === 'SUCCESS') {
          clearInterval(timer);
          this.loadBoards();
        }
      });
    }, 1000);
  }

  loadBoards() {
    this.api.getBoards().subscribe(b => (this.boards = b));
  }
}
