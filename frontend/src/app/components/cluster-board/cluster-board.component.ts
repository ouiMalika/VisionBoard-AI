import { Component, EventEmitter, Input, Output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClusterResult } from '../../models/image.model';

@Component({
  selector: 'app-cluster-board',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cluster-board.component.html',
  styleUrl: './cluster-board.component.css',
})
export class ClusterBoardComponent implements OnInit {
  @Input() clusterResult: ClusterResult = {};
  @Input() clusterCount = 0;
  @Output() back = new EventEmitter<void>();

  clusterEntries: { id: string; urls: string[]; tags: string[] }[] = [];

  ngOnInit(): void {
    this.clusterEntries = Object.entries(this.clusterResult).map(
      ([id, group]) => ({ id, urls: group.images, tags: group.tags })
    );
  }

  onBack(): void {
    this.back.emit();
  }
}
