import React, { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@apollo/client/react';
import {
  GET_RELEASES,
  CREATE_RELEASE,
  UPDATE_RELEASE,
  TOGGLE_STEP,
  DELETE_RELEASE,
} from './graphql/queries';
import { Release, ReleaseStatus } from './types';
import { Header } from './components/Header';
import { ReleaseCard } from './components/ReleaseCard';
import { CreateReleaseModal } from './components/CreateReleaseModal';
import { DeleteConfirmModal } from './components/DeleteConfirmModal';
import { Plus, PackageOpen, AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const { data, loading, error, refetch } = useQuery<{ releases: Release[] }>(GET_RELEASES, {
    notifyOnNetworkStatusChange: true,
  });

  const [createRelease] = useMutation(CREATE_RELEASE, {
    refetchQueries: [{ query: GET_RELEASES }],
  });

  const [updateRelease] = useMutation(UPDATE_RELEASE, {
    refetchQueries: [{ query: GET_RELEASES }],
  });

  const [toggleStep] = useMutation(TOGGLE_STEP, {
    refetchQueries: [{ query: GET_RELEASES }],
  });

  const [deleteRelease] = useMutation(DELETE_RELEASE, {
    refetchQueries: [{ query: GET_RELEASES }],
  });

  // Modal and filter state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [filter, setFilter] = useState<'all' | ReleaseStatus>('all');
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const releases: Release[] = useMemo(() => {
    return data?.releases || [];
  }, [data]);

  // Statistics
  const totalCount = releases.length;
  const plannedCount = releases.filter((r) => r.status === 'planned').length;
  const ongoingCount = releases.filter((r) => r.status === 'ongoing').length;
  const doneCount = releases.filter((r) => r.status === 'done').length;

  const filteredReleases = useMemo(() => {
    if (filter === 'all') return releases;
    return releases.filter((r) => r.status === filter);
  }, [releases, filter]);

  // Handlers
  const handleToggleStep = async (releaseId: string, stepId: number) => {
    try {
      await toggleStep({
        variables: {
          releaseId,
          stepId,
        },
      });
    } catch (err) {
      console.error('Failed to toggle step:', err);
    }
  };

  const handleUpdateAdditionalInfo = async (releaseId: string, additionalInfo: string) => {
    await updateRelease({
      variables: {
        input: {
          id: releaseId,
          additionalInfo,
        },
      },
    });
  };

  const handleCreateRelease = async (input: {
    name: string;
    dueDate: string;
    additionalInfo?: string;
  }) => {
    await createRelease({
      variables: {
        input,
      },
    });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteRelease({
        variables: {
          id: deleteTarget.id,
        },
      });
      setDeleteTarget(null);
    } catch (err) {
      console.error('Failed to delete release:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        onOpenCreate={() => setIsCreateOpen(true)}
        totalReleases={totalCount}
        ongoingCount={ongoingCount}
        doneCount={doneCount}
      />

      {/* Toolbar / Filters & Counts */}
      <div className="toolbar">
        <div className="filter-group">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({totalCount})
          </button>
          <button
            className={`filter-btn ${filter === 'planned' ? 'active' : ''}`}
            onClick={() => setFilter('planned')}
          >
            Planned ({plannedCount})
          </button>
          <button
            className={`filter-btn ${filter === 'ongoing' ? 'active' : ''}`}
            onClick={() => setFilter('ongoing')}
          >
            Ongoing ({ongoingCount})
          </button>
          <button
            className={`filter-btn ${filter === 'done' ? 'active' : ''}`}
            onClick={() => setFilter('done')}
          >
            Done ({doneCount})
          </button>
        </div>

        <div className="stats-summary">
          <div className="stats-item">
            <span>Overall:</span>
            <span className="stats-number">{doneCount} / {totalCount} shipped</span>
          </div>
          <button
            className="btn-icon"
            onClick={() => refetch()}
            title="Refresh releases"
            aria-label="Refresh releases"
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && !data && (
        <div className="loading-indicator">
          <div className="spinner" />
          <p>Loading releases from GraphQL API...</p>
        </div>
      )}

      {error && (
        <div
          className="empty-state"
          style={{ borderColor: 'rgba(239, 68, 68, 0.4)', backgroundColor: 'rgba(239, 68, 68, 0.05)' }}
        >
          <AlertCircle size={40} color="var(--danger)" style={{ marginBottom: 12 }} />
          <h3 className="empty-title" style={{ color: 'var(--danger)' }}>
            Error Connecting to API
          </h3>
          <p className="empty-desc">{error.message}</p>
          <button className="btn btn-secondary" onClick={() => refetch()}>
            <RefreshCw size={16} /> Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredReleases.length === 0 && (
        <div className="empty-state">
          <PackageOpen size={48} className="empty-icon" />
          <h3 className="empty-title">
            {filter === 'all'
              ? 'No releases found'
              : `No releases with status "${filter}"`}
          </h3>
          <p className="empty-desc">
            {filter === 'all'
              ? 'Get started by creating your first software release checklist.'
              : 'Try changing your active filter or create a new release.'}
          </p>
          {filter === 'all' && (
            <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
              <Plus size={16} /> Create First Release
            </button>
          )}
        </div>
      )}

      {/* Releases Cards List */}
      <main className="releases-grid">
        {filteredReleases.map((release) => (
          <ReleaseCard
            key={release.id}
            release={release}
            onToggleStep={handleToggleStep}
            onUpdateAdditionalInfo={handleUpdateAdditionalInfo}
            onDeleteRequest={(id, name) => setDeleteTarget({ id, name })}
          />
        ))}
      </main>

      {/* Create Release Modal */}
      <CreateReleaseModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreate={handleCreateRelease}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        releaseName={deleteTarget?.name || ''}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        isDeleting={isDeleting}
      />
    </div>
  );
};

export default App;
