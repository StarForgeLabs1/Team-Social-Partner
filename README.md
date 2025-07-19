# 多平台社交自动化系统（Supabase 版本）

## 快速部署

### 1. Supabase 控制台新建表
在 SQL Editor 执行 `supabase_schema.sql` 里的建表语句。

### 2. 配置环境变量
在 `.env` 或 Render 环境变量设置中填写（见 `.env.example`）。

### 3. 安装依赖并运行
```bash
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 5. 一键推送
直接推送本文件夹到 GitHub，新建仓库，连接 Render 一键部署即可。