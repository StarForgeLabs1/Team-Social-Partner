import { useState } from "react";

export default function PlatformExt() {
  const [result, setResult] = useState("");

  const testPublish = async () => {
    setResult("测试中...");
    const res = await fetch("/api/developer/test-publish", {method: "POST"});
    const data = await res.json();
    setResult(JSON.stringify(data));
  };

  return (
    <div>
      <h2>平台扩展与测试</h2>
      <button onClick={testPublish}>测试快速发布到所有平台</button>
      <div>
        <strong>测试结果：</strong>
        <pre>{result}</pre>
      </div>
    </div>
  );
}