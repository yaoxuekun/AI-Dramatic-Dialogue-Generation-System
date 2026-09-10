export interface FileUploadResponse {
  originalFilename: string;
  filePath: string;
  fileUrl: string;
  size: number;
  contentType?: string;
}
