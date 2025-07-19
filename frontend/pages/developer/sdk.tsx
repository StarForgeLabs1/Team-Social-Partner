import { useEffect, useState } from "react";

export default function SDKDownload() {
  const [sdks, setSdks] = useState([]);
  useEffect(() => {
    fetch("/api/developer/sdks").then(res => res.json()).then(setSdks);
  }, []);
  return (
    <div>
      <h2>SDK下载</h2>
      <ul>
        {sdks.map((sdk: any) => (
          <li key={sdk.lang}>
            {sdk.lang} <a href={sdk.url} target="_blank" rel="noopener">下载</a>
          </li>
        ))}
      </ul>
    </div>
  );
}