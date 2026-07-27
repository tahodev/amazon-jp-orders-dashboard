from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .classify import CATEGORIES
from .db import OrdersDB

PALETTE = {
    "食品饮料": "#2f7d57",
    "儿童": "#2b6fbb",
    "美妆护肤": "#b65a8d",
    "药品日用品": "#9a6a2f",
    "其他": "#6f7785",
}


def build_dashboard(db: OrdersDB) -> Path:
    data = db.summary()
    csv_paths = db.export_csv()
    html_text = render_dashboard(data, csv_paths)
    db.paths.dashboard_path.write_text(html_text, encoding="utf-8")
    return db.paths.dashboard_path


def render_dashboard(data: dict[str, Any], csv_paths: dict[str, Path]) -> str:
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    total = sum(int(row.get("total_yen") or 0) for row in data["categories"])
    items = sum(int(row.get("item_count") or 0) for row in data["categories"])
    months = len(data["monthly"])
    monthly_chart = _monthly_chart(data)
    category_chart = _category_chart(data["categories"])
    item_rows = "".join(_item_row(row) for row in data["recent_items"])
    run_rows = "".join(_run_row(row) for row in data["runs"])
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    years = sorted({int(row.get("year") or 0) for row in data["monthly"] if int(row.get("year") or 0)})
    orders_csv = html.escape(csv_paths["orders"].name)
    items_csv = html.escape(csv_paths["items"].name)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Amazon JP Orders Dashboard</title>
  <style>
    :root {{
      --bg: #f6f4ee;
      --panel: #fffdf7;
      --ink: #202124;
      --muted: #676b73;
      --line: #ded9cb;
      --accent: #1f5e45;
      --warn: #a45b1b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Yu Gothic UI", "Meiryo", "Microsoft YaHei", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.5;
    }}
    header {{
      padding: 28px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: #fbfaf5;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }}
    main {{ padding: 22px 32px 36px; max-width: 1420px; margin: 0 auto; }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 12px;
      margin: 18px 0 20px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
    }}
    .stat .label {{ color: var(--muted); font-size: 12px; }}
    .stat .value {{ margin-top: 4px; font-size: 24px; font-weight: 700; }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(320px, .65fr);
      gap: 16px;
      align-items: start;
    }}
    section {{
      margin-bottom: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .chart {{ width: 100%; overflow-x: auto; }}
    .bar-label {{ font-size: 12px; fill: #3f4248; }}
    .axis {{ stroke: #c9c2b4; stroke-width: 1; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 9px 8px; border-bottom: 1px solid #e8e3d7; vertical-align: top; }}
    th {{ color: var(--muted); text-align: left; font-weight: 600; white-space: nowrap; }}
    td.money, th.money {{ text-align: right; white-space: nowrap; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid #d9d1c2;
      border-radius: 999px;
      padding: 2px 8px;
      white-space: nowrap;
      background: #fffaf0;
    }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
    .toolbar {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-bottom: 12px;
    }}
    input, select {{
      height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 10px;
      background: #fff;
      color: var(--ink);
      min-width: 180px;
    }}
    .small {{ color: var(--muted); font-size: 12px; }}
    .yearbar {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }}
    .yearbar select {{ min-width: 130px; }}
    .pager {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 12px;
    }}
    .pager button {{
      min-width: 34px;
      height: 30px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      cursor: pointer;
    }}
    .pager button:disabled {{ opacity: .45; cursor: default; }}
    .category-edit {{
      min-width: 118px;
      height: 28px;
      padding: 0 8px;
      border-radius: 999px;
      font-size: 12px;
    }}
    .status {{
      min-width: 120px;
      color: var(--muted);
      font-size: 12px;
    }}
    a {{ color: #075b9f; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    @media (max-width: 920px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .stats, .grid {{ grid-template-columns: 1fr; }}
      table {{ font-size: 12px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Amazon.co.jp 注文支出统计</h1>
    <div class="meta">Generated at {html.escape(generated_at)} · local-only dashboard · CSV: data/exports/{orders_csv} / data/exports/{items_csv}</div>
  </header>
  <main>
    <div class="yearbar">
      <label class="small" for="year">年份</label>
      <select id="year">
        <option value="">全部年份</option>
        {"".join(f'<option value="{year}">{year}</option>' for year in years)}
      </select>
    </div>
    <div class="stats">
      <div class="stat"><div class="label">抓取商品行</div><div class="value" id="statItems">{items}</div></div>
      <div class="stat"><div class="label">总金额</div><div class="value" id="statTotal">{_yen(total)}</div></div>
      <div class="stat"><div class="label">月份数</div><div class="value" id="statMonths">{months}</div></div>
      <div class="stat"><div class="label">分类</div><div class="value" id="statCategories">{len(CATEGORIES)}</div></div>
    </div>
    <div class="grid">
      <section>
        <h2>月度支出</h2>
        <div class="chart" id="monthlyChart">{monthly_chart}</div>
      </section>
      <section>
        <h2>分类占比</h2>
        <div class="chart" id="categoryChart">{category_chart}</div>
      </section>
    </div>
    <section>
      <h2>商品明细</h2>
      <div class="toolbar">
        <input id="q" type="search" placeholder="搜索商品 / 订单号">
        <select id="cat">
          <option value="">全部分类</option>
          {"".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in CATEGORIES)}
        </select>
        <span class="small" id="count"></span>
        <span class="status" id="saveStatus"></span>
      </div>
      <table id="items">
        <thead>
          <tr><th>日期</th><th>订单号</th><th>商品</th><th>分类</th><th class="money">金额</th><th class="money">数量</th><th>命中</th></tr>
        </thead>
        <tbody>{item_rows}</tbody>
      </table>
      <div class="pager">
        <button id="prevPage" type="button">‹</button>
        <span class="small" id="pageInfo"></span>
        <button id="nextPage" type="button">›</button>
      </div>
    </section>
    <section>
      <h2>抓取记录</h2>
      <table>
        <thead><tr><th>时间</th><th>范围</th><th class="money">订单</th><th class="money">商品行</th><th>来源</th></tr></thead>
        <tbody>{run_rows}</tbody>
      </table>
    </section>
  </main>
  <script id="dashboard-data" type="application/json">{payload}</script>
  <script>
    const data = JSON.parse(document.getElementById('dashboard-data').textContent);
    const year = document.getElementById('year');
    const q = document.getElementById('q');
    const cat = document.getElementById('cat');
    const count = document.getElementById('count');
    const pageInfo = document.getElementById('pageInfo');
    const saveStatus = document.getElementById('saveStatus');
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');
    const monthlyChart = document.getElementById('monthlyChart');
    const categoryChart = document.getElementById('categoryChart');
    const rows = Array.from(document.querySelectorAll('#items tbody tr'));
    const pageSize = 25;
    let currentPage = 1;
    function applyFilter() {{
      const needle = q.value.trim().toLowerCase();
      const category = cat.value;
      const selectedYear = year.value;
      const matched = [];
      for (const row of rows) {{
        const text = row.innerText.toLowerCase();
        const okText = !needle || text.includes(needle);
        const okCat = !category || row.dataset.category === category;
        const okYear = !selectedYear || row.dataset.year === selectedYear;
        const ok = okText && okCat && okYear;
        if (ok) matched.push(row);
        row.style.display = 'none';
      }}
      const maxPage = Math.max(1, Math.ceil(matched.length / pageSize));
      if (currentPage > maxPage) currentPage = maxPage;
      const start = (currentPage - 1) * pageSize;
      for (const row of matched.slice(start, start + pageSize)) {{
        row.style.display = '';
      }}
      count.textContent = `${{matched.length}} / ${{rows.length}} 行`;
      pageInfo.textContent = `${{currentPage}} / ${{maxPage}}`;
      prevPage.disabled = currentPage <= 1;
      nextPage.disabled = currentPage >= maxPage;
      renderSummary(selectedYear);
    }}
    function yen(value) {{
      return '¥' + Math.round(value || 0).toLocaleString('ja-JP');
    }}
    function shortYen(value) {{
      value = Math.round(value || 0);
      return value >= 10000 ? (value / 10000).toFixed(1) + '万' : value.toLocaleString('ja-JP');
    }}
    function inYear(row, selectedYear) {{
      return !selectedYear || String(row.year) === selectedYear;
    }}
    function renderSummary(selectedYear) {{
      const monthly = data.monthly.filter(row => inYear(row, selectedYear));
      const catRows = data.category_monthly.filter(row => inYear(row, selectedYear));
      const itemsForYear = data.recent_items.filter(row => inYear(row, selectedYear));
      const total = catRows.reduce((sum, row) => sum + Number(row.total_yen || 0), 0);
      const categories = new Map();
      for (const row of catRows) {{
        const key = row.category || '其他';
        const prev = categories.get(key) || {{ category: key, total_yen: 0, item_count: 0 }};
        prev.total_yen += Number(row.total_yen || 0);
        prev.item_count += Number(row.item_count || 0);
        categories.set(key, prev);
      }}
      document.getElementById('statItems').textContent = itemsForYear.length;
      document.getElementById('statTotal').textContent = yen(total);
      document.getElementById('statMonths').textContent = monthly.length;
      document.getElementById('statCategories').textContent = {len(CATEGORIES)};
      renderMonthly(catRows);
      renderCategories(Array.from(categories.values()), total);
    }}
    function renderMonthly(catRows) {{
      const labels = Array.from(new Set(catRows.map(row => `${{row.year}}-${{String(row.month).padStart(2, '0')}}`))).sort();
      if (!labels.length) {{
        monthlyChart.innerHTML = '<div class="small">没有该年份的数据。</div>';
        return;
      }}
      const palette = {json.dumps(PALETTE, ensure_ascii=False)};
      const totals = Object.fromEntries(labels.map(label => [label, catRows.filter(row => `${{row.year}}-${{String(row.month).padStart(2, '0')}}` === label).reduce((sum, row) => sum + Number(row.total_yen || 0), 0)]));
      const maxTotal = Math.max(...Object.values(totals), 1);
      const width = Math.max(760, labels.length * 96);
      const height = 300, left = 54, bottom = 48, top = 20, chartH = height - top - bottom;
      const step = (width - left - 28) / Math.max(labels.length, 1);
      const barW = Math.min(54, step * 0.62);
      let svg = `<svg viewBox="0 0 ${{width}} ${{height}}" width="${{width}}" height="${{height}}" role="img">`;
      svg += `<line class="axis" x1="${{left}}" y1="${{height-bottom}}" x2="${{width-16}}" y2="${{height-bottom}}"/>`;
      labels.forEach((label, i) => {{
        const x = left + i * step + (step - barW) / 2;
        let y = height - bottom;
        for (const category of {json.dumps(CATEGORIES, ensure_ascii=False)}) {{
          const amount = catRows.filter(row => `${{row.year}}-${{String(row.month).padStart(2, '0')}}` === label && row.category === category).reduce((sum, row) => sum + Number(row.total_yen || 0), 0);
          if (amount <= 0) continue;
          const h = Math.max(2, amount / maxTotal * chartH);
          y -= h;
          svg += `<rect x="${{x.toFixed(1)}}" y="${{y.toFixed(1)}}" width="${{barW.toFixed(1)}}" height="${{h.toFixed(1)}}" fill="${{palette[category] || palette['其他']}}"><title>${{label}} ${{category}} ${{yen(amount)}}</title></rect>`;
        }}
        svg += `<text class="bar-label" x="${{(x + barW / 2).toFixed(1)}}" y="${{height-22}}" text-anchor="middle">${{label.slice(5)}}</text>`;
        svg += `<text class="bar-label" x="${{(x + barW / 2).toFixed(1)}}" y="${{Math.max(14, y-5).toFixed(1)}}" text-anchor="middle">${{shortYen(totals[label])}}</text>`;
      }});
      svg += '</svg>';
      monthlyChart.innerHTML = svg;
    }}
    function renderCategories(rows, total) {{
      if (!total) {{
        categoryChart.innerHTML = '<div class="small">没有该年份的数据。</div>';
        return;
      }}
      const palette = {json.dumps(PALETTE, ensure_ascii=False)};
      rows.sort((a, b) => b.total_yen - a.total_yen);
      categoryChart.innerHTML = rows.map(row => {{
        const pct = row.total_yen / total * 100;
        return `<div style="margin-bottom:10px">
          <div class="small" style="display:flex;justify-content:space-between;gap:12px">
            <span>${{row.category}} · ${{yen(row.total_yen)}} · ${{pct.toFixed(1)}}%</span>
            <span>${{row.item_count}} 件</span>
          </div>
          <div style="height:12px;background:#eee7da;border-radius:999px;overflow:hidden">
            <div style="width:${{pct.toFixed(2)}}%;height:100%;background:${{palette[row.category] || palette['其他']}}"></div>
          </div>
        </div>`;
      }}).join('');
    }}
    function resetAndFilter() {{ currentPage = 1; applyFilter(); }}
    year.addEventListener('change', resetAndFilter);
    q.addEventListener('input', resetAndFilter);
    cat.addEventListener('change', resetAndFilter);
    prevPage.addEventListener('click', () => {{ currentPage -= 1; applyFilter(); }});
    nextPage.addEventListener('click', () => {{ currentPage += 1; applyFilter(); }});
    document.querySelectorAll('.category-edit').forEach(select => {{
      select.addEventListener('change', async () => {{
        const row = select.closest('tr');
        const itemId = Number(row.dataset.itemId || 0);
        const category = select.value;
        saveStatus.textContent = '保存分类...';
        select.disabled = true;
        try {{
          const res = await fetch('/api/item-category', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ item_id: itemId, category, remember: true }})
          }});
          const data = await res.json();
          if (!data.ok) throw new Error(data.error || 'save failed');
          saveStatus.textContent = `已保存，同名商品更新 ${{data.affected_rows || 1}} 行`;
          setTimeout(() => location.reload(), 650);
        }} catch (err) {{
          saveStatus.textContent = `保存失败: ${{err.message || err}}`;
          select.disabled = false;
        }}
      }});
    }});
    applyFilter();
  </script>
</body>
</html>
"""


def _monthly_chart(data: dict[str, Any]) -> str:
    rows = data["category_monthly"]
    labels = sorted({f"{int(r['year'])}-{int(r['month']):02d}" for r in rows})
    if not labels:
        return "<div class='small'>还没有数据。先启动接收器并用 Chrome 扩展抓取注文履歴。</div>"
    totals = {
        label: sum(int(r.get("total_yen") or 0) for r in rows if f"{int(r['year'])}-{int(r['month']):02d}" == label)
        for label in labels
    }
    max_total = max(max(totals.values()), 1)
    width = max(760, len(labels) * 96)
    height = 300
    left = 54
    bottom = 48
    top = 20
    chart_h = height - top - bottom
    step = (width - left - 28) / max(len(labels), 1)
    bar_w = min(54, step * 0.62)
    parts = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img">']
    parts.append(f'<line class="axis" x1="{left}" y1="{height-bottom}" x2="{width-16}" y2="{height-bottom}"/>')
    for i, label in enumerate(labels):
        x = left + i * step + (step - bar_w) / 2
        y_base = height - bottom
        y = y_base
        for category in CATEGORIES:
            amount = sum(
                int(r.get("total_yen") or 0)
                for r in rows
                if f"{int(r['year'])}-{int(r['month']):02d}" == label and r.get("category") == category
            )
            if amount <= 0:
                continue
            h = max(2, amount / max_total * chart_h)
            y -= h
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{PALETTE[category]}">'
                f'<title>{html.escape(label)} {html.escape(category)} {_yen(amount)}</title></rect>'
            )
        parts.append(f'<text class="bar-label" x="{x + bar_w / 2:.1f}" y="{height-22}" text-anchor="middle">{html.escape(label[5:])}</text>')
        parts.append(f'<text class="bar-label" x="{x + bar_w / 2:.1f}" y="{max(14, y-5):.1f}" text-anchor="middle">{html.escape(_short_yen(totals[label]))}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _category_chart(rows: list[dict[str, Any]]) -> str:
    total = sum(int(row.get("total_yen") or 0) for row in rows)
    if total <= 0:
        return "<div class='small'>还没有可汇总金额。</div>"
    bars = []
    for row in rows:
        category = str(row.get("category") or "其他")
        amount = int(row.get("total_yen") or 0)
        item_count = int(row.get("item_count") or 0)
        pct = amount / total * 100
        bars.append(
            f"""<div style="margin-bottom:10px">
              <div class="small" style="display:flex;justify-content:space-between;gap:12px">
                <span>{html.escape(category)} · {_yen(amount)} · {pct:.1f}%</span>
                <span>{item_count} 件</span>
              </div>
              <div style="height:12px;background:#eee7da;border-radius:999px;overflow:hidden">
                <div style="width:{pct:.2f}%;height:100%;background:{PALETTE.get(category, PALETTE['其他'])}"></div>
              </div>
            </div>"""
        )
    return "".join(bars)


def _item_row(row: dict[str, Any]) -> str:
    category = str(row.get("category") or "其他")
    title = html.escape(str(row.get("title") or ""))
    year = str(row.get("year") or "")
    item_id = int(row.get("id") or 0)
    options = "".join(
        f"<option value='{html.escape(cat)}' {'selected' if cat == category else ''}>{html.escape(cat)}</option>"
        for cat in CATEGORIES
    )
    return (
        f"<tr data-item-id='{item_id}' data-category='{html.escape(category)}' data-year='{html.escape(year)}'>"
        f"<td>{html.escape(str(row.get('order_date') or ''))}</td>"
        f"<td>{html.escape(str(row.get('order_id') or ''))}</td>"
        f"<td>{title}</td>"
        f"<td><select class='category-edit'>{options}</select></td>"
        f"<td class='money'>{_yen(row.get('item_total_yen'))}</td>"
        f"<td class='money'>{int(row.get('quantity') or 1)}</td>"
        f"<td>{html.escape(str(row.get('matched_keyword') or ''))}</td>"
        "</tr>"
    )


def _run_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html.escape(str(row.get('captured_at') or ''))}</td>"
        f"<td>{html.escape(str(row.get('since_date') or ''))}</td>"
        f"<td class='money'>{int(row.get('order_count') or 0)}</td>"
        f"<td class='money'>{int(row.get('item_count') or 0)}</td>"
        f"<td>{html.escape(str(row.get('source_url') or ''))}</td>"
        "</tr>"
    )


def _yen(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return "¥" + f"{int(value):,}"
    except (TypeError, ValueError, OverflowError):
        return "-"


def _short_yen(value: int) -> str:
    if value >= 10000:
        return f"{value / 10000:.1f}万"
    return f"{value:,}"
