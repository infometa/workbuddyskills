// ========================================================================
// ops/a5-color-opacity.js — 着色/透明度/背景色
// 负责：opSetColor、opSetColorSelection、opSetOpacity、opSetBg
// 依赖：utils.js（log, setStatus, hideStatus, hexToInt）
// ========================================================================

async function opSetColor(ctx, p) {
  var theme = p.theme || p.color || 'chain-id';
  var value = p.value ? hexToInt(p.value) : null;
  log('set_color → ' + theme);

  if (!ctx.components.polymer) { log('无 polymer 组件', 'warn'); return; }

  // theme 别名映射（用户友好名 → Mol* 内置名）
  var themeAlias = {
    'residue-type': 'residue-name',
    'plddt': 'b-factor',          // pLDDT 存在 B-factor 列
    'hydrophobic': 'hydrophobicity',
    'occupancy': 'occupancy',
    'polymer-id': 'polymer-id',
  };
  if (themeAlias[theme]) theme = themeAlias[theme];

  var _plugin = ctx.plugin;
  var _polyRef = ctx.components.polymer.ref;
  var _reprRefs2 = [];
  _plugin.state.data.cells.forEach(function(cell, ref) {
    if (cell && cell.transform && cell.transform.parent === _polyRef) {
      _reprRefs2.push(ref);
    }
  });

  if (_reprRefs2.length === 0) { log('未找到表示层，跳过着色', 'warn'); return; }

  var _reprCell = _plugin.state.data.cells.get(_reprRefs2[0]);
  var _curType = (_reprCell && _reprCell.params && _reprCell.params.values) ?
    (_reprCell.params.values.type || { name: 'cartoon' }) : { name: 'cartoon' };

  var reprParams = value !== null
    ? { color: 'uniform', colorParams: { value: value } }
    : { color: theme };

  var _upd2 = _plugin.build();
  for (var _ri2 = 0; _ri2 < _reprRefs2.length; _ri2++) {
    _upd2.delete(_reprRefs2[_ri2]);
  }
  _plugin.builders.structure.representation.buildRepresentation(
    _upd2, ctx.components.polymer,
    Object.assign({ type: _curType.name || 'cartoon' }, reprParams),
    { tag: 'polymer-repr' }
  );
  await _upd2.commit();
  log('✓ 着色方案: ' + theme);
  setStatus('✓ 着色: ' + theme, 'ok');
  hideStatus();
}

async function opSetColorSelection(ctx, p) {
  var scsColor = p.value || p.color || '#FFCC00';
  var scsInt = hexToInt(scsColor);
  log('set_color_selection → ' + scsColor);
  try {
    var scsPlugin = ctx.plugin;
    if (!ctx.highlights || ctx.highlights.length === 0) {
      log('set_color_selection: 无选区，请先高亮残基', 'warn');
      setStatus('⚠ 请先选择残基', 'ok');
      return;
    }
    var scsLoci = ctx.highlights[ctx.highlights.length - 1].loci;

    // ★ 正确实现：使用 Mol* Overpaint 机制实现选区局部着色
    // 原理：OverpaintStructureRepresentation3DFromBundle 在现有 repr 节点上叠加染色层，
    //        不影响其他残基的颜色，实现真正的"仅选区变色"。
    var SE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
          || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!SE) { log('set_color_selection: 无 StructureElement', 'error'); return; }

    // 将 loci 转换为 Bundle（Overpaint 所需格式）
    var bundle = SE.Bundle && SE.Bundle.fromLoci ? SE.Bundle.fromLoci(scsLoci) : null;
    if (!bundle) {
      log('set_color_selection: 无法创建 Bundle，降级为全局着色', 'warn');
      // 降级方案：全局着色
      if (scsPlugin.managers.structure && scsPlugin.managers.structure.component) {
        await scsPlugin.managers.structure.component.updateRepresentationsTheme(
          scsPlugin.managers.structure.hierarchy.current.structures,
          { color: 'uniform', colorParams: { value: scsInt } }
        );
      }
      setStatus('✓ 全局染色（Bundle API 不可用）: ' + scsColor, 'ok');
      hideStatus();
      return;
    }

    // 找到所有 representation 节点（polymer/ligand 等）
    var reprRefs = [];
    scsPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.transform && cell.transform.transformer) {
        var tname = cell.transform.transformer.id || cell.transform.transformer.definition && cell.transform.transformer.definition.id || '';
        if (tname.indexOf('StructureRepresentation3D') >= 0) {
          reprRefs.push(ref);
        }
      }
    });

    if (reprRefs.length === 0) {
      log('set_color_selection: 未找到 repr 节点，尝试从 polymer 组件查找', 'warn');
      if (ctx.components.polymer) {
        var polyRef = ctx.components.polymer.ref;
        scsPlugin.state.data.cells.forEach(function(cell, ref) {
          if (cell && cell.transform && cell.transform.parent === polyRef) {
            reprRefs.push(ref);
          }
        });
      }
    }

    if (reprRefs.length === 0) {
      log('set_color_selection: 无可用 repr 节点', 'warn');
      setStatus('⚠ 无表示层可染色', 'ok');
      return;
    }

    // 获取 OverpaintStructureRepresentation3DFromBundle transform
    var molPluginState = molstar.lib && molstar.lib['mol-plugin-state'];
    var overpaintTransform = molPluginState && molPluginState.transforms
      && molPluginState.transforms.Representation
      && molPluginState.transforms.Representation.OverpaintStructureRepresentation3DFromBundle;

    if (!overpaintTransform) {
      // 通过 Xe 对象查找（molstar bundle 导出方式）
      var Xe = scsPlugin.builders && scsPlugin.builders.structure;
      // 尝试从 state.transforms 查找
      overpaintTransform = scsPlugin.state && scsPlugin.state.transforms
        && scsPlugin.state.transforms['Representation.OverpaintStructureRepresentation3DFromBundle'];
    }

    if (!overpaintTransform) {
      log('set_color_selection: OverpaintStructureRepresentation3DFromBundle 不可用，降级为全局着色', 'warn');
      if (scsPlugin.managers.structure && scsPlugin.managers.structure.component) {
        await scsPlugin.managers.structure.component.updateRepresentationsTheme(
          scsPlugin.managers.structure.hierarchy.current.structures,
          { color: 'uniform', colorParams: { value: scsInt } }
        );
      }
      setStatus('✓ 全局染色（Overpaint 不可用）: ' + scsColor, 'ok');
      hideStatus();
      return;
    }

    // 对每个 repr 节点应用 Overpaint
    var scsUpd = scsPlugin.build();
    var overpaintTag = 'selection-overpaint';
    // 先清除已有的 overpaint
    scsPlugin.state.data.cells.forEach(function(cell, ref) {
      var tags = (cell && cell.transform && cell.transform.tags) || [];
      if (tags.indexOf(overpaintTag) >= 0) {
        scsUpd.delete(ref);
      }
    });
    // 对每个 repr 添加 overpaint
    for (var ri = 0; ri < reprRefs.length; ri++) {
      scsUpd.to(reprRefs[ri]).apply(
        overpaintTransform,
        { layers: [{ bundle: bundle, color: scsInt, clear: false }] },
        { tags: [overpaintTag] }
      );
    }
    await scsUpd.commit();

    log('✓ 选区颜色已更新（Overpaint）: ' + scsColor + '（' + reprRefs.length + ' 个表示层）');
    setStatus('✓ 选区着色: ' + scsColor, 'ok');
    hideStatus();
  } catch(e) {
    log('set_color_selection 失败: ' + e.message + '，尝试降级', 'error');
    // 最终降级
    try {
      var fb = ctx.plugin;
      if (fb.managers.structure && fb.managers.structure.component) {
        await fb.managers.structure.component.updateRepresentationsTheme(
          fb.managers.structure.hierarchy.current.structures,
          { color: 'uniform', colorParams: { value: scsInt } }
        );
        setStatus('✓ 全局着色（降级）: ' + scsColor, 'ok');
        hideStatus();
      }
    } catch(_e2) { log('降级也失败: ' + _e2.message, 'error'); }
  }
}

async function opSetOpacity(ctx, p) {
  var opTarget = (p.target || 'polymer').toLowerCase();
  var opAlpha = parseFloat(p.alpha !== undefined ? p.alpha : 0.5);
  log('set_opacity: ' + opTarget + ' alpha=' + opAlpha);
  try {
    var opPlugin = ctx.plugin;
    var opCompRef = null;
    if (opTarget === 'polymer' && ctx.components.polymer) opCompRef = ctx.components.polymer.ref;
    else if ((opTarget === 'ligand' || opTarget === 'surface') && ctx.components.ligand) opCompRef = ctx.components.ligand.ref;
    else if (opTarget === 'water' && ctx.components.water) opCompRef = ctx.components.water.ref;

    if (!opCompRef) {
      // 尝试对所有组件设置
      opCompRef = ctx.components.polymer ? ctx.components.polymer.ref : null;
    }
    if (!opCompRef) { log('set_opacity: 无有效组件', 'warn'); return; }

    var opReprRefs = [];
    opPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.transform && cell.transform.parent === opCompRef) opReprRefs.push(ref);
    });

    if (opReprRefs.length === 0) { log('set_opacity: 未找到表示层', 'warn'); return; }

    var opReprCell = opPlugin.state.data.cells.get(opReprRefs[0]);
    var opCurType = (opReprCell && opReprCell.params && opReprCell.params.values) ?
      (opReprCell.params.values.type || { name: 'cartoon' }) : { name: 'cartoon' };
    var opCurColor = (opReprCell && opReprCell.params && opReprCell.params.values) ?
      (opReprCell.params.values.color || { name: 'chain-id' }) : { name: 'chain-id' };

    var opUpd = opPlugin.build();
    for (var opi = 0; opi < opReprRefs.length; opi++) opUpd.delete(opReprRefs[opi]);

    var opComp = opTarget === 'ligand' ? ctx.components.ligand
               : opTarget === 'water' ? ctx.components.water
               : ctx.components.polymer;
    opPlugin.builders.structure.representation.buildRepresentation(
      opUpd, opComp,
      {
        type: opCurType.name || 'cartoon',
        typeParams: { alpha: opAlpha },
        color: opCurColor.name || 'chain-id'
      },
      { tag: (opTarget === 'ligand' ? 'ligand-repr' : opTarget === 'water' ? 'water-repr' : 'polymer-repr') }
    );
    await opUpd.commit();
    log('✓ 透明度: ' + opTarget + ' = ' + opAlpha);
    setStatus('✓ 透明度: ' + opAlpha, 'ok');
    hideStatus();
  } catch(e) { log('set_opacity 失败: ' + e.message, 'error'); }
}

async function opSetBg(ctx, p) {
  var bgColor = p.color || '#1a1d24';
  var bgInt = hexToInt(bgColor);
  try {
    ctx.plugin.canvas3d && ctx.plugin.canvas3d.setProps({
      renderer: { backgroundColor: bgInt }
    });
    log('✓ 背景: ' + bgColor);
    setStatus('✓ 背景: ' + bgColor, 'ok');
    hideStatus();
  } catch(e) { log('set_bg 失败: ' + e.message, 'error'); }
}
