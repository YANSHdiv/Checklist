export type ReleaseStatus = 'planned' | 'ongoing' | 'done';

export interface Release {
  id: string;
  name: string;
  dueDate: string;
  additionalInfo?: string | null;
  completedSteps: number[];
  status: ReleaseStatus;
  createdAt: string;
  updatedAt: string;
}

export interface Step {
  id: number;
  title: string;
}

export const FIXED_STEPS: Step[] = [
  { id: 1, title: 'Code freeze' },
  { id: 2, title: 'Run automated tests' },
  { id: 3, title: 'Review changelog' },
  { id: 4, title: 'Update documentation' },
  { id: 5, title: 'Run security checks' },
  { id: 6, title: 'Build production bundle' },
  { id: 7, title: 'Deploy to staging' },
  { id: 8, title: 'Run smoke tests' },
  { id: 9, title: 'Deploy to production' },
  { id: 10, title: 'Verify production' },
];
