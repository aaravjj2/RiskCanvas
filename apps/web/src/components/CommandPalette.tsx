/**
 * CommandPalette.tsx (v4.4.0)
 *
 * Ctrl+K opens a command palette for quick navigation and search.
 * data-testids: cmdk-open, cmdk-input, cmdk-item-*
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

export interface CommandItem {
  id: string;
  label: string;
  description?: string;
  path?: string;
  action?: () => void;
}

const NAV_COMMANDS: CommandItem[] = [
  { id: 'dashboard', label: 'Go to Dashboard', description: 'Main analytics dashboard', path: '/' },
  { id: 'search', label: 'Go to Search', description: 'Global search across all data', path: '/search' },
  { id: 'activity', label: 'Go to Activity', description: 'Activity stream & presence', path: '/activity' },
  { id: 'devops', label: 'Go to DevOps', description: 'MR review, pipeline, artifacts', path: '/devops' },
  { id: 'governance', label: 'Go to Governance', description: 'Policy engine & eval suites', path: '/governance' },
  { id: 'sre', label: 'Go to SRE Playbooks', description: 'Incident triage & playbooks', path: '/sre' },
  { id: 'reports', label: 'Go to Reports', description: 'Report bundles & exports', path: '/reports-hub' },
  { id: 'jobs', label: 'Go to Jobs', description: 'Batch job queue', path: '/jobs' },
];

interface CommandPaletteProps {
  onSearchNavigate?: (query: string) => void;
}

export function CommandPalette({ onSearchNavigate }: CommandPaletteProps) {
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  // Ctrl+K opens the palette
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      setOpen(v => !v);
    }
    if (e.key === 'Escape') {
      setOpen(false);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (open) {
      setInputValue('');
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const filtered = NAV_COMMANDS.filter(cmd =>
    !inputValue.trim() ||
    cmd.label.toLowerCase().includes(inputValue.toLowerCase()) ||
    (cmd.description ?? '').toLowerCase().includes(inputValue.toLowerCase())
  );

  const handleSelect = (cmd: CommandItem) => {
    setOpen(false);
    if (cmd.path) {
      navigate(cmd.path);
    } else if (cmd.action) {
      cmd.action();
    }
  };

  const handleSubmit = () => {
    if (!inputValue.trim()) return;

    // If the input matches a command, run it
    if (filtered.length === 1) {
      handleSelect(filtered[0]);
      return;
    }

    // Otherwise route to search with prefilled text
    setOpen(false);
    if (onSearchNavigate) {
      onSearchNavigate(inputValue);
    } else {
      navigate(`/search?q=${encodeURIComponent(inputValue)}`);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      // Focus first item
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
      data-testid="cmdk-open"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={() => setOpen(false)}
      />

      {/* Palette panel */}
      <div className="relative w-full max-w-xl bg-card border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <span className="text-muted-foreground">⌘</span>
          <input
            ref={inputRef}
            data-testid="cmdk-input"
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-muted-foreground"
            placeholder="Search commands or type to search…"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleInputKeyDown}
          />
          <kbd className="text-xs text-muted-foreground border border-border rounded px-1">Esc</kbd>
        </div>

        {/* Commands list */}
        <ul className="py-2 max-h-[60vh] overflow-y-auto">
          {filtered.length === 0 && (
            <li className="px-4 py-3 text-sm text-muted-foreground">
              Press Enter to search for "{inputValue}"
            </li>
          )}
          {filtered.map((cmd) => (
            <li
              key={cmd.id}
              data-testid={`cmdk-item-${cmd.id}`}
              className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-accent transition-colors"
              onClick={() => handleSelect(cmd)}
            >
              <span className="text-sm font-medium flex-1">{cmd.label}</span>
              {cmd.description && (
                <span className="text-xs text-muted-foreground">{cmd.description}</span>
              )}
            </li>
          ))}
        </ul>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-border flex items-center gap-4 text-xs text-muted-foreground">
          <span><kbd className="bg-muted px-1 rounded">↵</kbd> select</span>
          <span><kbd className="bg-muted px-1 rounded">Esc</kbd> close</span>
          <span><kbd className="bg-muted px-1 rounded">Ctrl+K</kbd> toggle</span>
        </div>
      </div>
    </div>
  );
}

export default CommandPalette;
