const { spawn } = require('node:child_process');
const { existsSync } = require('node:fs');
const path = require('node:path');

// npm and Playwright execute commands through cmd.exe on Windows. Spawn Python
// directly so forward slashes and spaces in the checkout cannot become shell syntax.
const root = path.resolve(__dirname, '../..');
const executable = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts' : 'bin',
  process.platform === 'win32' ? 'python.exe' : 'python');

if (!existsSync(executable)) {
  console.error('Project Python environment is missing. Create .venv and install requirements.lock first.');
  process.exitCode = 1;
} else {
  const child = spawn(executable, process.argv.slice(2), {
    cwd: root,
    stdio: 'inherit',
    shell: false,
    windowsHide: true,
  });
  child.once('error', error => {
    console.error('Could not start project Python:', error.message);
    process.exitCode = 1;
  });
  child.once('exit', code => { process.exitCode = code ?? 1; });
  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => { if (child.exitCode === null) child.kill(signal); });
  }
}
