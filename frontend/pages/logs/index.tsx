import { useEffect, useState } from "react";

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/api/logs/").then(res => res.json()).then(setLogs);
  }, []);

  const addLog = () => {
    fetch("/api/logs/", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message})
    }).then(res => res.json()).then(log => {
      setLogs([...logs, log]);
      setMessage("");
    });
  };

  return (
    <div>
      <h2>日志面板</h2>
      <input value={message} onChange={e => setMessage(e.target.value)} placeholder="日志内容" />
      <button onClick={addLog}>添加日志</button>
      <ul>
        {logs.map((log: any, idx: number) => (
          <li key={idx}>
            [{log.timestamp}] {log.message}
          </li>
        ))}
      </ul>
    </div>
  );
}