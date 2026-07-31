// ========================================================================
// ops/a1-load.js — 加载/切换 PDB 结构
// 负责：opGetPdb（case 'get_pdb'）
// 依赖：utils.js（log, setStatus, hideStatus, guessFormat）、loader.js（loadStructure）
// ========================================================================

async function opGetPdb(ctx, p) {
  var pdbId = p.id || p.pdb || '';
  var pdbUrl = p.url || '';
  log('get_pdb: id=' + pdbId + ' url=' + pdbUrl);
  setStatus('正在加载 ' + (pdbId || pdbUrl) + '…', 'loading');

  // 构建 fetch URL，并记录是否需要 base64 解码
  var fetchUrl;
  var isProxied2 = false;
  var serverPath2 = null;
  if (pdbUrl) {
    if (pdbUrl.indexOf('cos://') === 0) {
      // cos:// 协议 → 通过 /__cos 代理（omics 认证 + GetObjectData）
      fetchUrl = '/__cos?uri=' + encodeURIComponent(pdbUrl);
      isProxied2 = true;
    } else if (pdbUrl.indexOf('/__file?path=') === 0 || pdbUrl.indexOf('/__cos?uri=') === 0) {
      // 已是代理 URL 格式（如 /api/pdb-url 返回的内容），直接使用
      fetchUrl = pdbUrl;
      isProxied2 = true;
      var pathMatch2 = pdbUrl.match(/\/__file\?path=(.+)/);
      if (pathMatch2) serverPath2 = decodeURIComponent(pathMatch2[1]);
    } else if (pdbUrl.indexOf('/') === 0) {
      // 绝对服务器路径 → 通过 /__file 代理
      fetchUrl = '/__file?path=' + encodeURIComponent(pdbUrl);
      isProxied2 = true;
      serverPath2 = pdbUrl;
    } else {
      // 相对路径或完整 HTTP URL → 直接 fetch（纯文本 PDB）
      fetchUrl = pdbUrl;
      isProxied2 = false;
    }
  } else if (pdbId) {
    // 从 RCSB PDB 下载（直接文本，无需 base64）
    fetchUrl = 'https://files.rcsb.org/download/' + pdbId.toUpperCase() + '.pdb';
    isProxied2 = false;
  } else {
    log('get_pdb: 缺少 id 或 url 参数', 'error');
    return;
  }

  try {
    var resp = await fetch(fetchUrl);
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    var pdbText;
    var name2 = pdbId ? pdbId.toLowerCase() + '.pdb' : (pdbUrl.split('/').pop().split('?')[0] || 'structure.pdb');
    if (isProxied2) {
      // 代理路由返回 JSON: { data: base64, name: str, path: str }
      var obj2 = await resp.json();
      if (obj2.error) throw new Error(obj2.error);
      pdbText = atob(obj2.data);
      name2 = obj2.name || name2;
      serverPath2 = obj2.path || serverPath2;
    } else {
      pdbText = await resp.text();
    }
    var fmt = guessFormat(name2);

    // 清除旧结构（如果有）
    if (ctx && ctx.plugin) {
      try {
        var oldUpd = ctx.plugin.build();
        if (ctx.components.polymer) oldUpd.delete(ctx.components.polymer.ref);
        if (ctx.components.ligand) oldUpd.delete(ctx.components.ligand.ref);
        if (ctx.components.water) oldUpd.delete(ctx.components.water.ref);
        if (ctx.structure) oldUpd.delete(ctx.structure.ref);
        await oldUpd.commit();
      } catch(e) { log('清除旧结构失败: ' + e.message, 'warn'); }
    }

    await loadStructure(window.__molPlugin, pdbText, fmt, name2, serverPath2);
    setStatus('✓ 已加载: ' + name2, 'ok');
  } catch(e) {
    log('get_pdb 失败: ' + e.message, 'error');
    setStatus('加载失败: ' + e.message, 'error');
  }
  hideStatus();
}
