const { spawnSync } = require('node:child_process');
const assert = require('node:assert/strict');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const launcher = path.resolve(__dirname, '../infrastructure/scripts/python.cjs');

function launch(args) {
  const result = spawnSync(process.execPath, [launcher, ...args], {
    cwd: os.tmpdir(),
    encoding: 'utf8',
    timeout: 20000,
    windowsHide: true,
  });
  assert.ifError(result.error);
  return result;
}

test('finds the project environment from another directory and preserves arguments', () => {
  const args = ['argument with spaces', 'literal & text'];
  const result = launch(['-c', 'import json, sys; print(json.dumps(sys.argv[1:]))', ...args]);
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), args);
});

test('propagates a failing Python exit code to CI', () => {
  const result = launch(['-c', 'import sys; sys.exit(7)']);
  assert.equal(result.status, 7, result.stderr);
});
