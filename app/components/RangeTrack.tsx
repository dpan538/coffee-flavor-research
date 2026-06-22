import type { CSSProperties } from "react";
import type { RangeScore } from "flavor-data";
import { rangeWidth, scoreToPercent } from "flavor-data";

type RangeTrackProps = {
  label: string;
  score: RangeScore;
};

export function RangeTrack({ label, score }: RangeTrackProps) {
  const style = {
    "--range-left": `${scoreToPercent(score.min)}%`,
    "--range-width": `${rangeWidth(score)}%`,
    "--typical-left": `${scoreToPercent(score.typical)}%`,
  } as CSSProperties;

  return (
    <div className="range-track" style={style}>
      <span>{label}</span>
      <span
        className="range-track__bar"
        role="img"
        aria-label={`${label}: min ${score.min}, typical ${score.typical}, max ${score.max}`}
      >
        <span className="range-track__range" />
        <span className="range-track__typical" />
      </span>
    </div>
  );
}
