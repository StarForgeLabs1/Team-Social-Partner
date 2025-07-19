import { useEffect, useState } from "react";

export default function WebhookManager() {
  const [webhooks, setWebhooks] = useState([]);
  const [url, setUrl] = useState("");

  useEffect(() => {
    fetch("/api/developer/webhooks").then(res => res.json()).then(setWebhooks);
  }, []);

  const addWebhook = () => {
    fetch("/api/developer/webhooks", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url})
    }).then(res => res.json()).then(w => {
      setWebhooks([...webhooks, w]);
      setUrl("");
    });
  };

  const deleteWebhook = (id: string) => {
    fetch(`/api/developer/webhooks/${id}`, {method: "DELETE"})
      .then(() => setWebhooks(webhooks.filter((w:any) => w.id !== id)));
  };

  return (
    <div>
      <h2>Webhook配置</h2>
      <input value={url} onChange={e => setUrl(e.target.value)} placeholder="Webhook URL"/>
      <button onClick={addWebhook}>添加Webhook</button>
      <ul>
        {webhooks.map((w: any) => (
          <li key={w.id}>{w.url}
            <button onClick={() => deleteWebhook(w.id)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}