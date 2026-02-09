import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.css',
})
export class UploadComponent {
  @Input() clusterCount = 3;
  @Input() uploadedCount = 0;
  @Input() uploading = false;

  @Output() filesAdded = new EventEmitter<File[]>();
  @Output() clusterCountChange = new EventEmitter<number>();
  @Output() createBoard = new EventEmitter<void>();

  isDragging = false;
  previewUrls: string[] = [];

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    const files = event.dataTransfer?.files;
    if (files) {
      this.handleFiles(Array.from(files));
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.handleFiles(Array.from(input.files));
    }
    input.value = '';
  }

  onClusterCountInput(value: string): void {
    const n = parseInt(value, 10);
    if (!isNaN(n)) {
      this.clusterCountChange.emit(n);
    }
  }

  onCreateBoard(): void {
    this.createBoard.emit();
  }

  private handleFiles(files: File[]): void {
    const imageFiles = files.filter((f) => f.type.startsWith('image/'));
    for (const file of imageFiles) {
      this.previewUrls.push(URL.createObjectURL(file));
    }
    this.filesAdded.emit(imageFiles);
  }
}
