import { useState, useCallback } from 'react';
import type { PanelId, WorkspaceState } from '@/features/investigation/types';

const DEFAULT_STATE: WorkspaceState = {
  leftPanelOpen: true,
  rightPanelOpen: true,
  centerPanelId: 'summary',
  leftWidth: 280,
  rightWidth: 320,
  splitDirection: 'vertical',
};

export function useWorkspaceState(initial?: Partial<WorkspaceState>) {
  const [state, setState] = useState<WorkspaceState>({ ...DEFAULT_STATE, ...initial });

  const toggleLeftPanel = useCallback(() => {
    setState((prev) => ({ ...prev, leftPanelOpen: !prev.leftPanelOpen }));
  }, []);

  const toggleRightPanel = useCallback(() => {
    setState((prev) => ({ ...prev, rightPanelOpen: !prev.rightPanelOpen }));
  }, []);

  const setCenterPanel = useCallback((id: PanelId) => {
    setState((prev) => ({ ...prev, centerPanelId: id }));
  }, []);

  const setLeftWidth = useCallback((w: number) => {
    setState((prev) => ({ ...prev, leftWidth: Math.max(220, Math.min(400, w)) }));
  }, []);

  const setRightWidth = useCallback((w: number) => {
    setState((prev) => ({ ...prev, rightWidth: Math.max(260, Math.min(420, w)) }));
  }, []);

  return { state, toggleLeftPanel, toggleRightPanel, setCenterPanel, setLeftWidth, setRightWidth };
}
