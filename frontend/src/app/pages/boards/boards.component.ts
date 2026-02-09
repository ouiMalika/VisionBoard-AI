import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService, BoardData } from '../../services/api.service';

@Component({
  selector: 'app-boards',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './boards.component.html',
  styleUrl: './boards.component.scss',
})
export class BoardsComponent implements OnInit {
  boards: BoardData[] = [];
  loading = true;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadBoards();
  }

  loadBoards() {
    this.loading = true;
    this.api.getBoards().subscribe({
      next: (boards) => {
        this.boards = boards;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  deleteBoard(id: number) {
    this.api.deleteBoard(id).subscribe(() => {
      this.boards = this.boards.filter((b) => b.id !== id);
    });
  }

  coverImage(board: BoardData): string {
    return board.images.length > 0 ? board.images[0].url : '';
  }
}
