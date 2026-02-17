/**
 * Server-Sent Events (SSE) client for real-time updates (v2.7+).
 * 
 * Usage:
 * ```typescript
 * const client = new EventClient('/events/jobs');
 * client.addEventListener('job.status_changed', (data) => {
 *   console.log('Job updated:', data);
 * });
 * client.connect();
 * ```
 */

export type EventHandler = (data: any) => void;

export class EventClient {
  private url: string;
  private eventSource: EventSource | null = null;
  private handlers: Map<string, EventHandler[]> = new Map();
  private reconnectDelay: number = 5000;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  
  constructor(url: string) {
    this.url = url;
  }
  
  /**
   * Connect to SSE endpoint.
   */
  connect(): void {
    if (this.eventSource) {
      return; // Already connected
    }
    
    try {
      this.eventSource = new EventSource(this.url);
      
      this.eventSource.onopen = () => {
        console.log(`[SSE] Connected to ${this.url}`);
        this.reconnectAttempts = 0;
      };
      
      this.eventSource.onerror = (error) => {
        console.error(`[SSE] Connection error:`, error);
        this.eventSource?.close();
        this.eventSource = null;
        
        // Attempt reconnection
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`[SSE] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);
          setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
          console.error(`[SSE] Max reconnection attempts reached`);
        }
      };
      
      // Set up generic message handler
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._dispatch('message', data);
        } catch (e) {
          console.error('[SSE] Failed to parse message:', e);
        }
      };
      
    } catch (error) {
      console.error('[SSE] Failed to create EventSource:', error);
    }
  }
  
  /**
   * Disconnect from SSE endpoint.
   */
  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      console.log(`[SSE] Disconnected from ${this.url}`);
    }
  }
  
  /**
   * Add event listener for specific event type.
   */
  addEventListener(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
      
      // Register with EventSource
      if (this.eventSource) {
        this.eventSource.addEventListener(eventType, (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            this._dispatch(eventType, data);
          } catch (e) {
            console.error(`[SSE] Failed to parse event ${eventType}:`, e);
          }
        });
      }
    }
    
    this.handlers.get(eventType)?.push(handler);
  }
  
  /**
   * Remove event listener.
   */
  removeEventListener(eventType: string, handler: EventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }
  
  /**
   * Dispatch event to registered handlers.
   */
  private _dispatch(eventType: string, data: any): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (e) {
          console.error(`[SSE] Handler error for ${eventType}:`, e);
        }
      });
    }
  }
}

/**
 * Create and auto-connect event client.
 */
export function createEventClient(url: string): EventClient {
  const client = new EventClient(url);
  client.connect();
  return client;
}
