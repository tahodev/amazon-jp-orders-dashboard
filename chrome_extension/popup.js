const RECEIVER = "http://127.0.0.1:8776";

const healthEl = document.getElementById("health");
const logEl = document.getElementById("log");
const syncLatestBtn = document.getElementById("syncLatest");
const syncHintEl = document.getElementById("syncHint");
const captureBtn = document.getElementById("capture");
const captureAllBtn = document.getElementById("captureAll");
const dashboardBtn = document.getElementById("dashboard");
const openYearBtn = document.getElementById("openYear");
const yearEl = document.getElementById("year");
const sinceEl = document.getElementById("since");
const untilEl = document.getElementById("until");
const detailsEl = document.getElementById("details");

function log(message) {
  const stamp = new Date().toLocaleTimeString();
  logEl.textContent = `[${stamp}] ${message}\n` + logEl.textContent;
}

async function checkHealth() {
  try {
    const res = await fetch(`${RECEIVER}/api/health`, { cache: "no-store" });
    const data = await res.json();
    healthEl.textContent = data.ok ? "ローカル受信サービス：接続済み" : "ローカル受信サービス：エラー";
  } catch (err) {
    healthEl.textContent = "ローカル受信サービス：停止中";
    log("先に scripts\\start_amazon_jp_orders.bat を起動してください。");
  }
}

openYearBtn.addEventListener("click", async () => {
  const year = selectedYear();
  await chrome.tabs.create({
    url: orderHistoryUrl(year)
  });
  log(`${year}年の注文履歴を開きました。`);
});

dashboardBtn.addEventListener("click", async () => {
  await chrome.tabs.create({ url: `${RECEIVER}/dashboard` });
});

syncLatestBtn.addEventListener("click", async () => {
  setBusy(true);
  try {
    const year = new Date().getFullYear();
    const untilDate = formatLocalDate(new Date());
    const stateRes = await fetch(`${RECEIVER}/api/sync-state?year=${year}`, { cache: "no-store" });
    const state = await stateRes.json();
    if (!stateRes.ok || !state.ok) {
      throw new Error(state.error || "ローカルの同期状態を取得できませんでした");
    }
    const sinceDate = recommendedSinceDate(state.latest_order_date, year, 14);
    yearEl.value = String(year);
    sinceEl.value = sinceDate;
    untilEl.value = untilDate;
    syncHintEl.textContent = state.latest_order_date
      ? `${state.order_count}件の注文を保存済み。14日前まで遡り、${sinceDate}〜${untilDate}を更新します`
      : `今年の記録はまだありません。${sinceDate}〜${untilDate}を初回同期します`;
    log(`${sinceDate}〜${untilDate}の同期を準備しています。`);
    const tab = await getAmazonTab({ allowCreate: true, year });
    if (!tab) {
      return;
    }
    await openBatchCapture(tab, year, sinceDate, untilDate, "latest");
  } catch (err) {
    log(`同期に失敗しました：${err?.message || err}`);
    if (String(err).includes("Failed to fetch")) {
      syncHintEl.textContent = "先に start_amazon_jp_orders.bat を起動してください";
    }
  } finally {
    setBusy(false);
  }
});

captureBtn.addEventListener("click", async () => {
  await runCurrentPageCapture();
});

captureAllBtn.addEventListener("click", async () => {
  setBusy(true);
  try {
    if (!validRange()) {
      return;
    }
    const tab = await getAmazonTab({ allowCreate: false });
    if (!tab) {
      return;
    }
    const year = selectedYear();
    await openBatchCapture(tab, year, sinceEl.value, untilEl.value, "range");
    log(`${sinceEl.value}〜${untilEl.value}の取り込みを開始しました。`);
  } catch (err) {
    log(`エラー：${err?.message || err}`);
  } finally {
    setBusy(false);
  }
});

async function runCurrentPageCapture() {
  setBusy(true);
  try {
    if (!validRange()) {
      return;
    }
    const tab = await getAmazonTab({ allowCreate: false });
    if (!tab) {
      return;
    }
    log("現在のページと注文内容を読み取っています...");
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: captureAmazonOrdersFromPage,
      args: [{
        sinceDate: sinceEl.value,
        untilDate: untilEl.value,
        includeDetails: detailsEl.checked,
        pageNumber: 1,
        returnNextUrl: false
      }]
    });
    if (!result?.ok) {
      log(`取り込みに失敗しました：${result?.error || "原因不明のエラー"}`);
      return;
    }
    log(`ページの解析が完了しました：${result.orders.length}件の注文 / ${result.item_count}件の商品`);
    const res = await fetch(`${RECEIVER}/api/capture`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result)
    });
    const saved = await res.json();
    if (!saved.ok) {
      log(`保存に失敗しました：${saved.error || res.status}`);
      return;
    }
    log(`保存完了：${saved.saved_orders}件の注文 / ${saved.saved_items}件の商品`);
    await chrome.tabs.create({ url: saved.dashboard_url || `${RECEIVER}/dashboard` });
  } catch (err) {
    log(`エラー：${err?.message || err}`);
  } finally {
    setBusy(false);
  }
}

async function getAmazonTab({ allowCreate, year = selectedYear() }) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id && tab.url?.startsWith("https://www.amazon.co.jp/")) {
    return tab;
  }
  if (allowCreate) {
    log("専用のAmazon注文履歴タブを開いています...");
    return chrome.tabs.create({ url: orderHistoryUrl(year), active: false });
  }
  log("先にAmazon.co.jpの注文履歴ページを開いてください。");
  return null;
}

async function openBatchCapture(tab, year, sinceDate, untilDate, mode) {
  const batchUrl = chrome.runtime.getURL(
    `batch.html?tabId=${encodeURIComponent(tab.id)}&year=${encodeURIComponent(year)}&since=${encodeURIComponent(sinceDate)}&until=${encodeURIComponent(untilDate)}&details=${detailsEl.checked ? "1" : "0"}&mode=${encodeURIComponent(mode)}`
  );
  await chrome.tabs.create({ url: batchUrl });
}

function setBusy(busy) {
  syncLatestBtn.disabled = busy;
  captureBtn.disabled = busy;
  captureAllBtn.disabled = busy;
}

function selectedYear() {
  return Number(yearEl.value || new Date().getFullYear());
}

function orderHistoryUrl(year) {
  return `https://www.amazon.co.jp/gp/your-account/order-history?timeFilter=year-${year}`;
}

function setYearRange(year) {
  sinceEl.value = `${year}-01-01`;
  untilEl.value = `${year}-12-31`;
}

function recommendedSinceDate(latestOrderDate, year, overlapDays) {
  const yearStart = `${year}-01-01`;
  if (!latestOrderDate || !latestOrderDate.startsWith(`${year}-`)) {
    return yearStart;
  }
  const latest = new Date(`${latestOrderDate}T00:00:00`);
  latest.setDate(latest.getDate() - overlapDays);
  return [formatLocalDate(latest), yearStart].sort().reverse()[0];
}

function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function validRange() {
  if (!sinceEl.value || !untilEl.value) {
    log("開始日と終了日を選択してください。");
    return false;
  }
  if (sinceEl.value > untilEl.value) {
    log("開始日は終了日以前にしてください。");
    return false;
  }
  return true;
}

async function init() {
  const currentYear = new Date().getFullYear();
  for (let year = currentYear; year >= 2010; year -= 1) {
    const option = document.createElement("option");
    option.value = String(year);
    option.textContent = `${year}年`;
    yearEl.appendChild(option);
  }
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const pageYear = tab?.url?.match(/(?:timeFilter|orderFilter)=year-(\d{4})/)?.[1];
  yearEl.value = pageYear || String(currentYear);
  setYearRange(yearEl.value);
  yearEl.addEventListener("change", () => setYearRange(yearEl.value));
  await checkHealth();
}

init();
