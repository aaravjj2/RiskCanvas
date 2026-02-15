import { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { Asset, AnalysisResult, DeterminismResult } from './types';
import { DEMO_PORTFOLIO, analyzePortfolio, checkDeterminism } from './api';

interface AppState {
  // Portfolio state
  portfolio: Asset[];
  setPortfolio: (assets: Asset[]) => void;
  loadFixture: () => void;
  
  // Analysis state
  analysis: AnalysisResult | null;
  runAnalysis: () => Promise<void>;
  
  // Determinism state
  determinism: DeterminismResult | null;
  runDeterminismCheck: () => Promise<void>;
  
  // UI state
  loading: boolean;
  error: string | null;
  setError: (error: string | null) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [portfolio, setPortfolio] = useState<Asset[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [determinism, setDeterminism] = useState<DeterminismResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFixture = useCallback(() => {
    setPortfolio(DEMO_PORTFOLIO);
    setAnalysis(null);
    setDeterminism(null);
    setError(null);
  }, []);

  const runAnalysis = useCallback(async () => {
    if (portfolio.length === 0) {
      setError('Load a portfolio first.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await analyzePortfolio(portfolio);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [portfolio]);

  const runDeterminismCheck = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await checkDeterminism();
      setDeterminism(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Determinism check failed');
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <AppContext.Provider
      value={{
        portfolio,
        setPortfolio,
        loadFixture,
        analysis,
        runAnalysis,
        determinism,
        runDeterminismCheck,
        loading,
        error,
        setError,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}
