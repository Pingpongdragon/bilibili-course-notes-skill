# 发布与验证

## 目录结构

```text
dsh-class-notes/
├── index.html
├── .nojekyll
├── README.md
├── notes/
│   ├── 01-welcome.md
│   ├── 01-welcome.html
│   └── ...
└── assets/
    ├── 01/live-01.jpg
    ├── 01/chapter-1.jpg
    └── ...
```

- 图放在 `assets/<两位编号>/`；
- 笔记里的相对路径：`../assets/01/live-01.jpg`（从 `notes/` 出发）；
- `.nojekyll` 必须上传，避免 GitHub Pages 用 Jekyll 处理。

## GitHub 发布

1. 建仓库（public）或用 `publish_github.mjs --repo owner/repo`。
2. Contents API 逐文件 PUT；已有文件先取 `sha`。
3. 开启 Pages：`POST /repos/{owner}/{repo}/pages`，`source={branch:"main", path:"/"}`。
4. 请求构建：`POST /repos/{owner}/{repo}/pages/builds`。
5. 轮询页面：加 `?t=Date.now()`，确认 `HTTP 200`。

## 验证脚本思路

```js
const html = await fetch(`${base}/notes/01-welcome.html?t=${Date.now()}`)
const text = await html.text()
assert(html.status === 200)
assert(text.includes('<figure>'))
assert(text.includes('画面 00:33'))
const img = await fetch(`${base}/assets/01/live-01.jpg?t=${Date.now()}`)
assert(img.status === 200)
```

同时检查：

- `figures` 数量 = 实录块数 + 章节图数；
- 每页 `画面 ` 图注数 > 0；
- 图片字节数 > 20KB，尺寸 1280x410。

## 常见错误

| 现象 | 原因 | 处理 |
|---|---|---|
| 页面还是旧内容 | Pages 构建滞后/缓存 | 显式 POST builds；`?t=` 绕过缓存 |
| 图片 404 | 只传了 HTML 没传 assets | 逐文件上传 assets |
| `.nojekyll` 403 `Repository has been locked` | Pages 正在构建/仓库锁 | 等构建结束，再传一次 |
| `GET /pages` 404 | Pages 未开启 | POST `/pages` |
| 上传 409 | 缺 `sha` | 先 GET contents 取 sha |
| raw.githubusercontent 超时 | 网络 | 改用 api.github.com contents |

## 安全

- 不把 `bili_credential.json`、`GITHUB_TOKEN`、`.env` 放进仓库；
- 发布前 `grep -R "SESSDATA\|ghp_\|github_pat_"`；
- 笔记里的 cookie 一律删除。
