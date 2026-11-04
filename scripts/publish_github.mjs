#!/usr/bin/env node
// Publish a generated notes folder to GitHub + Pages.
// Requires GITHUB_TOKEN with repo scope.
//
// Usage:
//   GITHUB_TOKEN=... node publish_github.mjs \
//     --dir dsh-class-notes --repo owner/repo --branch main
import fs from 'node:fs'
import path from 'node:path'

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, cur, i, arr) => {
    if (cur.startsWith('--')) acc.push([cur.slice(2), arr[i + 1] ?? ''])
    return acc
  }, []),
)
const dir = args.dir
const repoArg = args.repo
const branch = args.branch || 'main'
const token = process.env.GITHUB_TOKEN
if (!dir || !repoArg || !token) {
  console.error('usage: GITHUB_TOKEN=... node publish_github.mjs --dir <folder> --repo owner/repo [--branch main]')
  process.exit(1)
}
const [owner, repo] = repoArg.split('/')
const root = path.resolve(dir)

async function api(p, opt = {}) {
  const r = await fetch('https://api.github.com' + p, {
    ...opt,
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'course-notes-skill',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(opt.headers || {}),
    },
  })
  const text = await r.text()
  let data
  try { data = JSON.parse(text) } catch { data = text }
  if (!r.ok) {
    const e = new Error('HTTP ' + r.status)
    e.status = r.status
    e.body = data
    throw e
  }
  return data
}

function walk(d, base = '') {
  const out = []
  for (const name of fs.readdirSync(d)) {
    if (['.git', 'node_modules', '.video-cache', '.work', '.subs', '.subs_full'].includes(name)) continue
    if (/\.(m4s|mp4|zip|7z)$/i.test(name)) continue
    const full = path.join(d, name)
    const rel = base ? base + '/' + name : name
    const st = fs.statSync(full)
    if (st.isDirectory()) out.push(...walk(full, rel))
    else out.push(rel)
  }
  return out
}

async function ensureRepo() {
  try {
    await api(`/repos/${owner}/${repo}`)
  } catch (e) {
    if (e.status !== 404) throw e
    await api('/user/repos', {
      method: 'POST',
      body: JSON.stringify({ name: repo, private: false, auto_init: true }),
    })
    await new Promise(r => setTimeout(r, 1500))
  }
}

async function putFile(rel) {
  const local = path.join(root, rel)
  const content = fs.readFileSync(local).toString('base64')
  let sha = null
  try {
    sha = (await api(`/repos/${owner}/${repo}/contents/${encodeURI(rel)}?ref=${branch}`)).sha
  } catch {}
  await api(`/repos/${owner}/${repo}/contents/${encodeURI(rel)}`, {
    method: 'PUT',
    body: JSON.stringify({
      message: 'Publish course notes: ' + rel,
      content,
      branch,
      ...(sha ? { sha } : {}),
    }),
  })
}

async function ensurePages() {
  try {
    await api(`/repos/${owner}/${repo}/pages`)
  } catch (e) {
    if (e.status !== 404) return
    try {
      await api(`/repos/${owner}/${repo}/pages`, {
        method: 'POST',
        body: JSON.stringify({ source: { branch, path: '/' } }),
      })
    } catch (e2) {
      console.log('pages enable skipped:', e2.status, JSON.stringify(e2.body).slice(0, 160))
    }
  }
  try {
    await api(`/repos/${owner}/${repo}/pages/builds`, { method: 'POST' })
    console.log('pages build requested')
  } catch (e) {
    console.log('pages build request skipped:', e.status)
  }
}

async function main() {
  await ensureRepo()
  const files = walk(root)
  console.log('files:', files.length)
  let ok = 0
  for (const f of files) {
    try { await putFile(f); ok++ } catch (e) { console.log('fail', f, e.status) }
  }
  console.log('uploaded:', ok, '/', files.length)
  await ensurePages()
  console.log(`https://${owner}.github.io/${repo}/`)
}

main().catch(e => {
  console.error('FATAL', e.status || '', JSON.stringify(e.body || e.message).slice(0, 300))
  process.exit(1)
})
