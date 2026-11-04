#!/usr/bin/env node
// Markdown -> standalone HTML for course notes.
// Usage:
//   node build_html.mjs --input notes/01.md --output notes/01.html --title "课程笔记"
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

async function loadMarked() {
  try {
    return (await import('marked')).marked
  } catch {}
  const here = path.dirname(new URL(import.meta.url).pathname)
  const candidates = [
    path.join(process.cwd(), 'node_modules/marked/lib/marked.esm.js'),
    path.join(here, '..', 'node_modules/marked/lib/marked.esm.js'),
  ]
  for (const p of candidates) {
    try {
      return (await import(pathToFileURL(p).href)).marked
    } catch {}
  }
  throw new Error('marked not found: run `npm i marked` in this skill or your project')
}
const marked = await loadMarked()

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, cur, i, arr) => {
    if (cur.startsWith('--')) acc.push([cur.slice(2), arr[i + 1] ?? ''])
    return acc
  }, []),
)
const input = args.input
const output = args.output
if (!input || !output) {
  console.error('usage: node build_html.mjs --input x.md --output x.html [--title "..."]')
  process.exit(1)
}
const md = fs.readFileSync(input, 'utf8')
const title = args.title || (md.match(/^#\s+(.+)$/m)?.[1] ?? '课程笔记')
const body = marked.parse(md, { mangle: false, headerIds: true })
const css = `
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin:0; background:#f8fafc; color:#0f172a; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif; line-height:1.85; }
article { max-width: 880px; margin: 0 auto; background:#fff; padding: 48px 56px 80px; }
h1 { font-size: 30px; line-height:1.3; margin: 0 0 18px; }
h2 { font-size: 22px; margin: 40px 0 14px; padding-top: 12px; border-top: 1px solid #eef2f7; }
h3 { font-size: 18px; margin: 28px 0 10px; }
p { margin: 12px 0; }
a { color:#2563eb; }
blockquote { margin: 16px 0; padding: 10px 16px; border-left: 3px solid #93c5fd; background:#f8fafc; color:#334155; }
code { background:#f1f5f9; padding:1px 5px; border-radius:4px; font-size:.92em; }
pre { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:10px; overflow:auto; }
pre code { background:transparent; color:inherit; padding:0; }
table { width:100%; border-collapse:collapse; margin:16px 0; font-size:14px; }
th,td { border:1px solid #e2e8f0; padding:8px 10px; text-align:left; vertical-align:top; }
th { background:#f8fafc; }
figure { margin: 22px 0; }
figure img { width:100%; display:block; border-radius:12px; border:1px solid #e2e8f0; }
figcaption { color:#64748b; font-size:13px; margin-top:8px; text-align:center; }
hr { border:0; border-top:1px solid #e2e8f0; margin:32px 0; }
@media (max-width:640px){ article{padding:28px 16px 60px;} h1{font-size:24px;} h2{font-size:19px;} }
`
const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title.replace(/[<>&]/g, '')}</title>
<style>${css}</style>
</head>
<body><article>
${body}
</article></body></html>`
fs.mkdirSync(path.dirname(output), { recursive: true })
fs.writeFileSync(output, html, 'utf8')
console.log('wrote', output)
