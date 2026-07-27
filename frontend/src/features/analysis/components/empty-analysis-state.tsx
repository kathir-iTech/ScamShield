import { useNavigate } from 'react-router-dom';
import { EmptyPanel } from '@/components/ui/empty-panel';
import { Button } from '@/components/ui/button';

export function EmptyAnalysisState() {
  const navigate = useNavigate();

  return (
    <EmptyPanel
      title="No analysis results"
      description="Submit a message or image for analysis to see results here."
      action={
        <div className="flex gap-3">
          <Button variant="default" onClick={() => navigate('/analyze/text')}>
            Analyze Text
          </Button>
          <Button variant="outline" onClick={() => navigate('/analyze/image')}>
            Analyze Image
          </Button>
        </div>
      }
    />
  );
}
