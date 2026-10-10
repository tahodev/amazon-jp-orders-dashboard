// Synthetic-fixture regression test for chrome_extension/capture_core.js.
// Runs the real capture flow in Node via jsdom: order list page (document)
// + one multi-item detail page (fetch stub). All fixture values are synthetic.
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const { JSDOM } = require("jsdom");

const ROOT = path.resolve(__dirname, "..", "..");
const readFixture = (name) => fs.readFileSync(path.join(ROOT, "tests", "fixtures", name), "utf8");

const listHtml = readFixture("order-list-synthetic.html");
const detailHtml = readFixture("order-detail-multi-synthetic.html");

const dom = new JSDOM(listHtml, {
  url: "https://www.amazon.co.jp/gp/your-account/order-history?timeFilter=year-2026"
});

// jsdom does not implement innerText on some versions; the parser reads it.
if (typeof dom.window.HTMLElement.prototype.innerText === "undefined") {
  Object.defineProperty(dom.window.HTMLElement.prototype, "innerText", {
    get() { return this.textContent || ""; },
    configurable: true
  });
}

global.document = dom.window.document;
global.location = dom.window.location;
global.DOMParser = dom.window.DOMParser;
global.fetch = async () => ({ ok: true, status: 200, text: async () => detailHtml });

const source = fs.readFileSync(path.join(ROOT, "chrome_extension", "capture_core.js"), "utf8");
const captureAmazonOrdersFromPage = new Function(`${source}; return captureAmazonOrdersFromPage;`)();

(async () => {
  const result = await captureAmazonOrdersFromPage({ sinceDate: "2000-01-01", includeDetails: true });

  assert.strictEqual(result.ok, true, `capture failed: ${result.error || "unknown"}`);
  assert.strictEqual(result.orders.length, 2, `expected 2 orders, got ${result.orders.length}`);

  // 単品注文（詳細リンクなし → 一覧からの抽出、価格は合計にフォールバック）
  const single = result.orders.find((o) => o.order_id === "503-0000000-0000001");
  assert.ok(single, "single-item order not found");
  assert.strictEqual(single.order_date, "2026-03-14");
  assert.strictEqual(single.order_total_yen, 1980);
  assert.strictEqual(single.items.length, 1);
  assert.ok(single.items[0].title.includes("合成ノートブック"));
  assert.strictEqual(single.items[0].item_total_yen, 1980);
  assert.strictEqual(single.items[0].asin, "B0SYNTH001");

  // 複数商品注文（詳細ページのfetchをスタブして件数・単価・数量・小計を検証）
  const multi = result.orders.find((o) => o.order_id === "503-0000000-0000002");
  assert.ok(multi, "multi-item order not found");
  assert.strictEqual(multi.order_date, "2026-04-02");
  assert.strictEqual(multi.order_total_yen, 5360);
  assert.strictEqual(multi.detail_status, "ok");
  assert.strictEqual(multi.items.length, 2);
  const battery = multi.items.find((i) => i.title.includes("合成アルカリ電池"));
  const cable = multi.items.find((i) => i.title.includes("合成USB-Cケーブル"));
  assert.ok(battery && cable, "expected items missing");
  assert.strictEqual(battery.quantity, 2);
  assert.strictEqual(battery.item_price_yen, 1280);
  assert.strictEqual(battery.item_total_yen, 2560);
  assert.strictEqual(battery.asin, "B0SYNTH002");
  assert.strictEqual(cable.quantity, 1);
  assert.strictEqual(cable.item_price_yen, 2800);
  assert.strictEqual(cable.item_total_yen, 2800);
  assert.strictEqual(cable.asin, "B0SYNTH003");

  console.log("capture_core fixture test: OK (2 orders, 3 items, all synthetic)");
  process.exit(0);
})().catch((err) => {
  console.error("capture_core fixture test: FAILED");
  console.error(err);
  process.exit(1);
});
