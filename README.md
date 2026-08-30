<p align="center">
  <img src="./assets/brand.png" width="220" height="220" alt="明日方舟B站动态">
</p>

<h1 align="center">明日方舟B站动态 bilibili_dynamic</h1>

<p align="center">订阅配置的 B站账号动态（默认明日方舟官方号），并推送到当前群。</p>

<p align="center">
  <img alt="社区插件" src="https://img.shields.io/badge/%E7%A4%BE%E5%8C%BA%E6%8F%92%E4%BB%B6-4B5563">
  <img alt="明日方舟" src="https://img.shields.io/badge/%E6%98%8E%E6%97%A5%E6%96%B9%E8%88%9F-4EA94B">
  <img alt="版本" src="https://img.shields.io/github/v/tag/Blackish-Red/pallas-plugin-bilibili?label=%E7%89%88%E6%9C%AC&color=2563EB">
</p>

## 安装方式

可在控制台插件商店安装，也可按社区插件目录放入 `local/plugins/bilibili_dynamic/`。

安装或更新后重启 Bot，使插件的命令和轮询任务完成注册。

## 怎么使用

- `牛牛订阅B站动态`：订阅当前群的 B站动态推送（账号列表见控制台 `uids` 配置）。
- `牛牛取消订阅B站动态`：取消当前群的动态推送。
- `牛牛B站添加UID 12345`：为当前群添加关注的 B站 UID。
- `牛牛B站删除UID 12345`：从当前群移除关注的 B站 UID。
- `牛牛B站查看UID`：查看当前群关注的 B站 UID（未设置时使用全局配置）。
- `牛牛测试B站推送`：检查 B站接口连通性，不发送动态、不改动投递游标。

命令中的 `B` 不区分大小写。首次轮询只建立当前位置，不补发历史动态；后续新增图文、动态图片和可直接获取的 GIF 会随动态一并发送。Bot 重启或取消订阅后重新订阅时，同样只对齐当前位置，不补发停机/关闭期间产生的动态，仅推送对齐之后新增的动态。

> 详细用法、限制条件和可用范围以帮助为主。

## 命令权限

| 功能 | 默认等级 |
| --- | --- |
| `牛牛订阅B站动态` | 群管/群主 |
| `牛牛取消订阅B站动态` | 群管/群主 |
| `牛牛B站添加UID` | 群管/群主 |
| `牛牛B站删除UID` | 群管/群主 |
| `牛牛B站查看UID` | 群管/群主 |
| `牛牛测试B站推送` | 超级用户 |

命令权限可由控制台的命令权限配置覆盖。

## 配置项

> 可在控制台对应插件页中修改。

| 配置项 | 说明 |
| --- | --- |
| `enabled` | 是否启用 B站动态轮询。 |
| `uids` | 要关注的 B站 UID 列表（JSON 数组），默认 `[161775300]`（明日方舟官方号）；留空时回退为官方号。 |
| `poll_interval_sec` | 轮询间隔，范围为 60 至 3600 秒。 |
| `cookie` | 可选 B站登录 Cookie，用于降低风控概率。 |

### 获取 B站 Cookie

1. 在浏览器登录 https://www.bilibili.com/，按 `F12` 打开开发者工具并进入“网络”。
2. 刷新页面，选择任意发往 `api.bilibili.com` 的请求，在“请求标头”中复制完整 `Cookie` 值。
3. 粘贴到控制台的「B站登录 Cookie」并保存；不要发送到群聊、日志、Issue 或提交到仓库。
4. 在测试群发送 `牛牛测试B站推送` 验证。若仍提示 `412`，Cookie 可能失效或账号触发风控，重新登录后换用新的 Cookie。

## 排障

| 现象 | 处理 |
| --- | --- |
| 订阅后没有推送 | 检查 `enabled`，并确认 Bot 重启后已加载插件。首次轮询不会补发历史动态。 |
| 日志出现 `-352`、`-412` 或 HTTP `412` | B站风控导致请求被拒绝；在控制台为 `cookie` 填写自己的有效登录 Cookie。 |
| 图片或 GIF 没有发送 | 检查 OneBot 适配器的媒体发送能力，以及目标动态的资源是否仍可访问。 |

Cookie 属于敏感信息，不应提交到仓库或发送到群里。

## 实现

源码位置：

- 插件入口：[`__init__.py`](./src/pallas_plugin_bilibili/__init__.py)
- 配置定义：[`config.py`](./src/pallas_plugin_bilibili/config.py)
- 命令处理：[`commands.py`](./src/pallas_plugin_bilibili/commands.py)
- B站请求：[`client.py`](./src/pallas_plugin_bilibili/client.py)
- 轮询任务：[`startup.py`](./src/pallas_plugin_bilibili/startup.py)

实现要点：

- 关注控制台 `uids` 配置的 B站账号列表，默认明日方舟官方 UID `161775300`。
- 订阅状态按 Bot QQ 和群号持久化；已投递动态游标按 UID 和群号共享，避免多 bot 重复推送。
- 遇到 B站风控响应时记录失败，不把未成功获取的动态写入投递游标。

## 相关链接

- [社区插件索引](https://github.com/PallasBot/Pallas-Bot-Community-Plugin-Index)
- [社区插件商店说明](https://github.com/PallasBot/Pallas-Bot/blob/dev/docs/guide/community-plugin-store.md)
