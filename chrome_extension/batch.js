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
    log("missing tabId");
    return;
  }

  let totalOrders = 0;
  let totalItems = 0;
  let stopReason = "";
  log(`开始同步：${sinceDate} 至 ${untilDate}`);
  log(`读取订单详情：${includeDetails ? "是" : "否"}`);
  const firstPageUrl = `https://www.amazon.co.jp/gp/your-account/order-history?timeFilter=year-${year}`;
  log(`正在打开 ${year} 年注文履歴...`);
  await chrome.tabs.update(tabId, { url: firstPageUrl });
  await waitForTabComplete(tabId);
  await sleep(1200);

  for (let page = 1; page <= maxPages; page += 1) {
    log(`第 ${page} 页：正在读取列表和订单详情，请查看 Amazon 页面右上角进度...`);
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
    log(`第 ${page} 页读取完成：${result.orders.length} 个订单 / ${result.item_count} 个商品`);
    if (result.orders.length > 0) {
      log(`第 ${page} 页：正在写入本地数据库...`);
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
      log(`第 ${page} 页保存完成：${saved.saved_orders} 个订单 / ${saved.saved_items} 个商品`);
    }
    if (result.reached_since_date) {
      stopReason = `reached_since_date_${sinceDate}`;
      break;
    }
    if (!result.next_url) {
      stopReason = "no_next_page";
      break;
    }
    log(`第 ${page} 页完成，准备翻到下一页...`);
    await chrome.tabs.update(tabId, { url: result.next_url });
    await waitForTabComplete(tabId);
    await sleep(1800);
  }

  if (!stopReason) {
    stopReason = `max_pages_${maxPages}`;
  }
  const reasonText = friendlyStopReason(stopReason, sinceDate, maxPages);
  log(`同步完成：${totalOrders} 个订单 / ${totalItems} 个商品。${reasonText}`);
  await showAmazonStatus(tabId, `同步完成\n${totalOrders} 个订单 / ${totalItems} 个商品\n${reasonText}`, "success");
  await chrome.tabs.create({ url: `${RECEIVER}/dashboard` });
}

function friendlyStopReason(reason, sinceDate, maxPages) {
  if (reason.startsWith("reached_since_date_")) {
    return `已读取到起始日期 ${sinceDate}。`;
  }
  if (reason === "no_next_page") {
    return "已读取到最后一页。";
  }
  if (reason.startsWith("max_pages_")) {
    return `已达到 ${maxPages} 页安全上限，请检查日期范围。`;
  }
  return "任务已正常结束。";
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
    log(`无法更新 Amazon 页面提示：${err?.message || err}`);
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
  log(`ERROR: ${err?.message || err}`);
  const tabId = Number(new URLSearchParams(location.search).get("tabId"));
  if (tabId) {
    await showAmazonStatus(tabId, `同步失败\n${err?.message || err}\n请查看 Batch 标签页日志。`, "error");
  }
});
