// ========================================================================
// ops/a8-camera.js — 相机/视角控制
// 负责：opFocusChain、opFocusSelection、opResetView、opSpin、
//       opSaveView、opRestoreView、opSetProjection
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

async function opFocusChain(ctx, p) {
  var focusChain = (p.chain || 'A').toUpperCase();
  log('focus_chain: ' + focusChain);
  try {
    var fcPlugin = ctx.plugin;
    var fcStr = ctx.structure && ctx.structure.obj && ctx.structure.obj.data;
    if (!fcStr) { fcPlugin.canvas3d && fcPlugin.canvas3d.requestCameraReset(); return; }
    var SE_fc = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!SE_fc) { fcPlugin.canvas3d && fcPlugin.canvas3d.requestCameraReset(); return; }
    var fcUnits = fcStr.units;
    var fcUnitElements = [];
    for (var fcu = 0; fcu < fcUnits.length; fcu++) {
      var fcUnit = fcUnits[fcu];
      if (!fcUnit.model) continue;
      var fcH = fcUnit.model.atomicHierarchy;
      if (!fcH) continue;
      var fcAC = fcH.chains.auth_asym_id;
      var fcLC = fcH.chains.label_asym_id;
      var fcCASegs = fcH.chainAtomSegments;
      var fcMatchAtoms = [];
      for (var fcci = 0; fcci < fcAC.rowCount; fcci++) {
        if (fcAC.value(fcci) !== focusChain && fcLC.value(fcci) !== focusChain) continue;
        var fcAS = fcCASegs.offsets[fcci];
        var fcAE = fcCASegs.offsets[fcci + 1];
        for (var fcai = fcAS; fcai < fcAE; fcai++) fcMatchAtoms.push(fcai);
      }
      if (fcMatchAtoms.length > 0) {
        fcUnitElements.push({ unit: fcUnit, indices: { size: fcMatchAtoms.length, indices: new Int32Array(fcMatchAtoms) } });
      }
    }
    if (fcUnitElements.length > 0) {
      var fcLoci = SE_fc.Loci(fcStr, fcUnitElements);
      if (fcPlugin.managers.camera) fcPlugin.managers.camera.focusLoci(fcLoci);
      else fcPlugin.canvas3d && fcPlugin.canvas3d.requestCameraReset();
      log('✓ 聚焦: 链 ' + focusChain);
    } else {
      log('focus_chain: 未找到链 ' + focusChain + '，重置视角', 'warn');
      fcPlugin.canvas3d && fcPlugin.canvas3d.requestCameraReset();
    }
    setStatus('✓ 聚焦: 链 ' + focusChain, 'ok');
    hideStatus();
  } catch(e) {
    log('focus_chain 失败: ' + e.message, 'warn');
    ctx.plugin.canvas3d && ctx.plugin.canvas3d.requestCameraReset();
  }
}

async function opFocusSelection(ctx) {
  log('focus_selection');
  try {
    var fsPlugin = ctx.plugin;
    if (fsPlugin.managers.camera && ctx.highlights && ctx.highlights.length > 0) {
      var lastHl = ctx.highlights[ctx.highlights.length - 1];
      if (lastHl && lastHl.loci) {
        fsPlugin.managers.camera.focusLoci(lastHl.loci);
        log('✓ 聚焦到最近选区');
        setStatus('✓ 聚焦到选区', 'ok');
        hideStatus();
        return;
      }
    }
    fsPlugin.canvas3d && fsPlugin.canvas3d.requestCameraReset();
    setStatus('✓ 视角重置', 'ok');
    hideStatus();
  } catch(e) { log('focus_selection 失败: ' + e.message, 'error'); }
}

async function opResetView(ctx) {
  log('reset_view');
  try {
    var rvPlugin = ctx ? ctx.plugin : null;
    if (rvPlugin && rvPlugin.canvas3d) {
      rvPlugin.canvas3d.requestCameraReset();
      log('✓ 视角已重置');
      setStatus('✓ 视角已重置', 'ok');
      hideStatus();
    }
  } catch(e) { log('reset_view 失败: ' + e.message, 'error'); }
}

async function opSpin(ctx, p) {
  var spinActive = (p.active !== false && p.active !== 0);
  var spinSpeed = parseFloat(p.speed || 1);
  log('spin → ' + (spinActive ? 'ON speed=' + spinSpeed : 'OFF'));
  try {
    var canvas = ctx.plugin.canvas3d;
    if (!canvas) { log('canvas3d 不可用', 'warn'); return; }
    var tb = JSON.parse(JSON.stringify(canvas.props.trackball || {}));
    tb.animate = spinActive
      ? { name: 'spin', params: { speed: spinSpeed } }
      : { name: 'off', params: {} };
    canvas.setProps({ trackball: tb });
    log('✓ 旋转: ' + (spinActive ? 'ON' : 'OFF'));
    setStatus('✓ 旋转' + (spinActive ? '已启动' : '已停止'), 'ok');
    hideStatus();
  } catch(e) { log('spin 失败: ' + e.message, 'error'); }
}

async function opSaveView(ctx, p) {
  var svName = p.name || 'view_01';
  log('save_view: ' + svName);
  try {
    var svCanvas = ctx.plugin.canvas3d;
    if (!svCanvas) { log('save_view: canvas3d 不可用', 'warn'); return; }
    // 序列化相机状态
    var cam = svCanvas.camera;
    var snapshot = {
      position: cam.position ? { x: cam.position[0], y: cam.position[1], z: cam.position[2] } : null,
      target: cam.target ? { x: cam.target[0], y: cam.target[1], z: cam.target[2] } : null,
      up: cam.up ? { x: cam.up[0], y: cam.up[1], z: cam.up[2] } : null,
      radius: cam.radius,
      far: cam.far,
      near: cam.near,
    };
    if (!window.__pdbViewSnapshots) window.__pdbViewSnapshots = {};
    window.__pdbViewSnapshots[svName] = snapshot;
    log('✓ 视角已保存: ' + svName);
    setStatus('✓ 视角已保存: ' + svName, 'ok');
    hideStatus();
  } catch(e) { log('save_view 失败: ' + e.message, 'error'); }
}

async function opRestoreView(ctx, p) {
  var rvName = p.name || 'view_01';
  log('restore_view: ' + rvName);
  try {
    var rvSnapshots = window.__pdbViewSnapshots || {};
    var rvSnap = rvSnapshots[rvName];
    if (!rvSnap) {
      log('restore_view: 未找到快照 ' + rvName, 'warn');
      setStatus('⚠ 未找到视角快照: ' + rvName, 'ok');
      return;
    }
    var rvCanvas = ctx.plugin.canvas3d;
    if (!rvCanvas) { log('restore_view: canvas3d 不可用', 'warn'); return; }
    // 通过相机目标+位置还原
    if (rvCanvas.camera && rvSnap.position && rvSnap.target) {
      rvCanvas.camera.setState({
        position: [rvSnap.position.x, rvSnap.position.y, rvSnap.position.z],
        target: [rvSnap.target.x, rvSnap.target.y, rvSnap.target.z],
        up: rvSnap.up ? [rvSnap.up.x, rvSnap.up.y, rvSnap.up.z] : [0, 1, 0],
        radius: rvSnap.radius,
      });
      rvCanvas.requestRedraw();
    }
    log('✓ 视角已恢复: ' + rvName);
    setStatus('✓ 视角已恢复: ' + rvName, 'ok');
    hideStatus();
  } catch(e) { log('restore_view 失败: ' + e.message, 'error'); }
}

async function opSetProjection(ctx, p) {
  var projMode = (p.mode || 'perspective').toLowerCase();
  log('set_projection: ' + projMode);
  try {
    var projCanvas = ctx.plugin.canvas3d;
    if (!projCanvas) { log('set_projection: canvas3d 不可用', 'warn'); return; }
    var isoMode = (projMode === 'orthographic' || projMode === 'ortho');
    projCanvas.setProps({
      camera: { mode: isoMode ? 'orthographic' : 'perspective' }
    });
    log('✓ 投影模式: ' + projMode);
    setStatus('✓ 投影: ' + projMode, 'ok');
    hideStatus();
  } catch(e) { log('set_projection 失败: ' + e.message, 'error'); }
}
