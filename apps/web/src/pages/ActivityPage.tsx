import { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getActivity, resetActivity, getPresence } from '@/lib/api';

const TYPE_COLORS: Record<string, string> = {
  'run.execute': 'bg-blue-100 text-blue-800',
  'report.build': 'bg-green-100 text-green-800',
  'job.submit': 'bg-purple-100 text-purple-800',
  'policy.evaluate': 'bg-yellow-100 text-yellow-800',
  'eval.suite_run': 'bg-orange-100 text-orange-800',
  'sre.playbook_generate': 'bg-red-100 text-red-800',
  'search.reindex': 'bg-gray-100 text-gray-800',
  'presence.join': 'bg-teal-100 text-teal-800',
  'presence.leave': 'bg-pink-100 text-pink-800',
};

const STATUS_COLORS: Record<string, string> = {
  online: 'bg-green-500',
  idle: 'bg-yellow-400',
  offline: 'bg-gray-400',
};

const ALL_TYPES = Object.keys(TYPE_COLORS);

export default function ActivityPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [presence, setPresence] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [liveConnected, setLiveConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const loadActivity = async () => {
    setLoading(true);
    const data = await getActivity({ workspace_id: 'demo-workspace', limit: 50 });
    if (data?.events) setEvents(data.events);
    const pData = await getPresence({ workspace_id: 'demo-workspace' });
    if (pData?.presence) setPresence(pData.presence);
    setLoading(false);
  };

  const handleReset = async () => {
    setLoading(true);
    await resetActivity();
    await loadActivity();
    setLoading(false);
  };

  const connectLive = () => {
    if (esRef.current) {
      esRef.current.close();
    }
    const es = new EventSource('http://localhost:8090/events/activity?workspace_id=demo-workspace');
    esRef.current = es;
    es.addEventListener('activity.connected', () => {
      setLiveConnected(true);
    });
    es.addEventListener('activity.event', (e: MessageEvent) => {
      try {
        const ev = JSON.parse(e.data);
        setEvents(prev => {
          const exists = prev.some(p => p.event_id === ev.event_id);
          return exists ? prev : [ev, ...prev];
        });
      } catch {}
    });
    es.onerror = () => {
      setLiveConnected(false);
      es.close();
    };
  };

  useEffect(() => {
    loadActivity();
    return () => {
      esRef.current?.close();
    };
  }, []);

  const filteredEvents = activeFilter
    ? events.filter(e => e.type === activeFilter)
    : events;

  return (
    <div data-testid="activity-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Activity Stream</h1>
          <p className="text-muted-foreground">Real-time workspace activity and presence</p>
        </div>
        <div className="flex gap-2">
          {liveConnected && (
            <Badge className="bg-green-500 text-white" data-testid="activity-live-badge">
              ● Live
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={connectLive} data-testid="activity-connect-live">
            Connect Live
          </Button>
          <Button size="sm" onClick={loadActivity} disabled={loading} data-testid="activity-refresh">
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleReset} data-testid="activity-reset">
            Reset Demo
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Activity Feed */}
        <div className="col-span-2 space-y-3">
          {/* Type Filters */}
          <div className="flex flex-wrap gap-2" data-testid="activity-filters">
            <Button
              size="sm"
              variant={activeFilter === null ? 'default' : 'outline'}
              onClick={() => setActiveFilter(null)}
              data-testid="activity-filter-all"
            >
              All
            </Button>
            {ALL_TYPES.map(t => (
              <Button
                key={t}
                size="sm"
                variant={activeFilter === t ? 'default' : 'outline'}
                onClick={() => setActiveFilter(activeFilter === t ? null : t)}
                data-testid={`activity-filter-${t.replace('.', '-')}`}
              >
                {t}
              </Button>
            ))}
          </div>

          {/* Feed */}
          <Card className="p-4" data-testid="activity-feed">
            {loading && <p className="text-muted-foreground text-sm">Loading...</p>}
            {!loading && filteredEvents.length === 0 && (
              <p className="text-muted-foreground text-sm">No events</p>
            )}
            {filteredEvents.length > 0 && (
              <ul className="space-y-2" data-testid="activity-feed-ready">
                {filteredEvents.map((ev, idx) => (
                  <li
                    key={ev.event_id}
                    className="flex items-start gap-3 py-2 border-b last:border-0"
                    data-testid={`activity-item-${idx}`}
                    data-event-id={ev.event_id}
                    data-event-type={ev.type}
                  >
                    <span
                      className={`text-xs font-mono px-2 py-0.5 rounded ${TYPE_COLORS[ev.type] ?? 'bg-gray-100 text-gray-700'}`}
                    >
                      {ev.type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">{ev.message}</p>
                      <p className="text-xs text-muted-foreground">{ev.actor}   {ev.ts}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        {/* Presence Panel */}
        <div className="space-y-3">
          <h2 className="font-semibold text-lg">Presence</h2>
          <Card className="p-4" data-testid="presence-panel">
            {presence.length === 0 && (
              <p className="text-muted-foreground text-sm">No presence data</p>
            )}
            {presence.length > 0 && (
              <ul className="space-y-3" data-testid="presence-ready">
                {presence.map((user, idx) => (
                  <li
                    key={user.actor}
                    className="flex items-center gap-3"
                    data-testid={`presence-user-${idx}`}
                    data-actor={user.actor}
                    data-status={user.status}
                  >
                    {/* Avatar */}
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-bold flex-shrink-0">
                      {user.display?.[0]?.toUpperCase() ?? '?'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium">{user.display}</p>
                      <p className="text-xs text-muted-foreground truncate">{user.actor}</p>
                    </div>
                    <span className="flex items-center gap-1">
                      <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[user.status] ?? 'bg-gray-400'}`} />
                      <span className="text-xs capitalize">{user.status}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
