import React, { useState } from 'react';
import {
  Calendar,
  Trash2,
  Check,
  Edit2,
  FileText,
  Clock,
  CheckCircle2,
  Circle,
  Save,
  X,
} from 'lucide-react';
import { Release, FIXED_STEPS } from '../types';

interface ReleaseCardProps {
  release: Release;
  onToggleStep: (releaseId: string, stepId: number) => void;
  onUpdateAdditionalInfo: (releaseId: string, info: string) => Promise<void>;
  onDeleteRequest: (releaseId: string, releaseName: string) => void;
}

export const ReleaseCard: React.FC<ReleaseCardProps> = ({
  release,
  onToggleStep,
  onUpdateAdditionalInfo,
  onDeleteRequest,
}) => {
  const [isEditingInfo, setIsEditingInfo] = useState(false);
  const [infoText, setInfoText] = useState(release.additionalInfo || '');
  const [isSavingInfo, setIsSavingInfo] = useState(false);

  const completedCount = (release.completedSteps || []).length;
  const totalSteps = FIXED_STEPS.length;
  const progressPercent = Math.round((completedCount / totalSteps) * 100);

  // Format Due Date
  const formattedDueDate = (() => {
    try {
      const d = new Date(release.dueDate);
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      }).format(d);
    } catch {
      return release.dueDate;
    }
  })();

  const handleSaveInfo = async () => {
    setIsSavingInfo(true);
    try {
      await onUpdateAdditionalInfo(release.id, infoText);
      setIsEditingInfo(false);
    } catch (err) {
      console.error('Failed to update additional info', err);
    } finally {
      setIsSavingInfo(false);
    }
  };

  const handleCancelInfo = () => {
    setInfoText(release.additionalInfo || '');
    setIsEditingInfo(false);
  };

  return (
    <div className={`release-card status-${release.status}`}>
      {/* Top Header */}
      <div className="card-top">
        <div className="card-title-group">
          <h2 className="release-name">{release.name}</h2>
          <span className={`badge badge-${release.status}`}>
            {release.status === 'done' && <CheckCircle2 size={12} />}
            {release.status === 'ongoing' && <Clock size={12} />}
            {release.status === 'planned' && <Circle size={12} />}
            {release.status}
          </span>
        </div>

        <div className="card-meta-actions">
          <div className="meta-due-date" title="Release Due Date">
            <Calendar size={15} />
            <span>{formattedDueDate}</span>
          </div>
          <button
            className="btn-icon"
            onClick={() => onDeleteRequest(release.id, release.name)}
            title="Delete release"
            aria-label={`Delete release ${release.name}`}
          >
            <Trash2 size={17} />
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-container">
        <div className="progress-header">
          <span className="progress-label">Checklist Progress</span>
          <span className="progress-counter">
            {completedCount} / {totalSteps} ({progressPercent}%)
          </span>
        </div>
        <div className="progress-track">
          <div
            className={`progress-fill status-${release.status}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Checklist Steps Grid */}
      <div className="checklist-section">
        <div className="checklist-title">Release Steps</div>
        <div className="checklist-grid">
          {FIXED_STEPS.map((step) => {
            const isCompleted = release.completedSteps?.includes(step.id);
            return (
              <div
                key={step.id}
                className={`checklist-item ${isCompleted ? 'checked' : ''}`}
                onClick={() => onToggleStep(release.id, step.id)}
                role="checkbox"
                aria-checked={isCompleted}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === ' ' || e.key === 'Enter') {
                    e.preventDefault();
                    onToggleStep(release.id, step.id);
                  }
                }}
              >
                <div className="checkbox-custom">
                  {isCompleted && <Check size={12} strokeWidth={3} />}
                </div>
                <span className="checklist-text">
                  {step.id}. {step.title}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Additional Information Section */}
      <div className="additional-info-box">
        <div className="info-header">
          <div className="info-title">
            <FileText size={15} />
            <span>Additional Information</span>
          </div>
          {!isEditingInfo && (
            <button
              className="btn-text"
              onClick={() => {
                setInfoText(release.additionalInfo || '');
                setIsEditingInfo(true);
              }}
            >
              <Edit2 size={13} />
              {release.additionalInfo ? 'Edit' : 'Add Note'}
            </button>
          )}
        </div>

        {isEditingInfo ? (
          <div className="info-edit-area">
            <textarea
              className="info-textarea"
              value={infoText}
              onChange={(e) => setInfoText(e.target.value)}
              placeholder="Enter release notes, deployment instructions, or rollback plan..."
              rows={3}
              autoFocus
            />
            <div className="info-edit-actions">
              <button
                className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                onClick={handleCancelInfo}
                disabled={isSavingInfo}
              >
                <X size={14} />
                Cancel
              </button>
              <button
                className="btn btn-primary"
                style={{ padding: '4px 12px', fontSize: '0.8rem' }}
                onClick={handleSaveInfo}
                disabled={isSavingInfo}
              >
                <Save size={14} />
                {isSavingInfo ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        ) : (
          <div className="info-content">
            {release.additionalInfo ? (
              release.additionalInfo
            ) : (
              <span className="info-empty">No additional details provided.</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
