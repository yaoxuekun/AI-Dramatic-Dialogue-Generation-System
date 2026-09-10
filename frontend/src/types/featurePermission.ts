import type { UserRole } from './auth';

export interface FeaturePermission {
  id: number;
  featureKey: string;
  featureName: string;
  category: string;
  description?: string;
  allowedRoles: UserRole[];
  enabled: boolean;
  sortOrder: number;
}

export interface FeaturePermissionUpdateRequest {
  allowedRoles: UserRole[];
  enabled?: boolean;
}
