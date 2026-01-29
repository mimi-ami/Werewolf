import { useGameStore } from "../../store/gameStore";

export function ReviewPanel() {
  const reviews = useGameStore((s) => s.reviews);

  if (!reviews) return null;

  return (
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_10%,rgba(255,255,255,0.08),transparent_40%),rgba(5,10,20,0.92)] text-white overflow-auto p-8">
      <h2 className="text-2xl mb-6 tracking-wide">赛后复盘</h2>

      {Object.entries(reviews).map(([pid, review]) => (
        <div
          key={pid}
          className="mb-6 rounded-2xl border border-white/10 bg-white/5 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.45)]"
        >
          <h3 className="text-lg mb-3 uppercase tracking-[0.25em] text-emerald-200/70">
            {pid}
          </h3>

          <p>
            <b>总体策略：</b> {review.overall_strategy}
          </p>
          {review.turning_point && (
            <p>
              <b>转折点：</b> {review.turning_point}
            </p>
          )}
          {review.biggest_mistake && (
            <p>
              <b>最大失误：</b> {review.biggest_mistake}
            </p>
          )}
          {review.if_play_again && (
            <p>
              <b>如果再玩一次：</b> {review.if_play_again}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
