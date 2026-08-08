# 明日方舟 B站动态推送

![明日方舟 B站动态推送](assets/brand.png)

订阅明日方舟官方 B站账号（UID `161775300`）的新增动态，并推送到群内。

## 安装

在 Pallas-Bot 控制台的社区插件页安装 `bilibili_dynamic`，或使用命令：

```bash
uv run pallas plugin community install bilibili_dynamic \
  --repo https://github.com/Blackish-Red/pallas-plugin-bilibili.git \
  --ref v0.1.4
```

安装或更新后重启 Bot，使插件的命令和轮询任务完成注册。

## 使用

群管理员发送下列命令即可订阅或取消订阅当前群：

| 命令 | 作用 |
| --- | --- |
| `牛牛订阅B站动态` | 订阅明日方舟官方 B站动态推送。 |
| `牛牛关闭B站推送` | 关闭当前群的动态推送。 |

命令中的 `B` 不区分大小写。首次轮询只建立当前位置，不补发历史动态；后续新增图文、动态图片和可直接获取的 GIF 会随动态一并发送。

## 配置

可在控制台插件配置中调整轮询间隔。B站可能因风控返回 `-352`、`-412` 或 HTTP `412`；遇到这类情况，请在插件配置的 `cookie` 中填写自己的有效 B站登录 Cookie。Cookie 属于敏感信息，不应提交到仓库或发送到群里。

## 兼容性

- Pallas-Bot `>= 4.1.31`
- OneBot v11
