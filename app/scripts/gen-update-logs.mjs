import { execSync } from 'child_process'
import { writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const outPath = resolve(__dirname, '../src/config/update-logs.ts')

function getGitLog() {
  try {
    const output = execSync(
      'git log --pretty=format:"%H|||%s|||%ai" --date=short',
      { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
    )
    return output.trim().split('\n').filter(Boolean).map(line => {
      const parts = line.split('|||')
      const hash = parts[0].trim().slice(0, 7)
      const message = parts.slice(1, -1).join('|||').trim()
      const date = parts[parts.length - 1].trim().split(' ')[0]
      return { hash, message, date }
    })
  } catch {
    return []
  }
}

function cleanMessage(msg) {
  // Strip conventional commit prefixes
  return msg
    .replace(/^(feat|fix|docs|style|refactor|test|chore|perf|ci|build)(\(.*?\))?:\s*/i, '')
    .trim()
}

function truncate(msg, max) {
  if (msg.length <= max) return msg
  return msg.slice(0, max - 1) + '…'
}

const commits = getGitLog()
if (!commits.length) {
  console.log('No git history found, keeping existing update-logs.ts')
  process.exit(0)
}

// Group by date
const dateGroups = new Map()
for (const c of commits) {
  if (!dateGroups.has(c.date)) dateGroups.set(c.date, [])
  dateGroups.get(c.date).push(c)
}

const sortedDates = [...dateGroups.keys()].sort().reverse()
const logs = []
let vi = 0

for (const date of sortedDates) {
  const group = dateGroups.get(date)
  const title = truncate(cleanMessage(group[0].message), 60)
  const details = group.map(c => truncate(cleanMessage(c.message), 200))

  // Only include entries with meaningful content
  if (details.length === 0) continue

  logs.push({
    version: `2.${vi}.0`,
    date,
    title,
    details,
  })
  vi++
}

const content = `/**
 * 更新日志 — 由 scripts/gen-update-logs.mjs 在 build 时从 git 历史自动生成
 * 不要手动编辑此文件
 */
export interface UpdateLogItem {
  version: string
  date: string
  title: string
  details: string[]
}

export const updateLogs: UpdateLogItem[] = ${JSON.stringify(logs, null, 2)};
`

writeFileSync(outPath, content, 'utf-8')
console.log(`Generated update-logs.ts with ${logs.length} entries from git history`)
