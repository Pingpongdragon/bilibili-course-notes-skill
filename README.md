# B站课程图文笔记 Skill

把 B站 课程/讲座系列整理成带时间轴、720p 截图和连贯讲解的图文笔记，并发布到 GitHub Pages。

- 仓库：<https://github.com/Pingpongdragon/bilibili-course-notes-skill>
- 发布包：`bilibili-course-notes-skill.zip`（本仓库根目录）

## 安装

DSH 会从这些目录发现 skill（优先级从高到低）：

- `<项目根>/.dsh/skills/bilibili-course-notes/`
- `<项目根>/.agents/skills/bilibili-course-notes/`
- `<dshHome>/skills/bilibili-course-notes/`

把本目录放到任意一个位置即可。项目根是包含 `.git` 的最近祖先目录。

## 快速开始

```bash
pip install bilibili-api-python pillow imageio-ffmpeg
npm i marked

# 1. 完整字幕
python scripts/fetch_subtitles.py --bvids BV1...,BV1... --out .work/subs

# 2. 官方章节
python scripts/fetch_chapters.py --bvids BV1...,BV1... --out .work/chapters.json

# 3. 按 18~22 段写 01_timeline.json（见 references/note-template.md）

# 4. 抽 720p 帧（时间来自语义选帧）
python scripts/extract_frames.py --bvid BV1... --times 33,259,560 \
  --out-dir assets/01 --prefix live

# 5. Markdown -> HTML
node scripts/build_html.mjs --input notes/01.md --output notes/01.html

# 6. 发布
GITHUB_TOKEN=... node scripts/publish_github.mjs \
  --dir dsh-class-notes --repo owner/repo --branch main
```

## 这个 skill 解决的核心问题

1. **字幕截断**：`x/player/v2` 常只给前 14 分钟；用 `bilibili-api.get_subtitle` 拿完整轨道。
2. **截图不对应**：不要用章节起点；用完整字幕关键词匹配到“讲师正在讲这段”的时间。
3. **1080p 幻觉**：源常见 2240x720，B站最高 1280x410；先查 `dimension` 再承诺。
4. **文字跳跃**：每 5 分钟一个实录块，2~4 句承接叙述，而不是章节摘要。
5. **Markdown 挤成一段**：`⭐ 核心 / 🔧 实操 / ⚠️ 易错` 必须独立加粗段落。
6. **Pages 不更新**：显式 `POST /pages/builds`，用 `?t=` 验证。

## SkillHub / ClawHub

发布包已按 SkillHub 要求把元数据放在 `SKILL.md` frontmatter：

```yaml
slug: bilibili-course-notes
displayName: B站课程图文笔记
version: 1.0.0
summary: ...
license: MIT
```

上传前先打 zip：

```bash
zip -r bilibili-course-notes-skill.zip bilibili-course-notes
```

Web：<https://skillhub.cn/dashboard> → 发布技能 → 上传 zip。
CLI：

```bash
npm i -g @astron-team/skillhub
skillhub login --token sk_xxx
skillhub publish ./bilibili-course-notes --namespace global
```

ClawHub：

```bash
$env:CLAWHUB_REGISTRY = "https://skill.xfyun.cn"
clawhub login --token sk_xxx
clawhub publish ./bilibili-course-notes --slug my-team--bilibili-course-notes --name "B站课程图文笔记" --version 1.0.0
```

**不要把 cookie/token 打进 zip。**

## License

MIT
