// Screenshots of the live page for the LinkedIn carousel (phone size, 3x). Run from the project folder:
//   node docs/linkedin/capture_shots.mjs
import puppeteer from "puppeteer-core";

const SITE = "https://cari-data-bps.netlify.app";
const OUT = "docs/linkedin/shots";
const browser = await puppeteer.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });

async function page(scheme) {
  const p = await browser.newPage();
  await p.setViewport({ width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
  await p.goto(SITE, { waitUntil: "networkidle2" });
  if (await p.$eval("#welcome", (n) => !n.hidden)) await p.click("#welcome-start");
  return p;
}
async function ask(p, q) {
  await p.type("#q", q);
  await p.keyboard.press("Enter");
  await p.waitForSelector("#results .result", { timeout: 90000 });
  await new Promise((r) => setTimeout(r, 800));
}
async function openTable(p, nth) {
  await p.click(`#results .result:nth-child(${nth}) button.primary`);
  await p.waitForFunction(() => !document.getElementById("table-wrap").hidden, { timeout: 90000 });
  await new Promise((r) => setTimeout(r, 800));
}

let p = await page("dark");
await p.screenshot({ path: `${OUT}/home_dark.png` });
await p.close();

p = await page("light");
await ask(p, "tingkat pengangguran jawa barat");
await p.screenshot({ path: `${OUT}/search_light.png` });
await openTable(p, 1);
await p.screenshot({ path: `${OUT}/panel_var_light.png` });
await p.close();

await new Promise((r) => setTimeout(r, 65000)); // per-client limit: 20 requests a minute
p = await page("light");
await ask(p, "jumlah penduduk miskin kabupaten garut");
await openTable(p, 1);
await p.screenshot({ path: `${OUT}/panel_garut_light.png` });
await p.close();
await browser.close();
