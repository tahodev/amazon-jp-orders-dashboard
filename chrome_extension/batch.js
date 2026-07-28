const RECEIVER = "http://127.0.0.1:8776";
const logEl = document.getElementById("log");

function log(message) {
  const stamp = new Date().toLocaleTimeString();
  logEl.textContent += `[${stamp}] ${message}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

async function main() {
  const params = new URLSearchParams(location.search);
  const tabId = Number(params.get("tabId"));
  const year = Number(params.get("year") || new Date().getFullYear());
  const sinceDate = params.get("since") || `${year}-01-01`;
  const untilDate = params.get("until") || `${year}-12-31`;
  const includeDetails = params.get("details") !== "0";
  const mode = params.get("mode") || "range";
  const maxPages = Number(params.get("maxPages") || 50);
  if (!tabId) {
    log("対象のAmazonタブを特定できませんでした。");
    return;
  }

  let totalOrders = 0;
  let totalItems = 0;
  let stopReason = "";
  log(`同期期間：${sinceDate}〜${untilDate}`);
  log(`注文内容ページの確認：${includeDetails ? "あり" : "なし"}`);
  const firstPageUrl = `https://www.amazon.co.jp/gp/your-account/order-history?timeFilter=year-${year}`;
  log(`${year}年の注文履歴を開いています...`);
  await chrome.tabs.update(tabId, { url: firstPageUrl });
  await waitForTabComplete(tabId);
  await sleep(1200);

  for (let page = 1; page <= maxPages; page += 1) {
    log(`${page}ページ目：注文一覧と注文内容を確認しています。Amazonページ右上の進捗も確認できます。`);
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: captureAmazonOrdersFromPage,
      args: [{
        sinceDate,
        untilDate,
        includeDetails,
        pageNumber: page,
        returnNextUrl: true
      }]
    });
    if (!result?.ok) {
      throw new Error(result?.error || `page ${page} capture failed`);
    }
    log(`${page}ページ目の読取完了：${result.orders.length}件の注文 / ${result.item_count}件の商品`);
    if (result.orders.length > 0) {
      log(`${page}ページ目：ローカルデータベースに保存しています...`);
      const res = await fetch(`${RECEIVER}/api/capture`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...result,
          note: `chrome_extension_${mode}_page_${page}:${result.stop_reason || ""}`
        })
      });
      const saved = await res.json();
      if (!saved.ok) {
        throw new Error(saved.error || `page ${page} save failed`);
      }
      totalOrders += saved.saved_orders || 0;
      totalItems += saved.saved_items || 0;
      log(`${page}ページ目の保存完了：${saved.saved_orders}件の注文 / ${saved.saved_items}件の商品`);
    }
    if (result.reached_since_date) {
      stopReason = `reached_since_date_${sinceDate}`;
      break;
    }
    if (!result.next_url) {
      stopReason = "no_next_page";
      break;
    }
    log(`${page}ページ目が完了しました。次のページへ移動します...`);
    await chrome.tabs.update(tabId, { url: result.next_url });
    await waitForTabComplete(tabId);
    await sleep(1800);
  }

  if (!stopReason) {
    stopReason = `max_pages_${maxPages}`;
  }
  const reasonText = friendlyStopReason(stopReason, sinceDate, maxPages);
  log(`同期完了：${totalOrders}件の注文 / ${totalItems}件の商品。${reasonText}`);
  await showAmazonStatus(tabId, `同期が完了しました\n${totalOrders}件の注文 / ${totalItems}件の商品\n${reasonText}`, "success");
  await chrome.tabs.create({ url: `${RECEIVER}/dashboard` });
}

function friendlyStopReason(reason, sinceDate, maxPages) {
  if (reason.startsWith("reached_since_date_")) {
    return `開始日（${sinceDate}）以前の注文を確認したため終了しました。`;
  }
  if (reason === "no_next_page") {
    return "最後のページまで確認しました。";
  }
  if (reason.startsWith("max_pages_")) {
    return `安全上限の${maxPages}ページに達しました。日付範囲を確認してください。`;
  }
  return "正常に終了しました。";
}

async function showAmazonStatus(tabId, message, status) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: (text, state) => {
        const box = document.getElementById("amazon-jp-orders-capture-status");
        if (!box) return;
        box.textContent = `Amazon JP Orders\n${text}`;
        box.style.borderColor = state === "error" ? "#b42318" : "#1f7a4d";
        box.style.background = state === "error" ? "#fff4f2" : "#f1fff6";
      },
      args: [message, status]
    });
  } catch (err) {
    log(`Amazonページの進捗表示を更新できませんでした：${err?.message || err}`);
  }
}

function waitForTabComplete(tabId) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      reject(new Error("wait_tab_complete_timeout"));
    }, 30000);
    function listener(updatedTabId, changeInfo, tab) {
      if (updatedTabId === tabId && changeInfo.status === "complete") {
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve(tab);
      }
    }
    chrome.tabs.onUpdated.addListener(listener);
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

main().catch(async (err) => {
  log(`エラー：${err?.message || err}`);
  const tabId = Number(new URLSearchParams(location.search).get("tabId"));
  if (tabId) {
    await showAmazonStatus(tabId, `同期に失敗しました\n${err?.message || err}\n同期タブのログを確認してください。`, "error");
  }
});
