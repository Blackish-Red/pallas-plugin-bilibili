<p align="center">
  <img src="./assets/brand.png" width="220" height="220" alt="明日方舟B站动态">
</p>

<h1 align="center">明日方舟B站动态 bilibili_dynamic</h1>

<p align="center">订阅明日方舟官方 B站动态，并推送到当前群。</p>

<p align="center">
  <img alt="社区插件" src="https://img.shields.io/badge/%E7%A4%BE%E5%8C%BA%E6%8F%92%E4%BB%B6-4B5563">
  <img alt="明日方舟" src="https://img.shields.io/badge/%E6%98%8E%E6%97%A5%E6%96%B9%E8%88%9F-4EA94B">
  <img alt="版本" src="https://img.shields.io/badge/%E7%89%88%E6%9C%AC-v0.1.4-2563EB">
</p>

## 安装方式

可在控制台插件商店安装，也可按社区插件目录放入 `local/plugins/bilibili_dynamic/`。

安装或更新后重启 Bot，使插件的命令和轮询任务完成注册。

## 怎么使用

- `牛牛订阅B站动态`：订阅当前群的明日方舟官方 B站动态。
- `牛牛关闭B站推送`：取消当前群的动态推送。

命令中的 `B` 不区分大小写。首次轮询只建立当前位置，不补发历史动态；后续新增图文、动态图片和可直接获取的 GIF 会随动态一并发送。

> 详细用法、限制条件和可用范围以帮助为主。

## 命令权限

| 功能 | 默认等级 |
| --- | --- |
| `牛牛订阅B站动态` | 群管/群主 |
| `牛牛关闭B站推送` | 群管/群主 |

命令权限可由控制台的命令权限配置覆盖。

## 配置项

> 可在控制台对应插件页中修改。

| 配置项 | 说明 |
| --- | --- |
| `enabled` | 是否启用 B站动态轮询。 |
| `poll_interval_sec` | 轮询间隔，范围为 60 至 3600 秒。 |
| `cookie` | 可选 B站登录 Cookie，用于降低风控概率。 |

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

- 固定关注明日方舟官方 UID `161775300`。
- 订阅状态与已投递动态游标按 Bot QQ 和群号持久化，避免重复推送。
- 遇到 B站风控响应时记录失败，不把未成功获取的动态写入投递游标。

## 相关链接

- [社区插件索引](https://github.com/PallasBot/Pallas-Bot-Community-Plugin-Index)
- [社区插件商店说明](https://github.com/PallasBot/Pallas-Bot/blob/dev/docs/guide/community-plugin-store.md)
