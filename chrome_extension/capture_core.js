async function captureAmazonOrdersFromPage(options) {
  const currentYear = new Date().getFullYear();
  const sinceDate = options?.sinceDate || `${currentYear}-01-01`;
  const untilDate = options?.untilDate || "9999-12-31";
  const includeDetails = options?.includeDetails !== false;
  const pageNumber = Number(options?.pageNumber || 1);
  const returnNextUrl = options?.returnNextUrl === true;

  try {
    showCaptureOverlay("准备读取订单列表...");
    const orders = [];
    const seenOrderIds = new Set();
    let sawOlderOrder = false;
    const cards = findOrderCards(document);
    showCaptureOverlay(`第 ${pageNumber} 页：找到 ${cards.length} 个订单区块，开始读取...`);
    if (cards.length === 0) {
      showCaptureOverlay("没有找到订单区块。请确认当前页是注文履歴列表。", true);
      return {
        ok: false,
        error: "no_order_cards_found",
        source_url: location.href
      };
    }
    let index = 0;
    for (const card of cards) {
      index += 1;
      const order = extractOrderFromCard(card, location.href);
      if (!order.order_id || !order.order_date) {
        showCaptureOverlay(`第 ${pageNumber} 页：跳过第 ${index}/${cards.length} 个区块，缺少订单号或注文日`);
        continue;
      }
      if (order.order_date > untilDate) {
        showCaptureOverlay(`第 ${pageNumber} 页：跳过 ${order.order_date}，晚于 ${untilDate}`);
        continue;
      }
      if (order.order_date < sinceDate) {
        sawOlderOrder = true;
        showCaptureOverlay(`第 ${pageNumber} 页：遇到 ${order.order_date}，早于 ${sinceDate}`);
        continue;
      }
      if (seenOrderIds.has(order.order_id)) {
        showCaptureOverlay(`第 ${pageNumber} 页：跳过重复订单 ${order.order_id}`);
        continue;
      }
      seenOrderIds.add(order.order_id);
      if (includeDetails && order.detail_url) {
        showCaptureOverlay(`第 ${pageNumber} 页：读取第 ${index}/${cards.length} 单详情 ${order.order_id}`);
        const detail = await fetchDetail(order.detail_url, order.order_total_yen);
        if (detail.items.length > 0) {
          order.items = detail.items;
        }
        order.detail_status = detail.status;
      } else {
        showCaptureOverlay(`第 ${pageNumber} 页：读取第 ${index}/${cards.length} 单列表内容 ${order.order_id}`);
      }
      if (!order.items || order.items.length === 0) {
        order.items = extractItemsFromNode(card, order.order_total_yen, location.href);
      }
      orders.push(order);
      await sleep(650);
    }

    const itemCount = orders.reduce((sum, order) => sum + (order.items?.length || 0), 0);
    const reachedSinceDate = sawOlderOrder;
    const nextUrl = returnNextUrl && !reachedSinceDate ? findNextPageUrl(document, location.href) : "";
    const nextMessage = returnNextUrl && nextUrl
      ? "本页读取完成，正在保存；随后继续下一页。"
      : "本页读取完成，正在保存。";
    showCaptureOverlay(`${nextMessage}\n第 ${pageNumber} 页：${orders.length} 个订单 / ${itemCount} 个商品`);
    return {
      ok: true,
      source_url: location.href,
      since_date: sinceDate,
      until_date: untilDate,
      captured_at: new Date().toISOString(),
      orders,
      item_count: itemCount,
      next_url: nextUrl,
      reached_since_date: reachedSinceDate,
      stop_reason: reachedSinceDate ? `reached_since_date_${sinceDate}` : (nextUrl ? "page_complete_next_available" : "last_page_complete"),
      note: returnNextUrl ? "chrome_extension_batch_page" : "chrome_extension_current_page"
    };
  } catch (err) {
    showCaptureOverlay(`抓取异常：${err?.message || err}`, true);
    return { ok: false, error: err?.message || String(err), source_url: location.href };
  }

  function findOrderCards(doc) {
    const selectors = [
      ".order-card",
      ".js-order-card",
      ".yohtmlc-order-card",
      "div[class*='order-card']",
      ".a-box-group"
    ];
    const candidates = selectors.flatMap((sel) => Array.from(doc.querySelectorAll(sel)));
    const textCandidates = Array.from(doc.querySelectorAll("div, section")).filter((el) => {
      const text = normalizeText(el.innerText || "");
      return text.includes("注文番号") && text.includes("注文日") && text.includes("合計");
    });
    const merged = [...candidates, ...textCandidates];
    const unique = [];
    for (const el of merged) {
      if (!el || unique.some((seen) => seen === el || seen.contains(el))) {
        continue;
      }
      const text = normalizeText(el.innerText || "");
      if (text.length < 40 || !text.includes("注文番号")) {
        continue;
      }
      unique.push(el);
    }
    return unique;
  }

  function extractOrderFromCard(card, pageUrl) {
    const text = normalizeText(card.innerText || "");
    const orderId = matchFirst(text, /注文番号\s*([0-9]{3}-[0-9]{7}-[0-9]{7})/);
    const orderDate = parseDate(
      matchFirst(text, /注文日\s*([0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日)/) ||
      matchFirst(text, /([0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日)/)
    );
    const total = parseYen(
      matchFirst(text, /合計\s*([¥￥]\s*[0-9,]+)/) ||
      matchFirst(text, /ご請求額\s*[:：]?\s*([¥￥]\s*[0-9,]+)/)
    );
    const detailLink = Array.from(card.querySelectorAll("a")).find((a) => {
      const label = normalizeText(a.innerText || a.textContent || "");
      const href = a.href || "";
      return label.includes("注文内容") || href.includes("order-details") || href.includes("orderID=");
    });
    const items = extractItemsFromNode(card, total, pageUrl);
    return {
      order_id: orderId,
      order_date: orderDate,
      order_total_yen: total,
      detail_url: detailLink ? absoluteHref(detailLink, pageUrl) : "",
      title: items[0]?.title || "",
      items
    };
  }

  async function fetchDetail(url, orderTotal) {
    try {
      const res = await fetch(url, { credentials: "include", cache: "no-store" });
      if (!res.ok) {
        return { status: `http_${res.status}`, items: [] };
      }
      const html = await res.text();
      if (/captcha|認証|ログイン|sign in/i.test(html) && !html.includes("注文の詳細")) {
        return { status: "auth_or_captcha", items: [] };
      }
      const doc = new DOMParser().parseFromString(html, "text/html");
      return { status: "ok", items: extractItemsFromDetail(doc, orderTotal, url) };
    } catch (err) {
      return { status: err?.message || "fetch_failed", items: [] };
    }
  }

  function extractItemsFromDetail(doc, orderTotal, pageUrl) {
    const titleLinks = findProductLinks(doc);
    const out = [];
    const seen = new Set();
    for (const link of titleLinks) {
      const title = cleanTitle(link.innerText || link.textContent || "");
      if (!title || seen.has(title)) {
        continue;
      }
      seen.add(title);
      const block = climbForPriceBlock(link);
      const blockText = normalizeText(block?.innerText || "");
      const price = parseYen(matchFirst(blockText, /([¥￥]\s*[0-9,]+)/));
      const quantity = parseQuantity(blockText);
      const href = absoluteHref(link, pageUrl);
      out.push({
        title,
        item_url: href,
        asin: asinFromUrl(href),
        quantity,
        item_price_yen: price,
        item_total_yen: price ? price * quantity : null,
        seller: matchFirst(blockText, /販売[:：]\s*([^ ¥￥]+)/) || ""
      });
    }
    if (out.length === 1 && !out[0].item_total_yen && orderTotal) {
      out[0].item_total_yen = orderTotal;
      out[0].item_price_yen = orderTotal;
    }
    return out;
  }

  function extractItemsFromNode(root, orderTotal, pageUrl) {
    const links = findProductLinks(root);
    const out = [];
    const seen = new Set();
    for (const link of links) {
      const title = cleanTitle(link.innerText || link.textContent || "");
      if (!title || seen.has(title)) {
        continue;
      }
      seen.add(title);
      const href = absoluteHref(link, pageUrl);
      out.push({
        title,
        item_url: href,
        asin: asinFromUrl(href),
        quantity: 1,
        item_price_yen: links.length === 1 ? orderTotal : null,
        item_total_yen: links.length === 1 ? orderTotal : null,
        seller: ""
      });
    }
    return out;
  }

  function findProductLinks(root) {
    const blacklist = [
      "配送状況", "注文内容", "領収書", "商品レビュー", "再度購入", "商品を表示",
      "返品", "交換", "質問", "出品者", "定期おトク便", "カスタマーサービス",
      "Amazon Mastercard", "Amazonポイント", "Amazonギフトカード"
    ];
    return Array.from(root.querySelectorAll("a")).filter((a) => {
      const text = cleanTitle(a.innerText || a.textContent || "");
      if (text.length < 8 || blacklist.some((word) => text.includes(word))) {
        return false;
      }
      const href = a.href || a.getAttribute("href") || "";
      if (
        href.includes("footer_pay") ||
        href.includes("plattr=JBCBCCFT") ||
        href.includes("/dp/product/B08P4CFBK6")
      ) {
        return false;
      }
      if (a.closest("footer, #navFooter, #rhf, .navFooterBackToTop")) {
        return false;
      }
      return href.includes("/dp/") || href.includes("/gp/product/") || href.includes("/gp/aw/d/");
    });
  }

  function findNextPageUrl(doc, pageUrl) {
    const candidates = [
      ...Array.from(doc.querySelectorAll("ul.a-pagination li.a-last:not(.a-disabled) a")),
      ...Array.from(doc.querySelectorAll("a[aria-label*='次'], a[aria-label*='Next']")),
      ...Array.from(doc.querySelectorAll("a"))
    ];
    for (const a of candidates) {
      const label = normalizeText(`${a.innerText || ""} ${a.getAttribute("aria-label") || ""}`);
      const href = a.getAttribute("href") || "";
      if (!href) {
        continue;
      }
      if (label.includes("次") || label.toLowerCase().includes("next")) {
        return absoluteHref(a, pageUrl);
      }
    }
    return "";
  }

  function climbForPriceBlock(node) {
    let cur = node;
    for (let i = 0; i < 7 && cur?.parentElement; i += 1) {
      cur = cur.parentElement;
      const text = normalizeText(cur.innerText || "");
      if (text.includes("¥") || text.includes("￥")) {
        return cur;
      }
    }
    return node.parentElement;
  }

  function parseDate(text) {
    const value = normalizeText(text || "");
    const m = value.match(/([0-9]{4})\s*年\s*([0-9]{1,2})\s*月\s*([0-9]{1,2})\s*日/);
    if (!m) {
      return "";
    }
    return `${m[1]}-${String(Number(m[2])).padStart(2, "0")}-${String(Number(m[3])).padStart(2, "0")}`;
  }

  function parseYen(value) {
    if (!value) {
      return null;
    }
    const digits = String(value).replace(/[^0-9]/g, "");
    return digits ? Number(digits) : null;
  }

  function parseQuantity(text) {
    const explicit = matchFirst(text, /数量[:：]?\s*([0-9]+)/) || matchFirst(text, /Qty[:：]?\s*([0-9]+)/i);
    if (explicit) {
      return Number(explicit);
    }
    return 1;
  }

  function asinFromUrl(url) {
    const m = String(url || "").match(/\/(?:dp|gp\/product|gp\/aw\/d)\/([A-Z0-9]{10})/i);
    return m ? m[1].toUpperCase() : "";
  }

  function matchFirst(text, regex) {
    const m = String(text || "").match(regex);
    return m ? m[1].trim() : "";
  }

  function cleanTitle(text) {
    return normalizeText(text)
      .replace(/^商品名[:：]\s*/, "")
      .replace(/\s*\|\s*Amazon.*$/i, "")
      .trim();
  }

  function normalizeText(text) {
    return String(text || "").replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim();
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function absoluteHref(link, pageUrl) {
    const raw = link?.getAttribute?.("href") || link?.href || "";
    if (!raw) {
      return "";
    }
    try {
      return new URL(raw, pageUrl || location.href).href;
    } catch (err) {
      return raw;
    }
  }

  function showCaptureOverlay(message, isError = false) {
    let box = document.getElementById("amazon-jp-orders-capture-status");
    if (!box) {
      box = document.createElement("div");
      box.id = "amazon-jp-orders-capture-status";
      box.style.position = "fixed";
      box.style.zIndex = "2147483647";
      box.style.top = "14px";
      box.style.right = "14px";
      box.style.maxWidth = "360px";
      box.style.padding = "12px 14px";
      box.style.border = "1px solid #d5cdbc";
      box.style.borderRadius = "8px";
      box.style.background = "#fffdf7";
      box.style.boxShadow = "0 8px 28px rgba(0,0,0,.18)";
      box.style.color = "#202124";
      box.style.font = "13px/1.45 'Yu Gothic UI', Meiryo, sans-serif";
      box.style.whiteSpace = "pre-wrap";
      document.documentElement.appendChild(box);
    }
    box.style.borderColor = isError ? "#b54708" : "#1f5e45";
    box.textContent = `Amazon JP Orders\n${message}`;
  }
}
