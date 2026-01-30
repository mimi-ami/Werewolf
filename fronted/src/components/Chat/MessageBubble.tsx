import { useEffect, useMemo, useState } from "react";

export function MessageBubble({
  text,
  instant = false,
}: {
  text: string;
  instant?: boolean;
}) {
  const [displayed, setDisplayed] = useState("");
  const safeText =
    typeof text === "string" ? text.replace(/undefined/gi, "") : "";
  const chars = useMemo(() => Array.from(safeText || ""), [safeText]);

  useEffect(() => {
    if (instant) {
      setDisplayed(safeText);
      return;
    }
    setDisplayed("");
    if (!safeText) return;
    let i = 0;
    const timer = setInterval(() => {
      if (i >= chars.length) {
        clearInterval(timer);
        return;
      }
      setDisplayed((prev) => prev + chars[i]);
      i++;
    }, 30);

    return () => clearInterval(timer);
  }, [safeText, instant, chars]);

  return <span>{instant ? safeText : displayed}</span>;
}
