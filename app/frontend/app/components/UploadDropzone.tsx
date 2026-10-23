"use client";

import { useCallback } from "react";

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
}

export default function UploadDropzone({ onFileSelect }: UploadDropzoneProps) {
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const droppedFile = e.dataTransfer.files?.[0];
      if (droppedFile) {
        onFileSelect(droppedFile);
      }
    },
    [onFileSelect]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        onFileSelect(selectedFile);
      }
    },
    [onFileSelect]
  );

  return (
    <div
      className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center bg-slate-800/50 hover:border-sky-500 hover:bg-slate-800 transition-colors"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <p className="text-slate-300 mb-2">
        Drag & drop a chest X-ray image here, or click to browse
      </p>
      <p className="text-xs text-slate-500 mb-4">
        Supports PNG, JPG, DICOM
      </p>
      <label className="inline-block cursor-pointer rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 transition-colors">
        Select Image
        <input
          type="file"
          accept=".png,.jpg,.jpeg,.dcm,image/png,image/jpeg,image/jpg"
          className="hidden"
          onChange={handleChange}
        />
      </label>
    </div>
  );
}
