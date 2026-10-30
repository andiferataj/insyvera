import { defineConfig } from '@playwright/test';
export default defineConfig({
 testDir:'tests/e2e', timeout:120000, expect:{timeout:20000}, fullyParallel:false, workers:1,
 reporter:[['list'],['html',{open:'never'}]], use:{viewport:{width:1440,height:1000},baseURL:'http://127.0.0.1:5180',trace:'retain-on-failure',screenshot:'only-on-failure'},
 projects:[{name:'chromium',use:{browserName:'chromium'}}],
 webServer:[
  {command:'node infrastructure/scripts/python.cjs -m uvicorn app.main:app --host 127.0.0.1 --port 8100',cwd:__dirname,url:'http://127.0.0.1:8100/api/health',reuseExistingServer:!process.env.CI,timeout:30000},
  {command:'npm --prefix apps/web run dev',cwd:__dirname,url:'http://127.0.0.1:5180',reuseExistingServer:!process.env.CI,timeout:30000}
 ]
});
