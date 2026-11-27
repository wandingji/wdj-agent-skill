---
name: wandingji-cli
display_name: 万钉集 CLI
display_name_en: Wandingji CLI
description: 用万钉集 CLI 查询当前企业的需求项目、需求整理单（RT 单）和需求物料，发现已授权的业务操作，或检查和更新万钉集 CLI 技能。
description_zh: 在 WorkBuddy 中调用本机万钉集 CLI，查询项目、需求单和物料。
description_en: Use the local Wandingji CLI in WorkBuddy to query projects, demand tasks, and materials.
examples_zh:
  - "查一下万钉集里有哪些需求项目"
  - "找出这张 RT 单的需求物料"
  - "检查万钉集 CLI 技能是否有新版本"
examples_en:
  - "List my Wandingji demand projects"
  - "Show the materials on this Wandingji demand task"
  - "Check the Wandingji CLI skill for updates"
version: "1.0.0"
author: 万钉集
---

# 万钉集 CLI

## 版本检查

会话首次调用此技能时，用 Bash 执行 `python3 "<技能目录>/scripts/update.py" check`。技能目录是本次加载的 `SKILL.md` 所在目录。用户明确要求检查时追加 `--force`。使用脚本返回的状态和版本号，网络异常或已是最新版时继续业务任务。
用户只要求查版本时，报告检查结果，无需发起业务查询。

返回 `update_available` 时，用 `AskUserQuestion` 展示当前版本和目标版本，提供单选「现在更新」「稍后提醒」「跳过此版本」。宿主无法弹出选择框时，在对话中列出同样的选项并等待回复。

- 现在更新时，只有收到用户确认才运行 `python3 "<技能目录>/scripts/update.py" update <确认的版本>`。脚本升级受支持的本机安装目录，或者生成已校验的 ZIP，交给 WorkBuddy 的「添加技能 → 上传技能」导入。按脚本结果告知用户，并在新会话使用新版。
- 稍后提醒时运行 `python3 "<技能目录>/scripts/update.py" later <目标版本>`，24 小时内不重复提示该版本。跳过时把 `later` 换为 `skip`，有下一个版本才提示。

## 查询业务

需要 Python 3.12 或以上、万钉集 CLI 0.2.0 或以上以及团队提供的可信环境配置。执行 `wandingji auth status --json` 检查本机授权。授权失效时请用户执行 `wandingji auth login` 并在网页确认企业。凭据由 CLI 写入系统凭证库。

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
