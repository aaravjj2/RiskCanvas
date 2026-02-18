/**
 * TestHarnessPage.tsx (v4.5.0)
 *
 * Deterministic UI unit test harness, replacing Vitest with Playwright MCP.
 * Runs checks over frontend logic (config, API constants, CommandPalette,
 * EventClient). Only accessible when DEMO_MODE or E2E_MODE is enabled.
 *
 * Route: /__harness
 * data-testids:
 *   harness-ready         – summary row (data-all-pass)
 *   harness-check-<slug>  – per-check row (data-pass, data-expected-hash, data-actual-hash)
 *   expected-hash-<slug>  – expected hash cell
 *   actual-hash-<slug>    – actual hash cell
 */

import { useMemo } from 'react';
import { getDemoHeaders, getAuthMode, getAuthHeaders } from '@/lib/config';
import { DEMO_PORTFOLIO, MOCK_DETERMINISM, MOCK_ANALYSIS } from '@/lib/api';
import { EventClient } from '@/lib/eventClient';
import { NAV_COMMANDS } from '@/components/CommandPalette';

// ── Deterministic djb2 hash (no external deps) ────────────────────────────────
function djb2(s: string): string {
  let h = 5381;
  for (let i = 0; i < s.length; i++) {
    h = ((h * 33) ^ s.charCodeAt(i)) >>> 0;
  }
  return h.toString(16).padStart(8, '0');
}

// ── Check runner ──────────────────────────────────────────────────────────────
interface HarnessCheck {
  slug: string;
  description: string;
  actual: string;
  expected: string;
  pass: boolean;
  actual_hash: string;
  expected_hash: string;
}

function runChecks(): HarnessCheck[] {
  const checks: HarnessCheck[] = [];

  function check(slug: string, description: string, actual: string, expected: string) {
    const pass = actual === expected;
    checks.push({
      slug,
      description,
      actual,
      expected,
      pass,
      actual_hash: djb2(actual),
      expected_hash: djb2(expected),
    });
  }

  // ── Config / Auth checks (temporarily enable demo mode) ──────────────────
  const prevMode = localStorage.getItem('RC_DEMO_MODE');
  localStorage.setItem('RC_DEMO_MODE', 'true');
  try {
    // Check 1: getDemoHeaders() shape
    const headers = getDemoHeaders();
    const headerStr = Object.keys(headers)
      .sort()
      .map((k) => `${k}:${headers[k]}`)
      .join('|');
    check(
      'demo-headers-shape',
      'getDemoHeaders() returns x-demo-user and x-demo-role',
      headerStr,
      'x-demo-role:admin|x-demo-user:demo-user',
    );

    // Check 2: getAuthMode() returns 'demo'
    check(
      'auth-mode-demo',
      'getAuthMode() returns "demo" when RC_DEMO_MODE=true',
      getAuthMode(),
      'demo',
    );

    // Check 3: getAuthHeaders() delegates to demo headers
    const authHeaders = getAuthHeaders();
    const authStr = Object.keys(authHeaders)
      .sort()
      .map((k) => `${k}:${authHeaders[k]}`)
      .join('|');
    check(
      'auth-headers-demo',
      'getAuthHeaders() includes demo headers in demo mode',
      authStr,
      'x-demo-role:admin|x-demo-user:demo-user',
    );
  } finally {
    if (prevMode === null) localStorage.removeItem('RC_DEMO_MODE');
    else localStorage.setItem('RC_DEMO_MODE', prevMode);
  }

  // ── CommandPalette checks ─────────────────────────────────────────────────
  check(
    'cmdk-command-count',
    'NAV_COMMANDS has 8 entries',
    String(NAV_COMMANDS.length),
    '8',
  );

  check(
    'cmdk-command-ids',
    'NAV_COMMANDS IDs are deterministic (in order)',
    NAV_COMMANDS.map((c) => c.id).join(','),
    'dashboard,search,activity,devops,governance,sre,reports,jobs',
  );

  check(
    'cmdk-all-have-paths',
    'Every NAV_COMMAND has a path',
    String(NAV_COMMANDS.every((c) => !!c.path)),
    'true',
  );

  // ── API mock constant checks ──────────────────────────────────────────────
  check(
    'api-demo-portfolio-len',
    'DEMO_PORTFOLIO has 2 positions',
    String(DEMO_PORTFOLIO.length),
    '2',
  );

  check(
    'api-demo-portfolio-symbols',
    'DEMO_PORTFOLIO symbols are AAPL,MSFT',
    DEMO_PORTFOLIO.map((a) => a.symbol).join(','),
    'AAPL,MSFT',
  );

  check(
    'api-mock-determinism-passed',
    'MOCK_DETERMINISM.passed is true',
    String(MOCK_DETERMINISM.passed),
    'true',
  );

  check(
    'api-mock-determinism-checks-len',
    'MOCK_DETERMINISM has 4 checks',
    String(MOCK_DETERMINISM.checks.length),
    '4',
  );

  check(
    'api-mock-analysis-request-id',
    'MOCK_ANALYSIS.request_id is "demo-001"',
    MOCK_ANALYSIS.request_id,
    'demo-001',
  );

  // ── EventClient checks ────────────────────────────────────────────────────
  let sseInstantiateResult = 'ok';
  try {
    const ec = new EventClient('http://localhost:8090/events/test');
    // disconnect() on unconnected client must not throw
    ec.disconnect();
  } catch (e) {
    sseInstantiateResult = `error:${e instanceof Error ? e.message : String(e)}`;
  }
  check(
    'sse-client-instantiate',
    'EventClient can be instantiated and disconnect() is a no-op',
    sseInstantiateResult,
    'ok',
  );

  let sseAddHandlerResult = 'ok';
  try {
    const ec = new EventClient('http://localhost:8090/events/test');
    let called = false;
    // addEventListener works before connect (handler stored without crashing)
    ec.addEventListener('test.event', () => { called = String(called) as unknown as boolean; });
    ec.disconnect();
    sseAddHandlerResult = 'ok';
  } catch (e) {
    sseAddHandlerResult = `error:${e instanceof Error ? e.message : String(e)}`;
  }
  check(
    'sse-client-add-handler',
    'EventClient.addEventListener can register handlers before connect',
    sseAddHandlerResult,
    'ok',
  );

  let sseRemoveHandlerResult = 'ok';
  try {
    const ec = new EventClient('http://localhost:8090/events/test');
    const fn = () => {};
    ec.addEventListener('test.event', fn);
    ec.removeEventListener('test.event', fn);
    ec.disconnect();
    sseRemoveHandlerResult = 'ok';
  } catch (e) {
    sseRemoveHandlerResult = `error:${e instanceof Error ? e.message : String(e)}`;
  }
  check(
    'sse-client-remove-handler',
    'EventClient.removeEventListener does not throw',
    sseRemoveHandlerResult,
    'ok',
  );

  return checks;
}

// ── Page component ────────────────────────────────────────────────────────────
export default function TestHarnessPage() {
  const checks = useMemo(() => runChecks(), []);
  const passed = checks.filter((c) => c.pass).length;
  const failed = checks.filter((c) => !c.pass).length;
  const allPass = failed === 0;

  return (
    <div data-testid="harness-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">UI Test Harness</h1>
      <p className="text-sm text-muted-foreground mb-4">
        Deterministic frontend unit checks (v4.5.0) — Playwright-only, replacing Vitest.
      </p>

      <div
        data-testid="harness-ready"
        data-all-pass={String(allPass)}
        data-passed={String(passed)}
        data-failed={String(failed)}
        className={`mb-6 px-4 py-2 rounded text-sm font-mono border ${
          allPass
            ? 'bg-green-50 text-green-700 border-green-300'
            : 'bg-red-50 text-red-700 border-red-300'
        }`}
      >
        {allPass
          ? `✅ All ${checks.length} checks passed`
          : `❌ ${failed} failed / ${passed} passed out of ${checks.length}`}
      </div>

      <table className="w-full text-sm border-collapse border border-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="text-left p-2 border-b font-medium">Slug</th>
            <th className="text-left p-2 border-b font-medium">Description</th>
            <th className="text-center p-2 border-b font-medium">Pass</th>
            <th className="text-left p-2 border-b font-mono text-xs">Expected Hash</th>
            <th className="text-left p-2 border-b font-mono text-xs">Actual Hash</th>
          </tr>
        </thead>
        <tbody>
          {checks.map((c) => (
            <tr
              key={c.slug}
              data-testid={`harness-check-${c.slug}`}
              data-pass={String(c.pass)}
              data-expected-hash={c.expected_hash}
              data-actual-hash={c.actual_hash}
              className={`border-b ${c.pass ? 'hover:bg-gray-50' : 'bg-red-50'}`}
            >
              <td className="p-2 font-mono text-xs">{c.slug}</td>
              <td className="p-2 text-xs">{c.description}</td>
              <td className="p-2 text-center">
                <span className={c.pass ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>
                  {c.pass ? '✅' : '❌'}
                </span>
              </td>
              <td
                className="p-2 font-mono text-xs text-gray-500"
                data-testid={`expected-hash-${c.slug}`}
              >
                {c.expected_hash}
              </td>
              <td
                className="p-2 font-mono text-xs"
                data-testid={`actual-hash-${c.slug}`}
              >
                {c.actual_hash}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
