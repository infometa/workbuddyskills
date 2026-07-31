// ========================================================================
// ops/a4-repr.js — 表示方式控制
// 负责：opSetRepr（case 'set_repr'）、opSetReprByComponent（case 'set_repr_by_component'）
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

async function opSetRepr(ctx, p) {
  var repr = p.repr || p.type || 'cartoon';
  repr = repr.replace(/_/g, '-'); // 统一转连字符
  // 别名映射
  var reprAlias = { 'sticks': 'line', 'mesh-surface': 'molecular-surface',
    'dots': 'point', 'trace': 'backbone', 'surface': 'gaussian-surface' };
  if (reprAlias[repr]) repr = reprAlias[repr];
  log('set_repr → ' + repr);

  if (!ctx.components.polymer) { log('无 polymer 组件', 'warn'); return; }

  var plugin = ctx.plugin;
  var polymerRef = ctx.components.polymer.ref;

  var reprRefs = [];
  plugin.state.data.cells.forEach(function(cell, ref) {
    if (cell && cell.transform && cell.transform.parent === polymerRef) {
      reprRefs.push(ref);
    }
  });
  log('找到旧表示层: ' + reprRefs.length + ' 个');

  var upd = plugin.build();
  for (var ri = 0; ri < reprRefs.length; ri++) {
    upd.delete(reprRefs[ri]);
  }
  var colorScheme = (repr === 'line' || repr === 'ball-and-stick') ? 'element-symbol' : 'chain-id';
  plugin.builders.structure.representation.buildRepresentation(
    upd, ctx.components.polymer,
    { type: repr, color: colorScheme },
    { tag: 'polymer-repr' }
  );
  await upd.commit();
  log('✓ 表示已切换为: ' + repr);
  setStatus('✓ 表示: ' + repr, 'ok');
  hideStatus();

  // ★ 修复：重建 repr 后恢复链可见性状态（否则 chain_visibility 设置会被覆盖）
  await ReapplyChainVisibility(ctx);
}

/**
 * ReapplyChainVisibility — 重建表示层后重新应用链级显隐
 * 遍历 ctx.chainVisibility，对每条被标记为 hidden 的链重新执行显隐操作。
 * 被 opSetRepr / opSetReprByComponent / opHideHydrogens / opShowBackboneOnly 调用。
 */
async function ReapplyChainVisibility(ctx) {
  if (!ctx || !ctx.plugin || !ctx.chainVisibility) return;
  var chains = Object.keys(ctx.chainVisibility);
  var hiddenChains = chains.filter(function(c) { return !ctx.chainVisibility[c]; });
  if (hiddenChains.length === 0) return;

  log('ReapplyChainVisibility: 恢复 ' + hiddenChains.length + ' 条链的隐藏状态 [' + hiddenChains.join(', ') + ']');
  for (var i = 0; i < hiddenChains.length; i++) {
    await executeOp({ op: 'chain_visibility', params: { chain: hiddenChains[i], visible: false } });
  }
}

async function opSetReprByComponent(ctx, p) {
  var rbc = p; // polymer, ligand, water 各自的 repr
  log('set_repr_by_component: ' + JSON.stringify(rbc).substring(0, 80));
  try {
    var rbcPlugin = ctx.plugin;
    var rbcUpd = rbcPlugin.build();
    var rbcAliases = { 'sticks': 'line', 'mesh-surface': 'molecular-surface',
      'dots': 'point', 'trace': 'backbone', 'surface': 'gaussian-surface' };

    // polymer
    if (rbc.polymer && ctx.components.polymer) {
      var polyType = (rbc.polymer || 'cartoon').replace(/_/g,'-');
      if (rbcAliases[polyType]) polyType = rbcAliases[polyType];
      var polyRef = ctx.components.polymer.ref;
      var polyReprRefs = [];
      rbcPlugin.state.data.cells.forEach(function(cell, ref) {
        if (cell && cell.transform && cell.transform.parent === polyRef) polyReprRefs.push(ref);
      });
      for (var pi = 0; pi < polyReprRefs.length; pi++) rbcUpd.delete(polyReprRefs[pi]);
      rbcPlugin.builders.structure.representation.buildRepresentation(
        rbcUpd, ctx.components.polymer,
        { type: polyType, color: 'chain-id' }, { tag: 'polymer-repr' }
      );
    }
    // ligand
    if (rbc.ligand && ctx.components.ligand) {
      var ligType = (rbc.ligand || 'ball-and-stick').replace(/_/g,'-');
      if (rbcAliases[ligType]) ligType = rbcAliases[ligType];
      var ligRef = ctx.components.ligand.ref;
      var ligReprRefs = [];
      rbcPlugin.state.data.cells.forEach(function(cell, ref) {
        if (cell && cell.transform && cell.transform.parent === ligRef) ligReprRefs.push(ref);
      });
      for (var li = 0; li < ligReprRefs.length; li++) rbcUpd.delete(ligReprRefs[li]);
      rbcPlugin.builders.structure.representation.buildRepresentation(
        rbcUpd, ctx.components.ligand,
        { type: ligType, color: 'element-symbol' }, { tag: 'ligand-repr' }
      );
    }
    // water
    if (rbc.water && ctx.components.water) {
      var watType = (rbc.water || 'ball-and-stick').replace(/_/g,'-');
      if (rbcAliases[watType]) watType = rbcAliases[watType];
      var watRef = ctx.components.water.ref;
      var watReprRefs = [];
      rbcPlugin.state.data.cells.forEach(function(cell, ref) {
        if (cell && cell.transform && cell.transform.parent === watRef) watReprRefs.push(ref);
      });
      for (var wi = 0; wi < watReprRefs.length; wi++) rbcUpd.delete(watReprRefs[wi]);
      rbcPlugin.builders.structure.representation.buildRepresentation(
        rbcUpd, ctx.components.water,
        { type: watType, typeParams: { alpha: 0.4 } }, { tag: 'water-repr' }
      );
    }
    await rbcUpd.commit();
    log('✓ 分组件表示已更新');
    setStatus('✓ 分组件表示更新', 'ok');
    hideStatus();

    // ★ 修复：重建 repr 后恢复链可见性状态
    await ReapplyChainVisibility(ctx);
  } catch(e) { log('set_repr_by_component 失败: ' + e.message, 'error'); }
}
