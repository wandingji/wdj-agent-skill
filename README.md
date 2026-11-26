# 万钉集 Agent Skills

## wandingji-cli

适用于可执行本机命令的 Agent。使用团队提供的万钉集 CLI 0.2.0 或以上版本和对应环境配置。

```sh
npx skills add wandingji/wdj-agent-skill --list
npx skills add wandingji/wdj-agent-skill --skill wandingji-cli
```

在本机执行 `wandingji auth login`，用自己的万钉集账号在网页确认企业及授权。CLI 将凭据保存到操作系统的凭证库。安装技能后，新建 Agent 会话即可提出业务查询。
