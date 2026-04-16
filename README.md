# 蚌院人物新闻

一个部署到 GitHub Pages 的小工具页。

## 功能

- 展示 `全部 / 青春榜样 / 国奖风采`
- 每条内容显示标题、发布时间、链接
- 标题和链接都支持一键复制
- 链接支持新页面打开
- 文章数据来自 `data/articles.json`
- 本地直接打开时会降级读取 `data/articles.js`

## 数据更新

本仓库通过 `scripts/update_data.py` 抓取微信公众号合集数据，再生成 `data/articles.json` 和 `data/articles.js`。

当前已接入：

- `青春榜样`

## 本地运行

```bash
python3 scripts/update_data.py
python3 -m http.server 8000
```

然后访问 `http://localhost:8000`。

## GitHub Pages

1. 把仓库推到 GitHub
2. 在仓库 `Settings -> Pages` 里选择从 `main` 分支部署
3. `Actions` 中可手动运行 `Update News Data`
4. 推送到 `main` 后会自动部署到 GitHub Pages，并读取最新的 `data/articles.json`

## PushPlus 提醒

如果希望每天北京时间 `09:07` 自动抓取时，有新文章就给你发微信提醒：

1. 在 GitHub 仓库里打开 `Settings -> Secrets and variables -> Actions`
2. 新建一个 secret，名字填 `PUSHPLUS_TOKEN`
3. 值填你自己的 PushPlus token

工作流会在每天北京时间 `09:07` 运行；只有检测到新文章时才发送提醒。GitHub Actions 定时任务在整点更容易出现延迟，避开整点更稳。

## 已接入栏目

当前抓取源已包含 `青春榜样` 和 `国奖风采` 两个合集。
