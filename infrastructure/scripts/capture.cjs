const { chromium } = require('@playwright/test');
(async()=>{
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
await page.goto('http://127.0.0.1:5180');
await page.screenshot({path:'.local/auth.png',fullPage:true});
console.log(await page.title());
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
