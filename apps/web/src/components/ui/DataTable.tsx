/**
 * DataTable.tsx (v4.75.0 - Wave 33)
 *
 * Reusable sortable + selectable table component.
 * Deterministic stable sort (no external libs).
 *
 * data-testids:
 *   data-table, data-table-header, data-table-sort-{key},
 *   data-table-row-{i}, data-table-select-{i},
 *   data-table-bulk-bar, data-table-bulk-action,
 *   data-table-empty, data-table-copy-cell
 */
import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";

export interface ColumnDef<T> {
  key: string;
  header: string;
  /** Render cell content. Defaults to String(row[key]) */
  render?: (row: T, i: number) => React.ReactNode;
  /** Whether this column is sortable */
  sortable?: boolean;
  /** Tailwind width class e.g. "w-32" */
  width?: string;
}

interface DataTableProps<T extends Record<string, unknown>> {
  columns: ColumnDef<T>[];
  data: T[];
  /** Unique row key field. Falls back to index. */
  rowKey?: keyof T;
  selectable?: boolean;
  onSelectionChange?: (selected: T[]) => void;
  bulkActionLabel?: string;
  onBulkAction?: (selected: T[]) => void;
  emptyLabel?: string;
  className?: string;
  "data-testid"?: string;
}

type SortDir = "asc" | "desc" | null;

/** Deterministic stable sort — preserves original index on equal keys */
function stableSort<T>(arr: T[], key: string, dir: SortDir): T[] {
  if (!dir) return arr;
  return [...arr].sort((a, b) => {
    const av = String((a as any)[key] ?? "");
    const bv = String((b as any)[key] ?? "");
    const cmp = av.localeCompare(bv, undefined, { numeric: true, sensitivity: "base" });
    return dir === "asc" ? cmp : -cmp;
  });
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  rowKey,
  selectable = false,
  onSelectionChange,
  bulkActionLabel = "Export selected",
  onBulkAction,
  emptyLabel = "No records",
  className,
  "data-testid": testId = "data-table",
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);
  const [selectedIdx, setSelectedIdx] = useState<Set<number>>(new Set());

  const toggleSort = useCallback((key: string) => {
    setSortKey(prev => {
      if (prev !== key) { setSortDir("asc"); return key; }
      setSortDir(d => d === "asc" ? "desc" : d === "desc" ? null : "asc");
      return key;
    });
  }, []);

  const sorted = sortKey && sortDir ? stableSort(data, sortKey, sortDir) : data;

  const toggleRow = useCallback((i: number) => {
    setSelectedIdx(prev => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i); else next.add(i);
      const selected = [...next].map(idx => sorted[idx]);
      onSelectionChange?.(selected);
      return next;
    });
  }, [sorted, onSelectionChange]);

  const toggleAll = useCallback(() => {
    setSelectedIdx(prev => {
      if (prev.size === sorted.length) {
        onSelectionChange?.([]);
        return new Set();
      }
      const all = new Set(sorted.map((_, i) => i));
      onSelectionChange?.(sorted);
      return all;
    });
  }, [sorted, onSelectionChange]);

  const selectedItems = [...selectedIdx].map(i => sorted[i]);

  return (
    <div data-testid={testId} className={cn("flex flex-col gap-2", className)}>
      {/* Bulk action bar */}
      {selectable && selectedIdx.size > 0 && (
        <div
          data-testid="data-table-bulk-bar"
          className="flex items-center gap-3 px-3 py-2 bg-primary/10 rounded-md text-sm"
        >
          <span>{selectedIdx.size} row(s) selected</span>
          {onBulkAction && (
            <button
              data-testid="data-table-bulk-action"
              onClick={() => onBulkAction(selectedItems)}
              className="px-3 py-1 text-xs bg-primary text-primary-foreground rounded-md"
            >
              {bulkActionLabel}
            </button>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-auto rounded-md border border-border">
        <table className="w-full text-sm">
          <thead data-testid="data-table-header" className="sticky top-0 bg-muted/80 backdrop-blur-sm">
            <tr>
              {selectable && (
                <th className="w-8 px-3 py-2 text-left">
                  <input
                    type="checkbox"
                    data-testid="data-table-select-all"
                    checked={selectedIdx.size === sorted.length && sorted.length > 0}
                    onChange={toggleAll}
                    aria-label="Select all"
                  />
                </th>
              )}
              {columns.map(col => (
                <th
                  key={col.key}
                  className={cn(
                    "px-3 py-2 text-left font-semibold text-xs uppercase tracking-wide text-muted-foreground whitespace-nowrap",
                    col.width
                  )}
                >
                  {col.sortable ? (
                    <button
                      data-testid={`data-table-sort-${col.key}`}
                      onClick={() => toggleSort(col.key)}
                      className="flex items-center gap-1 hover:text-foreground transition-colors"
                    >
                      {col.header}
                      <span className="text-muted-foreground/60 tabular-nums w-3">
                        {sortKey === col.key ? (sortDir === "asc" ? "↑" : sortDir === "desc" ? "↓" : "") : ""}
                      </span>
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 && (
              <tr>
                <td
                  data-testid="data-table-empty"
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  className="px-3 py-12 text-center text-muted-foreground text-sm"
                >
                  {emptyLabel}
                </td>
              </tr>
            )}
            {sorted.map((row, i) => {
              const key = rowKey ? String(row[rowKey]) : String(i);
              const isSelected = selectedIdx.has(i);
              return (
                <tr
                  key={key}
                  data-testid={`data-table-row-${i}`}
                  className={cn(
                    "border-t border-border transition-colors",
                    isSelected ? "bg-primary/5" : "hover:bg-muted/40"
                  )}
                >
                  {selectable && (
                    <td className="w-8 px-3 py-2">
                      <input
                        type="checkbox"
                        data-testid={`data-table-select-${i}`}
                        checked={isSelected}
                        onChange={() => toggleRow(i)}
                        aria-label={`Select row ${i}`}
                      />
                    </td>
                  )}
                  {columns.map(col => (
                    <td
                      key={col.key}
                      className={cn("px-3 py-2 align-top tabular-nums", col.width)}
                    >
                      {col.render
                        ? col.render(row, i)
                        : String(row[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataTable;
