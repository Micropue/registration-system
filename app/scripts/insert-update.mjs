import { execSync } from 'child_process'

const API_BASE = process.env.API_BASE || 'http://localhost:8001'
const ADMIN_USER = process.env.ADMIN_USER || 'admin'
const ADMIN_PASS = process.env.ADMIN_PASS || '123456'

async function login() {
  const form = new URLSearchParams({ username: ADMIN_USER, password: ADMIN_PASS })
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString()
  })
  const data = await res.json()
  if (data.code !== 200) {
    throw new Error(`Login failed: ${data.msg}`)
  }
  return data.data.token
}

function getGitLog() {
  const output = execSync(
    'git log --pretty=format:"%H|||%s|||%ai" --date=iso',
    { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }
  )
  return output.trim().split('\n').filter(Boolean).map(line => {
    const [hash, message, date] = line.split('|||')
    return { hash, message, date }
  })
}

async function main() {
  try {
    const commits = getGitLog()
    console.log(`Found ${commits.length} commits in git history`)

    const token = await login()
    console.log('Logged in as admin')

    const res = await fetch(`${API_BASE}/admin/update-logs/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(commits)
    })
    const data = await res.json()
    if (data.code === 200) {
      console.log(data.msg)
    } else {
      console.error(`Sync failed: ${data.msg}`)
      process.exit(1)
    }
  } catch (e) {
    console.error('Error:', e.message)
    process.exit(1)
  }
}

main()
