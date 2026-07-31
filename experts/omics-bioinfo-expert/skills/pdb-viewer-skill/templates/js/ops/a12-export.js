// ========================================================================
// ops/a12-export.js — 导出/截图/场景快照/保存 PDB
// 负责：opScreenshot、opExportSelection、opExportFiltered、opSaveScene、
//       opLoadScene、opSavePdb；以及 showSaveDialog、closeSaveDialog、
//       window.confirmSave、doSavePdb
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

async function opScreenshot(ctx, p, op) {
  var isTransparent = (op === 'screenshot_transparent');
  var ssWidth = parseInt(p.width || 0);
  var ssHeight = parseInt(p.height || 0);
  var serverFilename = p.filename || null;  // 若指定，则同时 POST 到服务端保存
  var serverSaveDir = p.save_dir || '/tmp/pdb-verify-screenshots';  // 服务端保存目录
  log('screenshot' + (isTransparent ? '_transparent' : '') + (ssWidth ? ' ' + ssWidth + 'x' + ssHeight : ''));
  try {
    var canvas3d = ctx.plugin.canvas3d;
    if (!canvas3d || !canvas3d.webgl || !canvas3d.webgl.gl) { log('截图: canvas3d 不可用', 'warn'); return; }

    var origBg = null;
    if (isTransparent) {
      origBg = canvas3d.props.renderer && canvas3d.props.renderer.backgroundColor;
      canvas3d.setProps({ renderer: { backgroundColor: 0x00000000 } });
      await new Promise(function(r) { setTimeout(r, 100); });
    }

    var gl = canvas3d.webgl.gl;
    var c = gl.canvas;

    // ★ A12-4 修复：自定义分辨率截图（实际 resize canvas + 强制重渲染）
    var origW = 0, origH = 0;
    if (ssWidth > 0 && ssHeight > 0) {
      origW = c.width;
      origH = c.height;
      c.width = ssWidth;
      c.height = ssHeight;
      // 通知 Mol* canvas 尺寸改变
      try {
        if (canvas3d.handleResize) {
          canvas3d.handleResize();
        } else if (canvas3d.webgl && canvas3d.webgl.setSize) {
          canvas3d.webgl.setSize(ssWidth, ssHeight);
        }
        canvas3d.requestCameraReset && canvas3d.requestCameraReset();
      } catch(rse) { log('resize 通知失败(非致命): ' + rse.message, 'warn'); }
      // 等待 3 帧渲染完成
      await new Promise(function(r) { requestAnimationFrame(function() { requestAnimationFrame(function() { requestAnimationFrame(r); }); }); });
    }

    var imgData = c.toDataURL('image/png');

    // 恢复原始尺寸
    if (origW > 0) {
      c.width = origW;
      c.height = origH;
      try {
        if (canvas3d.handleResize) canvas3d.handleResize();
        else if (canvas3d.webgl && canvas3d.webgl.setSize) canvas3d.webgl.setSize(origW, origH);
        canvas3d.requestCameraReset && canvas3d.requestCameraReset();
      } catch(rse2) {}
      await new Promise(function(r) { requestAnimationFrame(r); });
    }

    if (isTransparent && origBg !== null) {
      canvas3d.setProps({ renderer: { backgroundColor: origBg } });
    }

    var a = document.createElement('a');
    a.href = imgData;
    a.download = (ctx.pdbName || 'structure') + (isTransparent ? '_transparent' : '') + (ssWidth ? '_' + ssWidth + 'x' + ssHeight : '') + '_screenshot.png';
    a.click();

    // ★ 同时 POST 到服务端保存（验证用，filename 参数指定时）
    if (serverFilename) {
      try {
        await fetch('/api/screenshot-save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data: imgData, filename: serverFilename, save_dir: serverSaveDir })
        });
        log('✓ 截图已发送至服务端: ' + serverFilename + ' → ' + serverSaveDir);
      } catch(se) { log('截图服务端保存失败: ' + se.message, 'warn'); }
    }

    log('✓ 截图已保存' + (ssWidth ? ' (' + ssWidth + 'x' + ssHeight + ')' : ''));
    setStatus('✓ 截图已保存', 'ok');
    hideStatus();
  } catch(e) { log('screenshot 失败: ' + e.message, 'error'); }
}

async function opExportSelection(ctx, p) {
  var esPath = p.path || ('/tmp/' + (ctx.pdbName || 'selection').replace('.pdb','') + '_selection.pdb');
  log('export_selection → ' + esPath);
  try {
    var esResp = await fetch('/api/export-pdb', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: esPath, action: 'selection', source: ctx.pdbPath })
    });
    var esResult = await esResp.json();
    if (esResult.ok) {
      log('✓ 已导出: ' + esResult.saved);
      setStatus('✓ 已导出: ' + esResult.saved, 'ok');
    } else {
      log('export_selection 失败: ' + esResult.error, 'error');
      setStatus('导出失败: ' + esResult.error, 'error');
    }
    hideStatus();
  } catch(e) { log('export_selection 失败: ' + e.message, 'error'); }
}

async function opExportFiltered(ctx, p) {
  var efPath = p.path || ('/tmp/' + (ctx.pdbName || 'filtered').replace('.pdb','') + '_filtered.pdb');
  log('export_filtered → ' + efPath);
  try {
    var efBody = {
      path: efPath,
      action: 'filter',
      source: ctx.pdbPath,
      remove: p.remove || [],
      keep_chains: p.keep_chains || null,
      keep_altloc: p.keep_altloc || null,
    };
    var efResp = await fetch('/api/export-pdb', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(efBody)
    });
    var efResult = await efResp.json();
    if (efResult.ok) {
      log('✓ 已导出过滤结构: ' + efResult.saved + '（移除 ' + (efResult.removed_count || 0) + ' 条）');
      setStatus('✓ 已导出: ' + efResult.saved, 'ok');
    } else {
      log('export_filtered 失败: ' + efResult.error, 'error');
      setStatus('导出失败: ' + efResult.error, 'error');
    }
    hideStatus();
  } catch(e) { log('export_filtered 失败: ' + e.message, 'error'); }
}

async function opSaveScene(ctx, p) {
  var ssName = p.name || 'scene_01';
  log('save_scene: ' + ssName);
  try {
    // 序列化当前场景：表示方式、着色、视角、高亮
    var sceneSnapshot = {
      pdbName: ctx.pdbName,
      pdbPath: ctx.pdbPath,
      chainVisibility: Object.assign({}, ctx.chainVisibility),
      waterHidden: ctx.waterHidden,
      highlights: ctx.highlights.map(function(h) {
        return { chain: h.chain, residues: h.residues };
      }),
      viewSnapshot: (window.__pdbViewSnapshots && window.__pdbViewSnapshots[ssName]) || null,
    };
    if (!window.__pdbSceneSnapshots) window.__pdbSceneSnapshots = {};
    window.__pdbSceneSnapshots[ssName] = sceneSnapshot;
    // 同时保存视角
    await executeOp({ op: 'save_view', params: { name: ssName } });
    sceneSnapshot.viewSnapshot = (window.__pdbViewSnapshots || {})[ssName];
    window.__pdbSceneSnapshots[ssName] = sceneSnapshot;
    log('✓ 场景已保存: ' + ssName);
    setStatus('✓ 场景已保存: ' + ssName, 'ok');
    hideStatus();
  } catch(e) { log('save_scene 失败: ' + e.message, 'error'); }
}

async function opLoadScene(ctx, p) {
  var lsName = p.name || 'scene_01';
  log('load_scene: ' + lsName);
  try {
    var lsSnapshots = window.__pdbSceneSnapshots || {};
    var lsSnap = lsSnapshots[lsName];
    if (!lsSnap) {
      log('load_scene: 未找到快照 ' + lsName, 'warn');
      setStatus('⚠ 未找到场景快照: ' + lsName, 'ok');
      return;
    }
    // 恢复视角
    if (lsSnap.viewSnapshot) {
      if (!window.__pdbViewSnapshots) window.__pdbViewSnapshots = {};
      window.__pdbViewSnapshots[lsName] = lsSnap.viewSnapshot;
      await executeOp({ op: 'restore_view', params: { name: lsName } });
    }
    // 恢复水分子状态
    if (lsSnap.waterHidden !== undefined) {
      await executeOp({ op: 'set_water', params: { visible: !lsSnap.waterHidden } });
    }
    log('✓ 场景已恢复: ' + lsName);
    setStatus('✓ 场景已恢复: ' + lsName, 'ok');
    hideStatus();
  } catch(e) { log('load_scene 失败: ' + e.message, 'error'); }
}

async function opSavePdb(ctx, p) {
  if (p.path && window.__pdbCtx) {
    window.__pdbCtx._userSavePath = p.path;
    log('保存路径已设置: ' + p.path);
  }
  if (p.confirm_required) {
    showSaveDialog();
  } else if (p.confirmed) {
    await doSavePdb();
  }
}

// ---- 保存 PDB 流程（对话框 + 实际保存）----

function showSaveDialog() {
  var dialog = document.getElementById('save-dialog');
  var msgEl = document.getElementById('save-dialog-msg');
  if (msgEl && window.__pdbCtx) {
    msgEl.textContent = '此操作将覆盖原始 PDB 文件: ' +
      (window.__pdbCtx.pdbName || '未知文件') +
      '\n此操作不可撤销，建议先使用"导出"保存副本。是否继续？';
  }
  if (dialog) dialog.classList.add('visible');
}

function closeSaveDialog() {
  var dialog = document.getElementById('save-dialog');
  if (dialog) dialog.classList.remove('visible');
}

window.closeSaveDialog = closeSaveDialog;

window.confirmSave = async function() {
  closeSaveDialog();
  await doSavePdb();
};

async function doSavePdb() {
  log('开始保存 PDB…');
  setStatus('正在保存…', 'loading');
  try {
    var ctx = window.__pdbCtx;
    if (!ctx) { log('保存失败: 无结构上下文', 'error'); return; }

    var savePath = ctx._userSavePath || ctx.pdbPath;
    if (!savePath) {
      log('❌ 保存失败: 未指定保存路径', 'error');
      setStatus('保存失败: 请提供保存路径 (path 参数)', 'error');
      return;
    }

    log('保存到: ' + savePath);

    var resp = await fetch('/api/save-pdb', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: savePath,
        name: ctx.pdbName,
        action: 'backup',
        create_if_missing: !ctx.pdbPath
      })
    });
    var result = await resp.json();
    if (result.ok) {
      log('✓ 已保存: ' + (result.saved || result.backup_path));
      setStatus('✓ 保存成功: ' + (result.saved || result.backup_path), 'ok');
    } else {
      log('保存失败: ' + result.error, 'error');
      setStatus('保存失败: ' + result.error, 'error');
    }
  } catch(e) {
    log('保存失败: ' + e.message, 'error');
    setStatus('保存失败: ' + e.message, 'error');
  }
}
