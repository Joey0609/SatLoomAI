---
name: satloom-wiki-editor
description: 使用本仓库的本地 MediaWiki API、卫星百科编写规范、快照和差异工具，研究、起草、审查或编辑 sat.huijiwiki.com 词条。适用于卫星百科词条的新建、更新和校对任务。
metadata:
  short-description: 按规范编写并审查卫星百科词条
---

# SatLoomAI 卫星百科编辑技能

本技能用于为卫星百科（`sat.huijiwiki.com`）准备准确、符合站点规范且便于审阅的 Wikitext 修改。本仓库包含本地 MediaWiki API 服务、站点编写规则、页面快照和文本差异工具。

## 开始前阅读

- 阅读 [WIKI_EDIT_GUIDE.md](WIKI_EDIT_GUIDE.md)，其中合并了编辑流程、本地 API、快照命名方式和站点综合规则。遇到特定类型词条时，再查看 `编写规范/` 中对应的详细规范。
- 阅读 [server/README.md](server/README.md)，了解本地服务的安装、启动和 API 行为。

## 词条编辑流程

1. 确认用户指定的词条标题、修改范围和资料来源。事实优先采用一手资料和权威报道；区分已确认事实、估算值与不确定信息，并为对应内容保留来源。不得大段复制其他百科网站的内容。
2. 检查 `http://127.0.0.1:6280/health`。服务不可用时，按照 `server/README.md` 准备或启动服务；如遇环境或站点访问问题，应说明实际阻碍，不要声称编辑成功。
3. 使用 `GET /v1/pages/{title}` 读取现有词条。新建前确认返回的 `exists` 为 `false`。修改现有词条时保留无关内容和原有结构。
4. 按照 `WIKI_EDIT_GUIDE.md`，将读取到的原文和拟修改后的完整 Wikitext 分别保存为带时间戳的 `original` 与 `modified` 快照，放在 `cache/` 下。不要将凭证或其他秘密写入快照或回复。
5. 依据综合规则和对应词条类型规范起草内容。对照资料和现有词条检查名称、日期、单位、链接、模板、分类、引用及 Wikitext 语法。
6. 使用 `python wikitext_diff/aidiff.py <原文文件> <修改文件>` 生成并检查 HTML 差异报告。向用户概述主要新增、删除和更正；差异报告不能代替事实核查。
7. 向用户展示修改稿、资料来源和变更摘要。只有得到用户明确确认后，才能进行线上写入。确认新建时使用 `POST /v1/pages`，确认修改现有词条时使用 `PUT /v1/pages/{title}`，并填写简洁的编辑摘要。除非用户明确要求并确认，不要调用删除或文件上传接口。
8. 如实报告 API 结果。写入失败或结果不明确时，先重新读取页面确认状态，再决定是否重试；未经成功响应或页面状态核实，不要声称写入成功。

## API 与项目约定

- 本地服务地址为 `http://127.0.0.1:6280`；健康检查地址为 `/health`；交互式 API 文档地址为 `/docs`。
- 页面读取响应包含 `title`、`text` 和 `exists`。新建和修改请求包含 `text`、`summary`、`minor` 和 `bot` 字段；具体以服务端 Schema 和项目说明为准。
- 服务可能需要站点凭证，也可能受到 Cloudflare/WAF 限制。不要在技能文件中打印、复制或提交 `credentials.json`。
- `cache/` 已由 Git 忽略。快照和差异报告保留在本地，除非用户另行要求提供。
