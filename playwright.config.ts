import { defineConfig } from '@playwright/test';
const python = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';
export default defineConfig({
 testDir:'tests/e2e', timeout:120000, expect:{timeout:20000}, fullyParallel:false, workers:1,
 reporter:[['list'],['html',{open:'never'}]], use:{viewport:{width:1440,height:1000},baseURL:'http://127.0.0.1:5180',trace:'retain-on-failure',screenshot:'only-on-failure'},
 projects:[{name:'chromium',use:{browserName:'chromium'}}],
 webServer:[
  {command:python+' -m uvicorn app.main:app --host 127.0.0.1 --port 8100',url:'http://127.0.0.1:8100/api/health',reuseExistingServer:true,timeout:30000},
  {command:'npm --prefix apps/web run dev',url:'http://127.0.0.1:5180',reuseExistingServer:true,timeout:30000}
 ]
});
