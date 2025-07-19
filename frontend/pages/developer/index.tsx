import { useEffect, useState } from "react";
import Router from "next/router";

export default function DeveloperPlatform() {
  const [isDev, setIsDev] = useState(false);

  useEffect(() => {
    fetch("/api/user/profile").then(res => res.json()).then(data => {
      if (data.role === "developer") setIsDev(true);
      else Router.replace("/403");
    });
  }, []);

  if (!isDev) return <div>加载中...</div>;

  return (
    <div>
      <h1>开发者平台</h1>
      <ul>
        <li><a href="/developer/api-keys">API密钥管理</a></li>
        <li><a href="/developer/webhooks">Webhook配置</a></li>
        <li><a href="/developer/platform-ext">平台扩展与测试</a></li>
        <li><a href="/developer/sdk">SDK下载</a></li>
        <li><a href="/developer/docs">API文档</a></li>
      </ul>
    </div>
  );
}