import { useEffect, useState } from "react";

export default function APIKeyManager() {
  const [keys, setKeys] = useState([]);
  const [newKey, setNewKey] = useState("");

  useEffect(() => {
    fetch("/api/developer/api-keys").then(res => res.json()).then(setKeys);
  }, []);

  const createKey = () => {
    fetch("/api/developer/api-keys", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name: newKey})
    }).then(res => res.json()).then(k => {
      setKeys([...keys, k]);
      setNewKey("");
    });
  };

  const deleteKey = (id: string) => {
    fetch(`/api/developer/api-keys/${id}`, {method: "DELETE"})
      .then(() => setKeys(keys.filter((k:any) => k.id !== id)));
  };

  return (
    <div>
      <h2>API密钥管理</h2>
      <input value={newKey} onChange={e => setNewKey(e.target.value)} placeholder="新密钥备注"/>
      <button onClick={createKey}>创建密钥</button>
      <ul>
        {keys.map((k: any) => (
          <li key={k.id}>
            {k.name} - {k.value}
            <button onClick={() => deleteKey(k.id)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}