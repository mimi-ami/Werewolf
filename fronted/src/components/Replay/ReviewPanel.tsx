import { useGameStore } from "../../store/gameStore";

export function ReviewPanel() {
  const reviews = useGameStore((s) => s.reviews);

  if (!reviews) return null;

  return (
    <div className="absolute inset-0 z-20 bg-[radial-gradient(circle_at_50%_10%,rgba(255,255,255,0.08),transparent_40%),rgba(5,10,20,0.92)] text-white overflow-auto p-8">
      <h2 className="text-3xl mb-6 tracking-wide">{"\u8d5b\u540e\u590d\u76d8"}</h2>

      {Object.entries(reviews).map(([pid, review]) => (
        <div
          key={pid}
          className="mb-6 rounded-2xl border border-white/10 bg-white/5 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.45)]"
        >
          <h3 className="text-xl mb-3 uppercase tracking-[0.25em] text-emerald-200/70">
            {pid}
          </h3>

          <p className="text-lg">
            <b>{"\u603b\u4f53\u7b56\u7565\uff1a"}</b> {review.overall_strategy}
          </p>
          {review.turning_point && (
            <p className="text-lg">
              <b>{"\u8f6c\u6298\u70b9\uff1a"}</b> {review.turning_point}
            </p>
          )}
          {review.biggest_mistake && (
            <p className="text-lg">
              <b>{"\u6700\u5927\u5931\u8bef\uff1a"}</b> {review.biggest_mistake}
            </p>
          )}
          {review.if_play_again && (
            <p className="text-lg">
              <b>{"\u5982\u679c\u518d\u73a9\u4e00\u6b21\uff1a"}</b> {review.if_play_again}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
