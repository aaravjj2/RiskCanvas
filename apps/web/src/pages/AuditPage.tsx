import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { listAuditEvents } from '@/lib/api';

export default function AuditPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  // Filters
  const [workspace, setWorkspace] = useState('');
  const [actor, setActor] = useState('');
  const [resourceType, setResourceType] = useState('');

  useEffect(() => {
    loadAuditEvents();
  }, [workspace, actor, resourceType]);

  const loadAuditEvents = async () => {
    setLoading(true);
    const filters: any = {};
    if (workspace) filters.workspace_id = workspace;
    if (actor) filters.actor = actor;
    if (resourceType) filters.resource_type = resourceType;

    const result = await listAuditEvents(filters);
    if (result) {
      setEvents(result.events || []);
    }
    setLoading(false);
  };

  const toggleExpand = (eventId: string) => {
    setExpandedEvent(expandedEvent === eventId ? null : eventId);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard');
  };

  return (
    <div data-testid="audit-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Audit Log</h1>
        <p className="text-gray-600">View all system events with deterministic hashes</p>
      </div>

      {/* Filters */}
      <Card className="p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="filter-workspace">Workspace ID</Label>
            <Input
              id="filter-workspace"
              data-testid="filter-workspace-input"
              placeholder="workspace-abc..."
              value={workspace}
              onChange={(e) => setWorkspace(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="filter-actor">Actor</Label>
            <Input
              id="filter-actor"
              data-testid="filter-actor-input"
              placeholder="user@example.com"
              value={actor}
              onChange={(e) => setActor(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="filter-resource">Resource Type</Label>
            <Select value={resourceType} onValueChange={setResourceType}>
              <SelectTrigger data-testid="filter-resource-select">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All types</SelectItem>
                <SelectItem value="portfolio">Portfolio</SelectItem>
                <SelectItem value="run">Run</SelectItem>
                <SelectItem value="report">Report</SelectItem>
                <SelectItem value="hedge">Hedge</SelectItem>
                <SelectItem value="workspace">Workspace</SelectItem>
                <SelectItem value="monitor">Monitor</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Audit Events Table */}
      <Card className="p-4">
        <h2 className="text-lg font-semibold mb-4">Audit Events</h2>
        <div data-testid="audit-events-table">
          {loading && <p>Loading audit events...</p>}
          {!loading && events.length === 0 && (
            <p className="text-gray-500 text-center py-8">No audit events found</p>
          )}
          {!loading && events.length > 0 && (
            <div className="space-y-2">
              {events.map((event) => (
                <Card
                  key={event.event_id}
                  data-testid={`audit-event-${event.event_id}`}
                  className="p-3 border hover:border-blue-500 cursor-pointer"
                  onClick={() => toggleExpand(event.event_id)}
                >
                  {/* Compact View */}
                  <div className="grid grid-cols-6 gap-4 text-sm">
                    <div>
                      <p className="text-xs text-gray-500">Sequence</p>
                      <p className="font-mono font-semibold">#{event.sequence}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Actor</p>
                      <p className="truncate">{event.actor}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Action</p>
                      <p className="font-semibold">{event.action}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Resource</p>
                      <p className="truncate">{event.resource_type}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Result</p>
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          event.result === 'success'
                            ? 'bg-green-100 text-green-800'
                            : event.result === 'failure'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {event.result}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Event ID</p>
                      <p className="font-mono text-xs truncate">{event.event_id.substring(0, 12)}...</p>
                    </div>
                  </div>

                  {/* Expanded View */}
                  {expandedEvent === event.event_id && (
                    <div className="mt-4 pt-4 border-t space-y-3">
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-1">Full Event ID</p>
                        <div className="flex gap-2 items-center">
                          <code className="text-xs bg-gray-100 p-1 rounded flex-1 overflow-x-auto">
                            {event.event_id}
                          </code>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              copyToClipboard(event.event_id);
                            }}
                            className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                            data-testid={`copy-event-id-${event.event_id}`}
                          >
                            Copy
                          </button>
                        </div>
                      </div>

                      {event.workspace_id && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 mb-1">Workspace ID</p>
                          <code className="text-xs bg-gray-100 p-1 rounded block overflow-x-auto">
                            {event.workspace_id}
                          </code>
                        </div>
                      )}

                      {event.resource_id && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 mb-1">Resource ID</p>
                          <code className="text-xs bg-gray-100 p-1 rounded block overflow-x-auto">
                            {event.resource_id}
                          </code>
                        </div>
                      )}

                      {event.input_hash && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 mb-1">Input Hash (SHA256)</p>
                          <div className="flex gap-2 items-center">
                            <code className="text-xs bg-gray-100 p-1 rounded flex-1 overflow-x-auto">
                              {event.input_hash}
                            </code>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                copyToClipboard(event.input_hash);
                              }}
                              className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                            >
                              Copy
                            </button>
                          </div>
                        </div>
                      )}

                      {event.output_hash && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 mb-1">Output Hash (SHA256)</p>
                          <div className="flex gap-2 items-center">
                            <code className="text-xs bg-gray-100 p-1 rounded flex-1 overflow-x-auto">
                              {event.output_hash}
                            </code>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                copyToClipboard(event.output_hash);
                              }}
                              className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                            >
                              Copy
                            </button>
                          </div>
                        </div>
                      )}

                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 mb-1">Metadata</p>
                          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(event.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
