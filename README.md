# SatLoomAI

**AI 辅助的卫星百科（sat.huijiwiki.com）词条编辑工具链和 MCP 服务器。**

SatLoomAI 将 AI Harness 代理与本地 MediaWiki API 服务结合在一起，实现自动化、可审查的 Wiki 词条编辑工作流。

---

## 项目结构

```
├── server/                  # 本地 Wiki API 服务（FastAPI）
│   ├── app/                 #   分层应用（core → wiki → services → api → schemas）
│   ├── run.py               #   服务启动入口
│   ├── config.json          #   站点与端口配置
│   ├── credentials.json     #   登录凭证（已 gitignore）
│   └── requirements.txt     #   依赖
├── cache/                   # 编辑前/后的 Wikitext 快照缓存
├── wikitext_diff/           # Wikitext 差异对比工具
│   └── aidiff.py            #   生成 HTML 差异报告并打开浏览器
├── 编写规范/                 # 26 份卫星百科 Wikitext 规范文件
├── WIKI_EDIT_GUIDE.md       # AI 编辑操作流程标准
├── Edit_Rules.md            # 综合编辑规则（从编写规范整理）
└── README.md                # 本文件
```

---

## 功能

| 功能块 | 说明 |
|---|---|
| **Wiki API 代理** | 通过本地 HTTP 服务（:6280）封装 MediaWiki API，提供页面 CRUD、分类查询、文件上传等 REST 接口 |
| **Cloudflare 绕过** | 内置 cloudscraper，自动处理 Cloudflare JS Challenge |
| **AI 编排工作流** | 定义了一套标准流程：数据获取 → 内容生成 → 差异对比 → 用户确认 → 推送编辑 |
| **编辑规则引擎** | 整合了 26 份 wiki 规范文件为统一的编辑规则，AI 据此生成合规内容 |
| **差异审查** | aidiff.py 生成 HTML 版差异报告，在修改推送到 Wiki 前可视化审查 |
| **缓存快照** | 每次编辑自动保存 original / modified 双份快照到 cache/，支持审计回溯 |

---

## 使用方法

这套工具链设计为在 AI Harness 中运行。基本流程如下：

### 1. 启动本地 API 服务

在 `server/` 目录下激活虚拟环境并启动：

```powershell
# 首次：创建虚拟环境并安装依赖
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 启动服务
.venv\Scripts\python.exe run.py
```

服务启动后，访问 `http://127.0.0.1:6280/health` 验证，查看 API 文档请访问 `http://127.0.0.1:6280/docs`。

### 2. 在 AI Harness 中发起编辑任务

在 AI Harness 对话中向 AI（Brother Whale）提出编辑请求，例如：

> "帮我把卫星百科中「凝视号」的词条更新一下，数据来源是 https://example.com/ning-shi-hao"（其实也可以把该文件作为一个SKILL）。

### 3. AI 自动执行编辑流程

AI 会按照 `WIKI_EDIT_GUIDE.md` 中的标准流程执行：

1. **前置检查** — 检查本地服务是否运行，必要时自动启动
2. **数据获取** — 通过 Firecrawl 抓取外部网页内容
3. **拉取原词条** — `GET /v1/pages/{title}` 获取现有 Wiki 内容
4. **缓存原版** — 保存到 `cache/{词条名}_{时间戳}_original.wikitext`
5. **生成修改版** — 结合外部数据与编辑规则生成新内容
6. **差异对比** — 使用 aidiff.py 生成 HTML 差异报告
7. **展示变更 + 等待确认** — 向用户展示增删改摘要
8. **推送编辑** — 用户确认后，`PUT /v1/pages/{title}` 将修改写入 Wiki

### 4. 审查并确认

AI 会向您展示变更摘要，您可以打开 aidiff 生成的 HTML 文件逐行审阅。确认后，AI 执行推送。

---

## API 概览

| 端点 | 说明 |
|---|---|
| `GET /health` | 健康检查 |
| `GET /v1/pages/{title}` | 获取词条内容 |
| `POST /v1/pages` | 创建新词条 |
| `PUT /v1/pages/{title}` | 修改词条 |
| `DELETE /v1/pages/{title}` | 删除词条 |
| `GET /v1/categories` | 列出分类 |
| `GET /v1/categories/{name}/members` | 分类成员列表 |
| `GET /v1/files/{filename}/info` | 文件信息 |
| `POST /v1/files/upload` | 上传文件 |
| `POST /v1/admin/shutdown` | 关闭服务 |

详细文档见 `server/README.md`。
