interface ProgressBarProps {
  progress: number;
  text: string;
  isVisible: boolean;
}

export function ProgressBar({ progress, text, isVisible }: ProgressBarProps) {
  if (!isVisible) return null;

  return (
    <div className="progress-container">
      <div className="progress-info">
        <span>{text}</span>
        <span>{progress}%</span>
      </div>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
