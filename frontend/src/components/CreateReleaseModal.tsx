import React, { useState } from 'react';
import { X, Plus, Calendar, Tag, FileText } from 'lucide-react';

interface CreateReleaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (input: {
    name: string;
    dueDate: string;
    additionalInfo?: string;
  }) => Promise<void>;
}

export const CreateReleaseModal: React.FC<CreateReleaseModalProps> = ({
  isOpen,
  onClose,
  onCreate,
}) => {
  // Format current datetime for default datetime-local input
  const getDefaultDateTime = () => {
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    nextWeek.setMinutes(0);
    return nextWeek.toISOString().slice(0, 16);
  };

  const [name, setName] = useState('');
  const [dueDate, setDueDate] = useState(getDefaultDateTime());
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Release name is required');
      return;
    }
    if (!dueDate) {
      setError('Due date is required');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      // Convert to ISO 8601 string for GraphQL
      const isoDueDate = new Date(dueDate).toISOString();
      await onCreate({
        name: name.trim(),
        dueDate: isoDueDate,
        additionalInfo: additionalInfo.trim() || undefined,
      });
      // Reset form
      setName('');
      setAdditionalInfo('');
      setDueDate(getDefaultDateTime());
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create release');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="modal-header">
          <h2 id="modal-title" className="modal-title">
            Create New Release
          </h2>
          <button
            className="btn-icon"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="form-error">{error}</div>}

            <div className="form-group">
              <label className="form-label" htmlFor="release-name">
                <Tag size={13} style={{ display: 'inline', marginRight: 4 }} />
                Release Name <span>*</span>
              </label>
              <input
                id="release-name"
                type="text"
                className="form-input"
                placeholder="e.g. v2.4.0 - Performance & Billing Upgrade"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="due-date">
                <Calendar size={13} style={{ display: 'inline', marginRight: 4 }} />
                Target Due Date & Time <span>*</span>
              </label>
              <input
                id="due-date"
                type="datetime-local"
                className="form-input"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="additional-info">
                <FileText size={13} style={{ display: 'inline', marginRight: 4 }} />
                Additional Information (Optional)
              </label>
              <textarea
                id="additional-info"
                className="form-textarea"
                placeholder="Add deployment instructions, key stakeholder approvals, rollback procedures..."
                value={additionalInfo}
                onChange={(e) => setAdditionalInfo(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              <Plus size={16} />
              {isSubmitting ? 'Creating...' : 'Create Release'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
