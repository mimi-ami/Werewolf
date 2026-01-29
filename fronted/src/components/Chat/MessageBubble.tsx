import { useEffect, useState } from "react";

export function MessageBubble({ text }: { text: string }) {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    setDisplayed("");
    if (!text) return;
    let i = 0;
    const timer = setInterval(() => {
      setDisplayed((prev) => prev + text[i]);
      i++;
      if (i >= text.length) clearInterval(timer);
    }, 30);

    return () => clearInterval(timer);
  }, [text]);

  return <span>{displayed}</span>;
}
