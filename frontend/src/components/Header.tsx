import React from 'react';
import { CheckSquare, Plus } from 'lucide-react';

interface HeaderProps {
  onOpenCreate: () => void;
  totalReleases: number;
  ongoingCount: number;
  doneCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenCreate,
  totalReleases,
  ongoingCount,
  doneCount,
}) => {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon">
          <CheckSquare size={26} />
        </div>
        <div>
          <h1 className="brand-title">Release Checklist</h1>
          <p className="brand-subtitle">
            Manage release cycles, track checklist progress, and automate delivery status
          </p>
        </div>
      </div>
      <div className="header-actions">
        <button
          className="btn btn-primary"
          onClick={onOpenCreate}
          aria-label="Create new release"
        >
          <Plus size={18} />
          New Release
        </button>
      </div>
    </header>
  );
};
