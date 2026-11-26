---
name: wandingji-cli
description: 通过万钉集 CLI 使用当前企业下已授权的业务工具。适用于查询需求项目、需求整理单（RT 单）、需求物料，以及发现当前账号可执行的万钉集业务操作。
---

# 万钉集 CLI

执行 `wandingji auth status --json` 检查本机授权。授权失效时请用户执行 `wandingji auth login` 并在网页确认企业。凭据由 CLI 写入系统凭证库。

| 用户要查 | 命令 |
| --- | --- |
| 需求项目 | `wandingji projects list --limit 5 --json` |
| 按名称筛选项目 | `wandingji projects list --name '项目名称' --json` |
| 需求单列表 | `wandingji demands list --limit 5 --json` |
| 按名称或单号搜索需求单 | `wandingji demands list --keyword '需求名称或单号' --json` |
| 某项目的需求单 | `wandingji demands list --project-id '项目ID' --json` |
| 某张需求单的物料 | `wandingji demands materials --task-no '需求单号' --json` |

按需求使用上一步返回的 `projectId`、`taskNo` 或 `taskId`。有多个合理目标时请用户选定。标识保持字符串。通过 shell 调用时正确引用来自用户和业务数据的参数。

其他操作用 `wandingji tools list` 查看服务端公布的名称和输入结构，再按结构调用 `wandingji tools call <名称> --arguments '<JSON 对象>'`。需要确认时把服务端给出的对象及动作展示给用户，依照返回的确认流程处理。操作状态未知时先查进度，避免重复写入。

解析单行 JSON 并检查退出码。列表成功时根据 `items`、`total`、`page`、`size` 和 `has_more` 表述范围。仅在用户要全量结果时逐页读取。权限错误、授权错误、连接错误和成功空列表分别处理。禁止将凭据放进对话、命令参数或输出。
