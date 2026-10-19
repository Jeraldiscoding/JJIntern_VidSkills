import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { connect } from '../../scripts/cdp.mjs';

// This command navigates only the isolated supplied browser. Never use a personal profile.
const checkedDate=process.argv[3];
if(!/^\d{4}-\d{2}-\d{2}$/.test(checkedDate ?? ''))
  throw new Error('Usage: node creative/scripts/capture-public.mjs PORT YYYY-MM-DD (actual client check date)');
const cdp = await connect(process.argv[2]);
const out = new URL('./', import.meta.url);
await fs.mkdir(out, { recursive: true });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const states = [];
try {
  await cdp.send('Page.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 390, height: 844, deviceScaleFactor: 2, mobile: true,
  });
  await cdp.send('Emulation.setEmulatedMedia', {
    features: [{ name: 'prefers-color-scheme', value: 'dark' }],
  });
  await cdp.send('Page.navigate', { url: 'https://jjintern.com/companies' });
  for (let i = 0; i < 25; i++) {
    if (await cdp.evaluate('!!document.querySelector("input[type=search]")')) break;
    await delay(400);
  }
  await cdp.evaluate('document.fonts.ready.then(() => true)');
  await delay(4500); // Allow public data/hydration; no freshness guarantee.
  if (!(await cdp.evaluate('document.querySelector("input[type=search]")?.value === ""')))
    throw new Error('Expected empty directory search.');
  const style = await cdp.evaluate(`({
    background: getComputedStyle(document.body).backgroundColor,
    bgVariable: getComputedStyle(document.documentElement).getPropertyValue('--bg'),
    font: getComputedStyle(document.body).fontFamily,
    theme: document.documentElement.getAttribute('data-theme'),
    stylesheets: [...document.styleSheets].map(s=>s.href)
  })`);
  async function capture(name, query) {
    const value = await cdp.evaluate(`({
      query: document.querySelector('input[type=search]').value,
      text: document.body.innerText,
      companyNames: [...document.querySelectorAll('p')].filter(p=>p.classList.contains('truncate') && p.classList.contains('font-semibold')).map(p=>p.innerText),
      url:location.href
    })`);
    if (value.query !== query) throw new Error(`Expected ${query}, got ${value.query}`);
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
    await fs.writeFile(new URL(`${name}.png`, out), Buffer.from(shot.data, 'base64'));
    states.push({ file: `${name}.png`, ...value });
  }
  await capture('directory-empty', '');
  const rect = await cdp.evaluate('document.querySelector("input[type=search]").getBoundingClientRect().toJSON()');
  await cdp.send('Input.dispatchMouseEvent', { type:'mousePressed', x:rect.x+80, y:rect.y+20, button:'left', clickCount:1 });
  await cdp.send('Input.dispatchMouseEvent', { type:'mouseReleased', x:rect.x+80, y:rect.y+20, button:'left', clickCount:1 });
  let query = '';
  for (const [i, letter] of [...'Microsoft'].entries()) {
    await cdp.send('Input.insertText', { text:letter });
    query += letter;
    await delay(250);
    await capture(`directory-${String(i+1).padStart(2,'0')}`, query);
  }
  const end = states.at(-1);
  if (!end.companyNames.includes('Microsoft') || end.text.includes('\nShopee\n') || end.text.includes('\nByteDance\n'))
    throw new Error('Search did not visibly narrow to Microsoft; do not use these captures as a working demo.');
  await fs.writeFile(new URL('capture-record.json', out), JSON.stringify({
    checked:checkedDate, captured_at_utc:new Date().toISOString(), timezone:'Europe/Stockholm', source:'https://jjintern.com/companies',
    context:'Isolated logged-out Chrome; actual input events; discrete captured states. Editorial timing is not a product-speed measurement.',
    style, states,
  }, null, 2)+'\n');
  const files=[];
  for(const name of ['capture-record.json', ...states.map(state=>state.file)]) {
    const bytes=await fs.readFile(new URL(name,out));
    files.push({path:name,sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length});
  }
  await fs.writeFile(new URL('manifest.json',out),JSON.stringify({
    checked:checkedDate,captured_at_utc:new Date().toISOString(),timezone:'Europe/Stockholm',source:'https://jjintern.com/companies',
    context:'Public logged-out screenshots; not employer-confirmed vacancies or a licence grant',files,
  },null,2)+'\n');
  console.log(JSON.stringify({ status:'captured', states:states.length, style, result:end.companyNames }));
} finally { cdp.close(); }
