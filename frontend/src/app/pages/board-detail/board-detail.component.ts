import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ApiService, BoardData } from '../../services/api.service';

@Component({
  selector: 'app-board-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './board-detail.component.html',
  styleUrl: './board-detail.component.scss',
})
export class BoardDetailComponent implements OnInit {
  board: BoardData | null = null;
  loading = true;
  editingName = false;
  editName = '';
  newTag = '';

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getBoard(id).subscribe({
      next: (board) => {
        this.board = board;
        this.editName = board.name;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  saveName() {
    if (!this.board) return;
    this.api.updateBoard(this.board.id, { name: this.editName }).subscribe(() => {
      this.board!.name = this.editName;
      this.editingName = false;
    });
  }

  addTag() {
    if (!this.board || !this.newTag.trim()) return;
    const tags = [...this.board.tags, this.newTag.trim()];
    this.api.updateBoard(this.board.id, { tags }).subscribe(() => {
      this.board!.tags = tags;
      this.newTag = '';
    });
  }

  removeTag(tag: string) {
    if (!this.board) return;
    const tags = this.board.tags.filter((t) => t !== tag);
    this.api.updateBoard(this.board.id, { tags }).subscribe(() => {
      this.board!.tags = tags;
    });
  }
}
