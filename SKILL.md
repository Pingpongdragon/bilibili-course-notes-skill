---
name: bilibili-course-notes
slug: bilibili-course-notes
displayName: B站课程图文笔记
version: 1.0.0
summary: 把 B站 课程/讲座系列整理成带时间轴、720p 截图和连贯讲解的图文笔记，并发布到 GitHub Pages。
description: Turn a B站 lecture series into timestamped, illustrated study notes and a public GitHub Pages blog. Uses full subtitle timelines, semantic frame selection (not chapter-start slates), 720p native frames, and a repeatable publish/verify loop.
whenToUse: 当用户要把 B站 课程、讲座、系列视频整理成详细笔记/图文实录/学习博客，或要求“截图跟文字对应”“每段时间轴配图”“完整复现课程”时使用。
license: MIT
---

# B站课程 → 图文笔记 → Pages

把一整个 B站 课程系列做成“可复习、可检索、图文对应”的公开笔记。核心不是“总结一下”，而是：

- 按**官方章节 + 完整字幕时间轴**组织；
- 每 5 分钟左右一个**课堂实录**块：时间、720p 截图、2~4 句前后衔接的讲解；
- 截图必须**语义对应**这段文字，不能用章节起点的片头/黑屏；
- 产出 Markdown + HTML，发布到 GitHub Pages，并逐页验证 HTTP 200。

## 适用输入

- 一个 B站 UP 主的课程合集，或一组 BV 号；
- 用户提供课程链接/BV 号/合集页；
- 需要公开博客时，提供 GitHub 仓库或 token（`GITHUB_TOKEN`）。

## 前置

```bash
# Python 3.10+
pip install bilibili-api-python pillow
# 可选：自带 ffmpeg 的 wheel（不想装系统 ffmpeg 时）
pip install imageio-ffmpeg
# Node 18+，用于 marked 构建 HTML
npm i marked
```

B站 登录态：准备一个 cookie 文件（默认 `~/.dsh/bili-duty/bili_credential.json`），字段：

```json
{"sessdata":"...","bili_jct":"...","buvid3":"...","dedeuserid":"..."}
```

或用环境变量 `BILI_SESSDATA` / `BILI_JCT` / `BILI_BUVID3` / `BILI_DEDEUSERID`。**不要把 cookie 写进仓库或 skill 包。**

## 流程

### 0. 先确认分辨率，别承诺 1080p

拉 `x/web-interface/view` 看 `dimension`，再拉 `x/player/playurl?qn=80&fnval=4048&fourk=1` 看 `dash.video` 的 `id/width/height`。

- 很多课堂录屏源就是 `2240x720`，B站最高只给 `1280x410`；**没有 1080p 流**。
- 有 1080p 才用 `id=80`；没有就老实说“720p 原生帧”，不要用 480 快照冒充。
- `videoshot` 的 480x270 雪碧图只适合快速预览/选候选，不适合最终配图。

### 1. 抓完整字幕（关键坑）

不要只用 `x/player/v2` 的 `subtitle_url`：长视频经常只返回前 14 分钟。用 `bilibili-api` 的 `Video.get_subtitle(cid)`，它会给出完整轨道：

```bash
python scripts/fetch_subtitles.py \
  --bvids BV1pb8o6yE8f,BV1CQt365EzW \
  --out .work/subs
```

输出 `{bvid, body:[{from,to,content}]}`。每篇通常 2200~2600 段，覆盖到视频结尾。先检查 `body[-1].to` 是否接近时长；不够就是被截断。

### 2. 抓官方章节

```bash
python scripts/fetch_chapters.py \
  --bvids BV1pb8o6yE8f,BV1CQt365EzW \
  --out .work/chapters.json
```

取 `x/player/v2` 的 `data.view_points`（`from/to/content`）。B站 官方章节通常 3~5 个，是很好的粗时间轴；但**不要**拿章节 `from` 直接截帧——那里经常是片头/“设备坏了”/黑屏。

### 3. 切 18~22 段“课堂实录”

用完整字幕按话题边界切，每段约 5 分钟，不要机械等分。每段产出：

```json
{"time":0,"end":259,"title":"开场：能力被日用品化","text":"2~4 句连贯讲解，承接上一段"}
```

要求：

- 覆盖 `0` 到视频结尾，首尾相接；
- `title` 8~16 字；
- `text` 是**连贯叙述**，不是 bullet；落到具体例子、数字、演示；
- 只写字幕真实出现的内容，ASR 错词按上下文校正。

可让子代理读完整字幕 JSON 生成；提示词见 `references/note-template.md`。

### 4. 语义选帧（不要 chapter start）

对每个实录块/章节，在它的时间范围内找“讲师正在讲这段内容”的时间点：

1. 从该块标题 + 讲解里抽关键词：英文术语、数字、章节标题词；
2. 在完整字幕的 `[from,to]` 段里打分：`content` 命中关键词越多越好；
3. 取最高分段的 `from + 1s` 作为截帧时间；
4. 最高分为 0 时，用 `from + 12% * duration` 兜底，避开片头；
5. 截完**看一眼**：如果画面是片头/黑屏/无关幻灯片，换下一个候选段。

具体打分和坑见 `references/frame-selection.md`。

### 5. 抽 720p 帧

先下载 `dash.video` 里分辨率最高的 `baseUrl` 到本地 `.m4s`（Python `urllib`，带 `Referer`/`Origin`），再用 ffmpeg 本地抽帧：

```bash
python scripts/extract_frames.py \
  --bvid BV1pb8o6yE8f \
  --times 33,259,560 \
  --out-dir assets/01 \
  --prefix live
```

不要直接把 B站 CDN URL 丢给 ffmpeg：实测会 `Error opening input files: I/O error`，Python 下载到本地再抽最稳。

### 6. 写笔记

推荐结构（完整模板见 `references/note-template.md`）：

```markdown
# 课程名

> BV号 · 时长 · 来源

## 一句话结论

## 官方章节时间轴
| 时间 | 章节 |

## 课堂实录（按时间顺序）
### 00:00–04:19 · 标题
<figure>
<img src="../assets/01/live-01.jpg" alt="标题">
<figcaption>画面 00:33 · 标题</figcaption>
</figure>

连贯讲解……

## 章节详解
### 1. ...
**⭐ 核心：** ……
**🔧 实操：** ……
**⚠️ 易错：** ……

## 速查卡
```

格式硬规则：

- `⭐ 核心 / 🔧 实操 / ⚠️ 易错` 必须是**独立加粗段落**，前后空行。Markdown 单换行会合并成一段。
- 图注写**实际截帧时间**（`画面 00:33`），不要写章节起始时间。
- 代码/命令用 fenced code，别放表格里。
- 每张图下面最好有一句“画面解读”，说明这张图对应正文哪句话。

### 7. 构建 HTML

```bash
node scripts/build_html.mjs \
  --input notes/01-welcome.md \
  --output notes/01-welcome.html \
  --title "课程笔记"
```

CSS 至少包含 `figure img { width:100%; border-radius:12px; }`、`figcaption` 灰色小字、移动端 padding。

### 8. 发布 + 验证

```bash
export GITHUB_TOKEN=...
node scripts/publish_github.mjs \
  --dir dsh-class-notes \
  --repo owner/repo \
  --branch main
```

发布后：

- 用 cache-buster 逐页请求：`?t=Date.now()`；
- 检查每页 `HTTP 200`、`<figure>` 数量、`画面 ` 图注数量；
- 图片也要求 200，并抽查尺寸（`1280x410`）；
- GitHub Pages 不更新时，显式 `POST /repos/{owner}/{repo}/pages/builds`，再轮询。
- 若仓库被锁 / `.nojekyll` 403，先查 Pages 构建状态，别反复重传。

## 验收清单

- [ ] 9/9 页面 200，图片 200
- [ ] 每篇 18~22 个实录块（或按用户要求密度）
- [ ] 每块 1 张 720p 图，图注是实际截帧时间
- [ ] 截图与文字语义对应，没有片头/黑屏
- [ ] 核心/实操/易错独立成段
- [ ] 手机宽度下图片不溢出
- [ ] 没有 cookie/token 进入仓库

## 常见坑

1. **字幕截断**：`x/player/v2` 只给前 14 分钟；改用 `bilibili-api.get_subtitle`。
2. **1080p 不存在**：源 2240x720，playurl 最高 1280x410；先查 dimension 再承诺。
3. **章节起点是片头**：00:00 可能是“设备坏了”；用字幕关键词选帧。
4. **ffmpeg 直连 CDN 失败**：先 Python 下载 m4s，本地抽帧。
5. **Markdown 单换行不换段**：核心/实操/易错之间必须空行。
6. **Pages 缓存**：上传后显式 request build，并用 `?t=` 验证。
7. **旧笔记没有 `###` 小节**：图按段落比例插入 `## 讲了什么`，或先升级结构。
8. **截图信息不够**：一章一张不够；用 18~22 段实录，每段一张。

## 文件

- `scripts/fetch_subtitles.py` — 完整字幕
- `scripts/fetch_chapters.py` — 官方章节 + 分辨率
- `scripts/extract_frames.py` — 720p 抽帧
- `scripts/build_html.mjs` — Markdown → HTML
- `scripts/publish_github.mjs` — GitHub Contents API + Pages
- `references/note-template.md` — 笔记结构/子代理提示词
- `references/frame-selection.md` — 语义选帧细节
- `references/publishing.md` — 发布/验证/排错
