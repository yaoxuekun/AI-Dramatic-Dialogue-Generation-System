export type PromptParameterDirection = 'INPUT' | 'OUTPUT';
export type PromptScope = 'DEFAULT' | 'SPECIFIC';

export interface AiPromptParameter {
  id?: number;
  direction: PromptParameterDirection;
  paramKey: string;
  paramName: string;
  dataType: string;
  requiredFlag: boolean;
  description?: string;
  exampleValue?: string;
  sortOrder: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface AiPrompt {
  id: number;
  promptKey: string;
  basePromptKey: string;
  promptScope: PromptScope;
  matchGenre?: string;
  matchStyle?: string;
  priority: number;
  promptName: string;
  category?: string;
  description?: string;
  templateContent: string;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
  parameters: AiPromptParameter[];
  children?: AiPrompt[];
}

export interface AiPromptRequest {
  promptKey: string;
  basePromptKey?: string;
  promptScope?: PromptScope;
  matchGenre?: string;
  matchStyle?: string;
  priority?: number;
  promptName: string;
  category?: string;
  description?: string;
  templateContent: string;
  enabled?: boolean;
  parameters: AiPromptParameter[];
}
