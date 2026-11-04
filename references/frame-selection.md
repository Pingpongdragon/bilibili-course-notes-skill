# 语义选帧

目标：截图要对应这一段文字，而不是“章节开始的那一帧”。

## 为什么不能用章节起点

B站 官方章节的 `from` 经常落在：

- 片头/设备调试（例如 00:00 的“设备坏了”）；
- 章节标题黑屏；
- 上一段内容的残留。

结果就是“文字讲能力日用品化，图是设备坏了”。

## 算法

对每个实录块/章节 `[from, to]`：

1. 抽关键词：
   - 英文术语/数字：`[A-Za-z][A-Za-z0-9+.#/-]{1,}`、`\d{3,4}`；
   - 章节标题按标点切词，保留长度 ≥2 的中文词；
   - 去掉 `the/and/for/this/that/...` 这类停用词。
2. 在完整字幕里筛 `from <= segment.from <= to`。
3. 对每段 `content.lower()` 统计关键词命中数。
4. 取命中数最高的段，`target = segment.from + 1`。
5. 最高分为 0：`target = from + max(20, 0.12 * (to-from))`。
6. 抽帧后**人工看一眼**；如果还是片头/黑屏，换第二高分候选段。

## 实例

| 课程 | 章节 | 选中时间 | 画面 |
|---|---|---|---|
| 01 | 课程简介 | 00:33 | “四次把昂贵能力变成日用品：PC 1975 Altair / 互联网 / iPhone / ChatGPT” |
| 02 | Prompt Engineering | 01:59 | “system prompt 之后……” |
| 06 | 需求工程 | 30:22 | “让 GPT 起一个 sub agent……” |
| 09 | 需求 | 10:53 | “Agent Harness：需求 / 上节课 150 行的 Mini-Agent” |

01 章节起点是 00:00，但那张是“设备坏了”；关键词 `1975/Altair/ChatGPT/PC` 把它推到 00:33 的正确幻灯片。

## 720p 抽帧

1. `playurl?qn=80&fnval=4048&fourk=1` 取 `dash.video` 中 `width*height` 最大者。
2. Python 带 `Referer` / `Origin` 下载 `.m4s` 到本地。
3. `ffmpeg -ss <t> -i <local.m4s> -frames:v 1 -q:v 2 out.jpg`。
4. 不要直接把 CDN URL 给 ffmpeg：常见 `Error opening input files: I/O error`。

## 分辨率预期

- 先看 `view.dimension`；课堂录屏常见 `2240x720`。
- B站 对 720p 源通常只给 `1280x410`；`id=80`/1080p 可能不存在。
- 不要用 480x270 的 `videoshot` 雪碧图冒充 720p；它只适合预览。
- 如果用户要 1080p，先说明源没有，再给 720p 方案。

## 验收

- 每张图 `1280x410`（或该视频实际最高分辨率）。
- 图注写实际时间：`画面 00:33`。
- 抽查 3 张：是否与所在段落文字对应；是否有片头/黑屏。
