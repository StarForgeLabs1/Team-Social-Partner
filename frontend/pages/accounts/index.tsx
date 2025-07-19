import { useEffect, useState } from "react";

export default function AccountManager() {
  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({username: "", nickname: "", platform: ""});

  useEffect(() => {
    fetch("/api/users/").then(res => res.json()).then(setUsers);
  }, []);

  const addUser = () => {
    fetch("/api/users/", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(newUser)
    }).then(res => res.json()).then(user => {
      setUsers([...users, user]);
      setNewUser({username: "", nickname: "", platform: ""});
    });
  };

  const deleteUser = (id: number|string) => {
    fetch(`/api/users/${id}`, {method: "DELETE"})
      .then(() => setUsers(users.filter((u:any) => u.id !== id)));
  };

  return (
    <div>
      <h2>账号管理</h2>
      <input
        placeholder="用户名"
        value={newUser.username}
        onChange={e => setNewUser({...newUser, username: e.target.value})}
      />
      <input
        placeholder="昵称"
        value={newUser.nickname}
        onChange={e => setNewUser({...newUser, nickname: e.target.value})}
      />
      <input
        placeholder="平台"
        value={newUser.platform}
        onChange={e => setNewUser({...newUser, platform: e.target.value})}
      />
      <button onClick={addUser}>添加账号</button>
      <ul>
        {users.map((u: any) => (
          <li key={u.id}>
            {u.nickname} ({u.username}) - {u.platform}
            <button onClick={() => deleteUser(u.id)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}