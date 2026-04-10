"""
A股策略选股系统 - Web 可视化界面
用法: python web.py [--port 8080]
"""
import sys
import os
import json
import argparse
import logging
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, Response
from scanner import StockScanner, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

_cache = {"results": None, "timestamp": None, "config": None}

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股策略选股系统</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0f1117;--card:#1a1d2e;--border:#2a2d3e;--text:#e1e4ed;--text2:#8b8fa3;--accent:#6366f1;--accent2:#818cf8;--green:#10b981;--red:#ef4444;--yellow:#f59e0b;--hover:#252840}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.header{background:var(--card);border-bottom:1px solid var(--border);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.header h1{font-size:20px;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header .meta{color:var(--text2);font-size:13px}
.layout{display:flex;min-height:calc(100vh - 57px)}
.sidebar{width:260px;background:var(--card);border-right:1px solid var(--border);padding:20px;overflow-y:auto;flex-shrink:0}
.main{flex:1;padding:20px;overflow-x:auto}
.section-title{font-size:13px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px}
select{width:100%;padding:8px 12px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:6px;font-size:14px;cursor:pointer;outline:none}
select:focus{border-color:var(--accent)}
.strat-list{display:flex;flex-direction:column;gap:8px;margin-bottom:20px}
.strat-item{display:flex;align-items:center;gap:10px;padding:8px 10px;background:var(--bg);border-radius:6px;cursor:pointer;border:1px solid transparent;transition:all .2s}
.strat-item:hover{border-color:var(--border)}
.strat-item.active{border-color:var(--accent);background:rgba(99,102,241,.1)}
.strat-item input{display:none}
.strat-item .check{width:18px;height:18px;border:2px solid var(--border);border-radius:4px;display:flex;align-items:center;justify-content:center;transition:all .2s;flex-shrink:0}
.strat-item.active .check{background:var(--accent);border-color:var(--accent)}
.strat-item.active .check::after{content:'✓';color:#fff;font-size:12px}
.strat-item .name{font-size:14px}
.btn{width:100%;padding:10px;background:var(--accent);color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;transition:all .2s;margin-top:12px}
.btn:hover{background:var(--accent2);transform:translateY(-1px)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text)}
.btn-outline:hover{border-color:var(--accent);color:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;text-align:center}
.stat-card .val{font-size:28px;font-weight:700;color:var(--accent)}
.stat-card .label{font-size:12px;color:var(--text2);margin-top:4px}
.table-wrap{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden}
table{width:100%;border-collapse:collapse}
th{background:var(--bg);padding:12px 16px;text-align:left;font-size:13px;font-weight:600;color:var(--text2);border-bottom:1px solid var(--border);white-space:nowrap;position:sticky;top:0}
td{padding:12px 16px;border-bottom:1px solid var(--border);font-size:14px;white-space:nowrap}
tr:hover{background:var(--hover);cursor:pointer}
tr:last-child td{border-bottom:none}
.tag{display:inline-block;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:500;margin:2px}
.tag-green{background:rgba(16,185,129,.15);color:var(--green)}
.tag-blue{background:rgba(99,102,241,.15);color:var(--accent2)}
.tag-yellow{background:rgba(245,158,11,.15);color:var(--yellow)}
.score-bar{display:flex;align-items:center;gap:8px}
.score-bar .bar{flex:1;height:6px;background:var(--bg);border-radius:3px;overflow:hidden}
.score-bar .fill{height:100%;border-radius:3px;transition:width .5s}
.pct-up{color:var(--green)}
.pct-down{color:var(--red)}
.empty{text-align:center;padding:60px 20px;color:var(--text2)}
.empty .icon{font-size:48px;margin-bottom:12px}
.loading{display:none;text-align:center;padding:40px}
.loading.show{display:block}
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}

/* Modal */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:200;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:14px;width:90%;max-width:900px;max-height:90vh;overflow-y:auto;padding:24px}
.modal-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.modal-header h2{font-size:18px}
.modal-close{background:none;border:none;color:var(--text2);font-size:24px;cursor:pointer;padding:4px 8px;border-radius:4px}
.modal-close:hover{background:var(--bg);color:var(--text)}
.chart-tabs{display:flex;gap:4px;margin-bottom:16px}
.chart-tab{padding:6px 14px;border-radius:6px;font-size:13px;cursor:pointer;border:1px solid var(--border);background:transparent;color:var(--text2);transition:all .2s}
.chart-tab.active{background:var(--accent);border-color:var(--accent);color:#fff}
.chart-container{position:relative;height:400px}
.chart-container canvas{width:100%!important}
@media(max-width:768px){.sidebar{width:200px}.stats{grid-template-columns:repeat(2,1fr)}}
@media(max-width:600px){.layout{flex-direction:column}.sidebar{width:100%;border-right:none;border-bottom:1px solid var(--border)}}
</style>
</head>
<body>
<div class="header">
  <h1>📊 A股策略选股系统 v1.0.5</h1>
  <div class="meta" id="metaInfo">就绪</div>
</div>
<div class="layout">
  <div class="sidebar">
    <div style="margin-bottom:20px">
      <div class="section-title">股票池</div>
      <select id="poolSelect">
        <option value="all">全市场 (5000+)</option>
        <option value="hs300">沪深300 (300只)</option>
        <option value="zz500">中证500 (500只)</option>
      </select>
    </div>
    <div style="margin-bottom:20px">
      <div class="section-title">组合模式</div>
      <select id="comboSelect">
        <option value="any">并集 (任一策略命中)</option>
        <option value="composite">交集 (全部策略命中)</option>
        <option value="single">单策略</option>
      </select>
    </div>
    <div>
      <div class="section-title">启用策略</div>
      <div class="strat-list" id="stratList"></div>
    </div>
    <button class="btn" id="scanBtn" onclick="startScan()">🚀 Start Scan</button>
    <button class="btn btn-outline" style="margin-top:8px" onclick="loadResults()">📋 Load Last Results</button>
  </div>
  <div class="main">
    <div class="stats" id="statsArea" style="display:none">
      <div class="stat-card"><div class="val" id="statCount">0</div><div class="label">符合条件</div></div>
      <div class="stat-card"><div class="val" id="statStrats">0</div><div class="label">命中策略</div></div>
      <div class="stat-card"><div class="val" id="statTime">-</div><div class="label">最近扫描</div></div>
    </div>
    <div class="loading" id="loading">
      <div class="spinner"></div>
      <div>正在扫描股票...首次扫描较慢，有缓存后秒出。</div>
    </div>
    <div id="tableArea">
      <div class="empty">
        <div class="icon">📈</div>
        <div>配置策略后点击"开始扫描"</div>
      </div>
    </div>
  </div>
</div>

<!-- K-line Modal -->
<div class="modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-header">
      <h2 id="modalTitle">K线图</h2>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="chart-tabs">
      <button class="chart-tab active" onclick="switchChart('price',this)">价格 + 均线</button>
      <button class="chart-tab" onclick="switchChart('macd',this)">MACD</button>
      <button class="chart-tab" onclick="switchChart('rsi',this)">RSI</button>
    </div>
    <div class="chart-container"><canvas id="mainChart"></canvas></div>
  </div>
</div>

<script>
const STRAT_NAMES = {
  ma_cross:'均线金叉', macd:'MACD信号',
  rsi:'RSI超买超卖', bollinger:'布林带',
  volume:'放量异动', trend:'多头排列',
  shrink_pullback:'缩量回踩', one_yang_three_yin:'一阳三阴',
  bottom_volume:'底部放量', box_oscillation:'箱体震荡',
  volume_breakout:'放量突破'
};
let chart = null, currentKlines = [], currentChartType = 'price';

async function init() {
  const cfg = await (await fetch('/api/config')).json();
  const list = document.getElementById('stratList');
  list.innerHTML = '';
  for (const [name, info] of Object.entries(cfg.strategies)) {
    const div = document.createElement('div');
    div.className = 'strat-item' + (info.enabled ? ' active' : '');
    div.dataset.name = name;
    div.innerHTML = `<div class="check"></div><div class="name">${STRAT_NAMES[name]||name}</div>`;
    div.onclick = () => div.classList.toggle('active');
    list.appendChild(div);
  }
  if (cfg.pool) document.getElementById('poolSelect').value = cfg.pool;
  if (cfg.combination) document.getElementById('comboSelect').value = cfg.combination;
  loadResults();
}

function getSelectedStrategies() {
  return [...document.querySelectorAll('.strat-item.active')].map(el => el.dataset.name);
}

async function startScan() {
  const btn = document.getElementById('scanBtn');
  btn.disabled = true; btn.textContent = '⏳ 扫描中...';
  document.getElementById('loading').classList.add('show');
  document.getElementById('tableArea').innerHTML = '';
  try {
    const res = await fetch('/api/scan', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        pool: document.getElementById('poolSelect').value,
        combination: document.getElementById('comboSelect').value,
        strategies: getSelectedStrategies(),
      })
    });
    const data = await res.json();
    if (data.success) renderResults(data);
    else alert('Scan failed: ' + (data.error||'Unknown error'));
  } catch(e) { alert('Request failed: ' + e.message); }
  btn.disabled = false; btn.textContent = '🚀 开始扫描';
  document.getElementById('loading').classList.remove('show');
}

async function loadResults() {
  const res = await (await fetch('/api/results')).json();
  if (res.results && res.results.length) renderResults({results:res.results, timestamp:res.timestamp, count:res.results.length});
}

function renderResults(data) {
  const {results, timestamp, count} = data;
  document.getElementById('statsArea').style.display = 'grid';
  document.getElementById('statCount').textContent = results.length;
  const strats = new Set();
  results.forEach(r => r.signals.forEach(s => strats.add(s.strategy)));
  document.getElementById('statStrats').textContent = strats.size;
  document.getElementById('statTime').textContent = timestamp || '-';
  document.getElementById('metaInfo').textContent = `Last scan: ${timestamp||'-'} | ${results.length} matched`;

  if (!results.length) {
    document.getElementById('tableArea').innerHTML = '<div class="empty"><div class="icon">🔍</div><div>未找到符合条件的股票</div></div>';
    return;
  }
  const maxScore = Math.max(...results.map(r => r.score), 1);
  let html = '<div class="table-wrap"><table><thead><tr><th>#</th><th>代码</th><th>名称</th><th>现价</th><th>涨跌%</th><th>信号</th><th>买入价</th><th>止损</th><th>目标价</th><th>风险</th><th>评分</th></tr></thead><tbody>';
  results.forEach((r, i) => {
    const pctClass = r.pct_chg >= 0 ? 'pct-up' : 'pct-down';
    const pctSign = r.pct_chg >= 0 ? '+' : '';
    const tags = r.signals.map(s => {
      const color = s.strength >= 4 ? 'tag-green' : s.strength >= 3 ? 'tag-blue' : 'tag-yellow';
      return `<span class="tag ${color}">${s.strategy}</span>`;
    }).join('');
    const barColor = r.score >= 12 ? 'var(--green)' : r.score >= 8 ? 'var(--accent)' : 'var(--yellow)';
    const barWidth = Math.round(r.score / maxScore * 100);
    const riskColors = {low:'var(--green)',medium:'var(--yellow)',high:'var(--red)'};
    const riskLabels = {low:'低',medium:'中',high:'高'};
    const buyP = r.buy_price ? r.buy_price.toFixed(2) : '-';
    const slP = r.stop_loss ? r.stop_loss.toFixed(2) : '-';
    const tpP = r.target_price ? r.target_price.toFixed(2) : '-';
    const riskTag = r.risk_level ? `<span style="color:${riskColors[r.risk_level]||'var(--text2)'}">${riskLabels[r.risk_level]||r.risk_level}</span>` : '-';
    html += `<tr onclick="openStock('${r.code}','${r.name}')">
      <td>${i+1}</td><td><b>${r.code}</b></td><td>${r.name}</td>
      <td>${r.close}</td><td class="${pctClass}">${pctSign}${r.pct_chg}%</td>
      <td>${tags}</td>
      <td>${buyP}</td><td>${slP}</td><td>${tpP}</td><td>${riskTag}</td>
      <td class="score-bar"><span>${r.score}</span><div class="bar"><div class="fill" style="width:${barWidth}%;background:${barColor}"></div></div></td>
    </tr>`;
  });
  html += '</tbody></table></div>';
  document.getElementById('tableArea').innerHTML = html;
}

async function openStock(code, name) {
  document.getElementById('modalTitle').textContent = `${code} ${name} - K-Line`;
  document.getElementById('modalOverlay').classList.add('show');
  const res = await (await fetch(`/api/stock/${code}`)).json();
  if (res.error) { alert(res.error); return; }
  currentKlines = res.klines;
  switchChart('price', document.querySelector('.chart-tab'));
}

function closeModal() { document.getElementById('modalOverlay').classList.remove('show'); }

function switchChart(type, btn) {
  document.querySelectorAll('.chart-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentChartType = type;
  renderChart(type);
}

function renderChart(type) {
  const kl = currentKlines;
  if (!kl.length) return;
  if (chart) chart.destroy();
  const ctx = document.getElementById('mainChart').getContext('2d');
  const labels = kl.map(k => k.date.slice(5));

  if (type === 'price') {
    chart = new Chart(ctx, {type:'line', data:{
      labels,
      datasets:[
        {label:'Close', data:kl.map(k=>k.close), borderColor:'#e1e4ed', borderWidth:1.5, pointRadius:0, tension:0.1},
        {label:'MA5', data:kl.map(k=>k.ma5), borderColor:'#f59e0b', borderWidth:1, pointRadius:0, borderDash:[4,2]},
        {label:'MA10', data:kl.map(k=>k.ma10), borderColor:'#6366f1', borderWidth:1, pointRadius:0, borderDash:[4,2]},
        {label:'MA20', data:kl.map(k=>k.ma20), borderColor:'#10b981', borderWidth:1, pointRadius:0, borderDash:[4,2]},
        {label:'MA60', data:kl.map(k=>k.ma60), borderColor:'#ef4444', borderWidth:1, pointRadius:0, borderDash:[4,2]},
      ]}, options:{responsive:true,maintainAspectRatio:false,interaction:{intersect:false,mode:'index'},
      plugins:{legend:{labels:{color:'#8b8fa3',font:{size:11}}}},scales:{x:{ticks:{color:'#8b8fa3',maxTicksLimit:12}},y:{ticks:{color:'#8b8fa3'}}}}
    });
  } else if (type === 'macd') {
    chart = new Chart(ctx, {type:'bar', data:{
      labels,
      datasets:[
        {label:'DIF', data:kl.map(k=>k.macd_dif), type:'line', borderColor:'#f59e0b', borderWidth:1.5, pointRadius:0, tension:0.1, yAxisID:'y'},
        {label:'DEA', data:kl.map(k=>k.macd_dea), type:'line', borderColor:'#6366f1', borderWidth:1.5, pointRadius:0, tension:0.1, yAxisID:'y'},
        {label:'Histogram', data:kl.map(k=>k.macd_hist), backgroundColor:kl.map(k=>(k.macd_hist||0)>=0?'rgba(16,185,129,.6)':'rgba(239,68,68,.6)'), borderWidth:0, yAxisID:'y'},
      ]}, options:{responsive:true,maintainAspectRatio:false,interaction:{intersect:false,mode:'index'},
      plugins:{legend:{labels:{color:'#8b8fa3',font:{size:11}}}},scales:{x:{ticks:{color:'#8b8fa3',maxTicksLimit:12}},y:{ticks:{color:'#8b8fa3'}}}}
    });
  } else if (type === 'rsi') {
    chart = new Chart(ctx, {type:'line', data:{
      labels,
      datasets:[
        {label:'RSI(14)', data:kl.map(k=>k.rsi), borderColor:'#818cf8', borderWidth:1.5, pointRadius:0, tension:0.1, fill:false},
        {label:'Overbought (70)', data:kl.map(()=>70), borderColor:'rgba(239,68,68,.4)', borderWidth:1, borderDash:[5,5], pointRadius:0},
        {label:'Oversold (30)', data:kl.map(()=>30), borderColor:'rgba(16,185,129,.4)', borderWidth:1, borderDash:[5,5], pointRadius:0},
      ]}, options:{responsive:true,maintainAspectRatio:false,interaction:{intersect:false,mode:'index'},
      plugins:{legend:{labels:{color:'#8b8fa3',font:{size:11}}}},scales:{x:{ticks:{color:'#8b8fa3',maxTicksLimit:12}},y:{min:0,max:100,ticks:{color:'#8b8fa3'}}}}
    });
  }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
init();
</script>
</body>
</html>"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    return parser.parse_args()


@app.route("/")
def index():
    return Response(HTML_PAGE, content_type="text/html; charset=utf-8")


@app.route("/api/config")
def api_config():
    config = load_config()
    return jsonify({
        "strategies": {k: {"enabled": v.get("enabled", False), "params": {pk: pv for pk, pv in v.items() if pk != "enabled"}}
                       for k, v in config.get("strategies", {}).items()},
        "pool": config.get("scan", {}).get("pool", "all"),
        "combination": config.get("combination", "any"),
    })


@app.route("/api/scan", methods=["POST"])
def api_scan():
    try:
        data = request.get_json(silent=True) or {}
        pool = data.get("pool")
        strategies = data.get("strategies")
        combination = data.get("combination")

        config = load_config()
        if pool:
            config["scan"]["pool"] = pool
        if combination:
            config["combination"] = combination
        if strategies:
            for name in config["strategies"]:
                config["strategies"][name]["enabled"] = name in strategies

        import tempfile, yaml
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8")
        yaml.dump(config, tmp, allow_unicode=True, default_flow_style=False)
        tmp.close()

        scanner = StockScanner(tmp.name)
        results = scanner.scan()
        os.unlink(tmp.name)

        _cache["results"] = results
        _cache["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _cache["config"] = {
            "pool": pool or config["scan"]["pool"],
            "strategies": [k for k, v in config["strategies"].items() if v.get("enabled")],
            "combination": combination or config["combination"],
        }

        return jsonify({
            "success": True,
            "count": len(results),
            "timestamp": _cache["timestamp"],
            "results": results,
        })
    except Exception as e:
        logger.exception("scan failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/results")
def api_results():
    return jsonify({
        "results": _cache["results"],
        "timestamp": _cache["timestamp"],
        "config": _cache["config"],
    })


@app.route("/api/stock/<code>")
def api_stock_detail(code):
    try:
        from data.fetcher import get_stock_history
        from utils.indicators import add_all_indicators

        days = int(request.args.get("days", 120))
        df = get_stock_history(code, days=days)
        if df.empty:
            return jsonify({"error": "No data"}), 404

        df = add_all_indicators(df)

        klines = []
        for _, row in df.iterrows():
            klines.append({
                "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"]),
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]) if row["volume"] == row["volume"] else 0,
                "ma5": round(float(row.get("MA5", 0)), 2) if row.get("MA5") == row.get("MA5") else None,
                "ma10": round(float(row.get("MA10", 0)), 2) if row.get("MA10") == row.get("MA10") else None,
                "ma20": round(float(row.get("MA20", 0)), 2) if row.get("MA20") == row.get("MA20") else None,
                "ma60": round(float(row.get("MA60", 0)), 2) if row.get("MA60") == row.get("MA60") else None,
                "macd_dif": round(float(row.get("MACD_DIF", 0)), 4) if row.get("MACD_DIF") == row.get("MACD_DIF") else None,
                "macd_dea": round(float(row.get("MACD_DEA", 0)), 4) if row.get("MACD_DEA") == row.get("MACD_DEA") else None,
                "macd_hist": round(float(row.get("MACD_HIST", 0)), 4) if row.get("MACD_HIST") == row.get("MACD_HIST") else None,
                "rsi": round(float(row.get("RSI", 0)), 2) if row.get("RSI") == row.get("RSI") else None,
            })

        return jsonify({"code": code, "klines": klines})
    except Exception as e:
        logger.exception(f"Failed to get {code}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/cache/clear", methods=["POST"])
def api_cache_clear():
    from data.fetcher import clear_cache
    clear_cache()
    return jsonify({"success": True, "message": "Cache cleared"})


if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Web UI: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
