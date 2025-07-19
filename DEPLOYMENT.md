# 多平台社交自动化系统 Supabase 部署步骤

## 1. 环境准备
- Python 3.8+、Node.js 16+
- Supabase 账号与项目
- 配置 .env 参考 .env.example

## 2. Supabase 数据库建表
- 在 Supabase SQL Editor 执行 `supabase_schema.sql` 内容

## 3. 本地测试
- pip install -r requirements.txt
- cd frontend && npm install
- uvicorn backend.main:app --host 0.0.0.0 --port 8000
- cd frontend && npm run dev

## 4. Render 或云服务器部署
- 推送代码到GitHub
- Render自动识别render.yaml并部署
- 验证服务正常运行