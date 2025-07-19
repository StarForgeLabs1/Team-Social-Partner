import { useEffect, useState } from "react";

export default function APIDocs() {
  const [docs, setDocs] = useState({docs: "", openapi: ""});
  useEffect(() => {
    fetch("/api/developer/docs").then(res => res.json()).then(setDocs);
  }, []);
  return (
    <div>
      <h2>API文档</h2>
      <p>
        <a href={docs.docs} target="_blank" rel="noopener">查看在线文档</a>
      </p>
      <p>
        <a href={docs.openapi} target="_blank" rel="noopener">下载 OpenAPI JSON</a>
      </p>
    </div>
  );
}