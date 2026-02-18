import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { listWorkspaces, createWorkspace, deleteWorkspace } from '@/lib/api';

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Create form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceOwner, setNewWorkspaceOwner] = useState('demo-user');
  const [newWorkspaceTags, setNewWorkspaceTags] = useState('');

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    setLoading(true);
    try {
      const result = await listWorkspaces();
      if (result) {
        // API returns array directly, not wrapped in {workspaces: [...]}
        setWorkspaces(Array.isArray(result) ? result : []);
        if (!currentWorkspace && Array.isArray(result) && result.length > 0) {
          setCurrentWorkspace(result[0].workspace_id);
        }
      }
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim()) {
      alert('Please enter a workspace name');
      return;
    }

    setLoading(true);
    try {
      const tags = newWorkspaceTags
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t);

      const result = await createWorkspace({
        name: newWorkspaceName,
        owner: newWorkspaceOwner,
        tags,
      });

      if (result) {
        await loadWorkspaces();
        setShowCreateForm(false);
        setNewWorkspaceName('');
        setNewWorkspaceTags('');
        alert(`Workspace created with ID: ${result.workspace_id}`);
      }
    } catch (error) {
      console.error('Failed to create workspace:', error);
      alert('Failed to create workspace. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWorkspace = async (workspaceId: string) => {
    if (!confirm('Delete this workspace? This cannot be undone.')) return;

    setLoading(true);
    try {
      const result = await deleteWorkspace(workspaceId);
      if (result) {
        await loadWorkspaces();
        if (currentWorkspace === workspaceId) {
          setCurrentWorkspace(null);
        }
      }
    } catch (error) {
      console.error('Failed to delete workspace:', error);
      alert('Failed to delete workspace. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="workspaces-page" className="p-6">
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Workspaces</h1>
          <p className="text-gray-600">Manage isolated workspaces for multi-tenancy</p>
        </div>
        <Button
          onClick={() => setShowCreateForm(!showCreateForm)}
          data-testid="toggle-create-form-btn"
        >
          {showCreateForm ? 'Cancel' : 'Create Workspace'}
        </Button>
      </div>

      {/* Current Workspace Indicator */}
      {currentWorkspace && (
        <Card className="p-4 mb-6 bg-blue-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Current Workspace</p>
              <p className="font-mono text-sm font-semibold" data-testid="current-workspace-id">
                {currentWorkspace}
              </p>
            </div>
            <span className="px-3 py-1 bg-blue-600 text-white text-sm rounded" data-testid="role-badge">
              Admin
            </span>
          </div>
        </Card>
      )}

      {/* Create Workspace Form */}
      {showCreateForm && (
        <Card className="p-4 mb-6" data-testid="create-workspace-form">
          <h2 className="text-lg font-semibold mb-4">Create New Workspace</h2>
          <div className="space-y-4">
            <div>
              <Label htmlFor="workspace-name">Workspace Name</Label>
              <Input
                id="workspace-name"
                data-testid="workspace-name-input"
                placeholder="My Workspace"
                value={newWorkspaceName}
                onChange={(e) => setNewWorkspaceName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="workspace-owner">Owner</Label>
              <Input
                id="workspace-owner"
                data-testid="workspace-owner-input"
                value={newWorkspaceOwner}
                onChange={(e) => setNewWorkspaceOwner(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="workspace-tags">Tags (comma-separated)</Label>
              <Input
                id="workspace-tags"
                data-testid="workspace-tags-input"
                placeholder="demo, test, production"
                value={newWorkspaceTags}
                onChange={(e) => setNewWorkspaceTags(e.target.value)}
              />
            </div>
            <Button
              onClick={handleCreateWorkspace}
              disabled={loading}
              data-testid="create-workspace-btn"
              className="w-full"
            >
              {loading ? 'Creating...' : 'Create Workspace'}
            </Button>
          </div>
        </Card>
      )}

      {/* Workspaces List */}
      <Card className="p-4">
        <h2 className="text-lg font-semibold mb-4">All Workspaces</h2>
        <div className="space-y-3" data-testid="workspaces-list">
          {loading && <p>Loading workspaces...</p>}
          {!loading && workspaces.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              No workspaces found. Create one to get started.
            </p>
          )}
          {!loading &&
            workspaces.map((ws) => (
              <Card
                key={ws.workspace_id}
                data-testid={`workspace-item-${ws.workspace_id}`}
                className={`p-4 border-2 ${
                  currentWorkspace === ws.workspace_id ? 'border-blue-500 bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{ws.name}</h3>
                    <p className="font-mono text-xs text-gray-500 mb-2">
                      {ws.workspace_id}
                    </p>
                    <div className="flex gap-2 items-center">
                      <span className="text-sm text-gray-600">Owner: {ws.owner}</span>
                      {ws.tags && ws.tags.length > 0 && (
                        <div className="flex gap-1">
                          {ws.tags.map((tag: string, idx: number) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => setCurrentWorkspace(ws.workspace_id)}
                      disabled={currentWorkspace === ws.workspace_id}
                      data-testid={`switch-workspace-btn-${ws.workspace_id}`}
                    >
                      {currentWorkspace === ws.workspace_id ? 'Active' : 'Switch'}
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteWorkspace(ws.workspace_id)}
                      data-testid={`delete-workspace-btn-${ws.workspace_id}`}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
        </div>
      </Card>
    </div>
  );
}
