# SatLoomAI Wiki Local Server

本目录提供一个本地 HTTP 服务（端口 **6280**），把 `https://sat.huijiwiki.com/` 的常用 Wiki 编辑/查询能力以 API 形式暴露出来。

> 注意：按你的要求，账号密码明文保存在 `credentials.json`。为了避免误提交，已在 `.gitignore` 中默认忽略。

## 目录结构

- `app/`：应用主体（分层结构：core/wiki/services/api/schemas）
- `run.py`：启动入口（支持被 API 关闭）
- `requirements.txt`：依赖
- `config.json`：站点与端口配置
- `credentials.json`：账号密码（明文）

## 创建 venv + 安装依赖（在 server/ 下执行）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

## 启动/停止

启动：

```powershell
.venv\Scripts\python.exe run.py
```

停止（向服务器发送 shutdown 请求，服务器自行关闭）：

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:6280/v1/admin/shutdown
```

启动后访问：
- 健康检查：`GET http://127.0.0.1:6280/health`
- OpenAPI：`GET http://127.0.0.1:6280/docs`

## 重要说明：站点 403（Cloudflare/WAF）

如果调用 `sat.huijiwiki.com` 时出现 403 且页面内容类似 "Just a moment..."，说明站点启用了 Cloudflare/WAF 的浏览器挑战。

这会导致 **Python/服务器侧** 无法直接访问 `api.php`（包括 `mwclient`），从而所有"创建/修改/删除/上传"等接口都会失败。

解决方式需要站点侧配合（推荐其一）：
- 在 Cloudflare/WAF 中 **按源 IP 放行** 你运行本服务的机器 IP。
- 或对路径 `/api.php`（以及可能的 `/w/api.php`）设置 **跳过挑战/降低安全级别** 的规则。
- 确认站点未禁止匿名访问 API 的基础查询（至少 `action=query&meta=siteinfo` 能 200）。

## API 概览（v1）

- 页面（词条）
  - `GET /v1/pages/{title}` 获取内容
  - `POST /v1/pages` 创建
  - `PUT /v1/pages/{title}` 修改
  - `DELETE /v1/pages/{title}` 删除
- 分类
  - `GET /v1/categories` 列出分类（分页）
  - `GET /v1/categories/{name}/members` 列出分类成员（分页）
- 文件
  - `GET /v1/files/{filename}/info` 文件信息
  - `GET /v1/files/{filename}/usage` 文件使用情况
  - `GET /v1/files/{filename}/download` 下载（流式）
  - `POST /v1/files/upload` 上传（multipart）
- 管理
  - `POST /v1/admin/shutdown` 关闭服务
