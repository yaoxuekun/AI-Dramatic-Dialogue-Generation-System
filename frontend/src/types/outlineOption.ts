export type StoryOutlineOptionType = 'GENRE' | 'STYLE';

export interface StoryOutlineOption {
  id: number;
  type: StoryOutlineOptionType;
  name: string;
  description?: string;
  sortOrder: number;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface StoryOutlineOptionRequest {
  type: StoryOutlineOptionType;
  name: string;
  description?: string;
  sortOrder?: number;
  enabled?: boolean;
}
