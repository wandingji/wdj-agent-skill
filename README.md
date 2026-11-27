# 万钉集 Agent Skills

## wandingji-cli

适用于可执行本机命令的 Agent。使用团队提供的万钉集 CLI 0.2.0 或以上版本和对应环境配置。

```sh
npx skills add wandingji/wdj-agent-skill --list
npx skills add wandingji/wdj-agent-skill --skill wandingji-cli
```

在本机执行 `wandingji auth login`，用自己的万钉集账号在网页确认企业及授权。CLI 将凭据保存到操作系统的凭证库。安装技能后，新建 Agent 会话即可提出业务查询。

技能在会话首次使用时检查本仓库的稳定发行版本。新版提示提供「现在更新」「稍后提醒」「跳过此版本」。用户确认后，更新器会校验固定 Git 提交中的技能内容。本机直接安装的 WorkBuddy 技能可原位升级，其他安装会得到可导入的 ZIP。

维护发行版本时，先提交 `skills/wandingji-cli` 的版本及内容，再更新 `releases/wandingji-cli.json`。该文件的 `version` 使用语义化版本号，`revision` 记录包含该版本技能的完整 Git 提交。WorkBuddy 市场独立提供发布审核，更新渠道应指向对应发行版本。
