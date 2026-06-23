import { marked } from "marked";
import { useEffect, useState } from "react";
import { fetchEval } from "../api";

export function EvalView() {
  const [html, setHtml] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchEval()
      .then((md) => {
        if (active) setHtml(marked.parse(md, { async: false }) as string);
      })
      .catch((e: Error) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, []);

  if (error) return <div className="error">{error}</div>;
  return (
    <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />
  );
}
