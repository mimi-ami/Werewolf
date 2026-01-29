import { useEffect, useState } from "react";

export function MessageBubble({ text }: { text: string }) {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    setDisplayed("");
    if (!text) return;
    let i = 0;
    const timer = setInterval(() => {
      if (i >= text.length) {
        clearInterval(timer);
        return;
      }
      setDisplayed((prev) => prev + text.charAt(i));
      i++;
    }, 30);

    return () => clearInterval(timer);
  }, [text]);

  return <span>{displayed}</span>;
}
