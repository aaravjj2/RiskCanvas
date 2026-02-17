import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, XCircle, Database, Radio } from "lucide-react";
import { listJobs, cancelJob, getJobsBackend } from "@/lib/api";
import { EventClient } from "@/lib/eventClient";

interface Job {
  job_id: string;
  workspace_id: string;
  job_type: string;
  status: string;
  created_at: string;
  completed_at?: string;
  result?: any;
  error?: string;
}

interface JobsBackend {
  backend: string;
  persistent: boolean;
  description: string;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<{ job_type?: string; status?: string }>({});
  const [backend, setBackend] = useState<JobsBackend>({ backend: "memory", persistent: false, description: "Loading..." });
  const [connected, setConnected] = useState(false);
  const eventClientRef = useRef<EventClient | null>(null);

  useEffect(() => {
    loadJobs();
    loadBackend();
    
    // Set up SSE for live updates (v2.7+)
    setupLiveUpdates();
    
    return () => {
      // Cleanup on unmount
      if (eventClientRef.current) {
        eventClientRef.current.disconnect();
      }
    };
  }, [filter]);
  
  const setupLiveUpdates = () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8090';
    const client = new EventClient(`${apiUrl}/events/jobs`);
    
    client.addEventListener('job.created', (data: Job) => {
      console.log('[JobsPage] Job created:', data);
      setJobs(prev => [data, ...prev]);
    });
    
    client.addEventListener('job.status_changed', (data: Job) => {
      console.log('[JobsPage] Job status changed:', data);
      setJobs(prev => prev.map(job => 
        job.job_id === data.job_id ? data : job
      ));
    });
    
    // Track connection status
    client.connect();
    setConnected(true);
    
    eventClientRef.current = client;
  };

  const loadJobs = async () => {
    setLoading(true);
    const result = await listJobs(filter);
    if (result && result.jobs) {
      setJobs(result.jobs);
    }
    setLoading(false);
  };

  const loadBackend = async () => {
    const result = await getJobsBackend();
    if (result) {
      setBackend(result);
    }
  };

  const handleRefresh = () => {
    loadJobs();
  };

  const handleCancelJob = async (jobId: string) => {
    await cancelJob(jobId);
    loadJobs();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "succeeded":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      case "running":
        return "bg-blue-100 text-blue-800";
      case "queued":
        return "bg-yellow-100 text-yellow-800";
      case "cancelled":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getJobTypeColor = (jobType: string) => {
    switch (jobType) {
      case "run":
        return "bg-purple-100 text-purple-800";
      case "report":
        return "bg-indigo-100 text-indigo-800";
      case "hedge":
        return "bg-teal-100 text-teal-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div data-testid="jobs-page" className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Job Queue</h1>
          <p className="text-gray-600">Async job management and execution tracking</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2" data-testid="job-store-backend-badge">
            <Database className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-600">{backend.backend}</span>
            {backend.persistent && (
              <Badge variant="outline" className="text-xs">persistent</Badge>
            )}
          </div>
          {connected && (
            <div className="flex items-center gap-2" data-testid="live-updates-badge">
              <Radio className="h-4 w-4 text-green-500 animate-pulse" />
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">live</Badge>
            </div>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={handleRefresh}
            disabled={loading}
            data-testid="refresh-jobs-btn"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <div>
            <label className="text-sm font-semibold mb-2 block">Job Type</label>
            <select
              className="border rounded px-3 py-2"
              value={filter.job_type || ""}
              onChange={(e) => setFilter({ ...filter, job_type: e.target.value || undefined })}
              data-testid="filter-job-type"
            >
              <option value="">All</option>
              <option value="run">Run</option>
              <option value="report">Report</option>
              <option value="hedge">Hedge</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-semibold mb-2 block">Status</label>
            <select
              className="border rounded px-3 py-2"
              value={filter.status || ""}
              onChange={(e) => setFilter({ ...filter, status: e.target.value || undefined })}
              data-testid="filter-status"
            >
              <option value="">All</option>
              <option value="queued">Queued</option>
              <option value="running">Running</option>
              <option value="succeeded">Succeeded</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Job History */}
      <Card>
        <CardHeader>
          <CardTitle>Job History</CardTitle>
          <CardDescription>All submitted jobs with deterministic IDs</CardDescription>
        </CardHeader>
        <CardContent>
          <div data-testid="jobs-list" className="space-y-4">
            {loading && (
              <div className="text-muted-foreground text-center py-8">
                Loading jobs...
              </div>
            )}

            {!loading && jobs.length === 0 && (
              <div className="text-muted-foreground text-center py-8">
                No jobs found
              </div>
            )}

            {!loading && jobs.length > 0 && jobs.map((job) => (
              <div
                key={job.job_id}
                className="border rounded-lg p-4"
                data-testid={`job-${job.job_id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className={getJobTypeColor(job.job_type)}>
                        {job.job_type.toUpperCase()}
                      </Badge>
                      <Badge className={getStatusColor(job.status)}>
                        {job.status.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="font-mono text-sm text-gray-700">{job.job_id}</p>
                    <p className="text-sm text-gray-600">Workspace: {job.workspace_id}</p>
                    <p className="text-xs text-gray-500">Created: {job.created_at}</p>
                    {job.completed_at && (
                      <p className="text-xs text-gray-500">Completed: {job.completed_at}</p>
                    )}
                    {job.error && (
                      <p className="text-xs text-red-600 mt-2">Error: {job.error}</p>
                    )}
                  </div>
                  <div>
                    {(job.status === "queued" || job.status === "running") && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleCancelJob(job.job_id)}
                        data-testid={`cancel-job-${job.job_id}`}
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
