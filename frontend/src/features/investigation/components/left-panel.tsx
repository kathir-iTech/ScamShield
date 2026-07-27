import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { StoredAnalysis } from '@/features/analysis/types';
import { Clock, FileText, ArrowRight, Trash2 } from 'lucide-react';

interface LeftPanelProps {
  currentId: string | null;
  history: StoredAnalysis[];
  onSelectHistory: (id: string) => void;
  onClearCurrent: () => void;
}

export function LeftPanel({ currentId, history, onSelectHistory, onClearCurrent }: LeftPanelProps) {
  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      {currentId && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-medium">Current Case</CardTitle>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClearCurrent} aria-label="Clear current case">
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <Badge variant="secondary" className="text-[10px]">Active</Badge>
          </CardContent>
        </Card>
      )}

      <Card className="flex-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium">Case History</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 pt-0">
          {history.length === 0 ? (
            <p className="py-4 text-center text-xs text-zinc-500">No previous cases</p>
          ) : (
            history.map((item) => (
              <button
                key={item.id}
                onClick={() => onSelectHistory(item.id)}
                className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-xs transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 ${
                  item.id === currentId ? 'bg-emerald-50 dark:bg-emerald-900/20' : ''
                }`}
              >
                <FileText className="h-3.5 w-3.5 shrink-0 text-zinc-400" />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-zinc-700 dark:text-zinc-300">
                    {item.inputText || item.inputFileName || `Case #${item.id}`}
                  </p>
                  <div className="flex items-center gap-2 text-[10px] text-zinc-400">
                    <Clock className="h-2.5 w-2.5" />
                    {new Date(item.timestamp).toLocaleDateString()}
                  </div>
                </div>
                <ArrowRight className="h-3 w-3 shrink-0 text-zinc-400" />
              </button>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
