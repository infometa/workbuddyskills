// ========================================================================
// ops/a3-visibility.js — 可见性控制
// 负责：opSetWater、opChainVisibility、opLigandVisibility、opIsolate、
//       opShowAll、opHideHydrogens、opShowBackboneOnly
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

async function opSetWater(ctx, p) {
  var show = (p.visible !== false && p.visible !== 0);
  log('set_water → ' + (show ? '显示' : '隐藏'));
  if (!ctx.components.water) { log('无水分子组件', 'warn'); return; }

  var waterRef = ctx.components.water.ref;
  var wPlugin = ctx.plugin;
  await wPlugin.build().to(waterRef).update(function(old) {
    return Object.assign({}, old, { isHidden: !show });
  }).commit();
  ctx.waterHidden = !show;
  log('✓ 水分子: ' + (show ? '显示' : '已隐藏'));
  setStatus('✓ 水分子' + (show ? '已显示' : '已隐藏'), 'ok');
  hideStatus();
}

async function opChainVisibility(ctx, p) {
  var chainId = (p.chain || 'A').toUpperCase();
  var visible = (p.visible !== false && p.visible !== 0);
  log('chain_visibility: ' + chainId + ' → ' + (visible ? '显示' : '隐藏'));
  try {
    var cvPlugin = ctx.plugin;
    var cvStr = ctx.structure && ctx.structure.obj && ctx.structure.obj.data;
    if (!cvStr) { log('chain_visibility: 无结构数据', 'warn'); return; }

    var cvPolyRef = ctx.components.polymer ? ctx.components.polymer.ref : null;
    if (!cvPolyRef) { log('chain_visibility: 无 polymer 组件', 'warn'); return; }

    // 获取当前表示层类型
    var cvReprRefs = [];
    cvPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.transform && cell.transform.parent === cvPolyRef) {
        cvReprRefs.push({ ref: ref, cell: cell });
      }
    });

    if (cvReprRefs.length === 0) { log('chain_visibility: 未找到表示层', 'warn'); return; }

    // 获取当前 repr 参数
    var cvReprCell = cvPlugin.state.data.cells.get(cvReprRefs[0].ref);
    var cvCurType = (cvReprCell && cvReprCell.params && cvReprCell.params.values) ?
      (cvReprCell.params.values.type || { name: 'cartoon' }) : { name: 'cartoon' };
    var cvCurColor = (cvReprCell && cvReprCell.params && cvReprCell.params.values) ?
      (cvReprCell.params.values.color || { name: 'chain-id' }) : { name: 'chain-id' };

    // 更新链的可见性记录
    ctx.chainVisibility[chainId] = visible;

    // 重建 polymer repr：使用 expression 过滤链
    var MS = molstar.lib && molstar.lib['mol-script'] && molstar.lib['mol-script'].language
      ? molstar.lib['mol-script'].language.MolScript
      : null;

    if (!MS) {
      // 降级方案：通过组件 isHidden 控制（整体显隐，不区分链）
      log('chain_visibility: MolScript 不可用，使用组件级显隐（影响所有链）', 'warn');
      await cvPlugin.build().to(cvPolyRef).update(function(old) {
        return Object.assign({}, old, { isHidden: !visible });
      }).commit();
      setStatus('✓ 链 ' + chainId + (visible ? ' 显示' : ' 隐藏') + '（组件级）', 'ok');
      hideStatus();
      return;
    }

    // 创建链级选择 expression
    var chainExpr = MS.struct.generator.atomGroups({
      'chain-test': MS.core.rel.eq([MS.ammp('auth_asym_id'), chainId])
    });

    // 找到或创建该链的专属组件
    var cvCompTag = 'chain-comp-' + chainId;
    var existingCompRef = null;
    cvPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.transform && cell.transform.tags &&
          cell.transform.tags.indexOf(cvCompTag) >= 0) {
        existingCompRef = ref;
      }
    });

    if (!existingCompRef) {
      // 创建链专属组件
      var cvStructRef = ctx.structure.ref;
      var cvBuild = cvPlugin.build();
      cvBuild.to(cvStructRef).apply(
        molstar.lib['mol-plugin-state'].transforms.model.StructureComponent,
        { type: { name: 'expression', params: { expression: chainExpr } }, label: 'Chain ' + chainId },
        { tags: [cvCompTag] }
      );
      await cvBuild.commit();
      // 找到新创建的组件引用
      cvPlugin.state.data.cells.forEach(function(cell, ref) {
        if (cell && cell.transform && cell.transform.tags &&
            cell.transform.tags.indexOf(cvCompTag) >= 0) {
          existingCompRef = ref;
        }
      });
    }

    if (existingCompRef) {
      await cvPlugin.build().to(existingCompRef).update(function(old) {
        return Object.assign({}, old, { isHidden: !visible });
      }).commit();
      log('✓ 链 ' + chainId + (visible ? ' 已显示' : ' 已隐藏'));
      setStatus('✓ 链 ' + chainId + (visible ? ' 显示' : ' 隐藏'), 'ok');
      hideStatus();
    } else {
      log('chain_visibility: 创建链组件失败', 'warn');
      // 最终降级：整体显隐
      await cvPlugin.build().to(cvPolyRef).update(function(old) {
        return Object.assign({}, old, { isHidden: !visible });
      }).commit();
      setStatus('✓ ' + (visible ? '显示' : '隐藏') + '（降级模式）', 'ok');
      hideStatus();
    }
  } catch(e) {
    log('chain_visibility 失败: ' + e.message, 'error');
    // 最终降级
    if (ctx.components.polymer) {
      var cRef = ctx.components.polymer.ref;
      var vis = (p.visible !== false && p.visible !== 0);
      await ctx.plugin.build().to(cRef).update(function(old) {
        return Object.assign({}, old, { isHidden: !vis });
      }).commit();
      setStatus('✓ ' + (vis ? '显示' : '隐藏') + '（降级）', 'ok');
      hideStatus();
    }
  }
}

async function opLigandVisibility(ctx, p) {
  var ligVisible = (p.visible !== false && p.visible !== 0);
  log('ligand_visibility → ' + (ligVisible ? '显示' : '隐藏'));
  if (!ctx.components.ligand) { log('无配体组件', 'warn'); return; }
  try {
    await ctx.plugin.build().to(ctx.components.ligand.ref).update(function(old) {
      return Object.assign({}, old, { isHidden: !ligVisible });
    }).commit();
    log('✓ 配体' + (ligVisible ? '已显示' : '已隐藏'));
    setStatus('✓ 配体' + (ligVisible ? '显示' : '隐藏'), 'ok');
    hideStatus();
  } catch(e) { log('ligand_visibility 失败: ' + e.message, 'error'); }
}

async function opIsolate(ctx, p) {
  var isoTarget = (p.target || '').toLowerCase();
  log('isolate: ' + isoTarget);
  try {
    var isoPlugin = ctx.plugin;
    if (isoTarget.startsWith('chain:')) {
      var isoChain = isoTarget.split(':')[1].toUpperCase();

      // ★ 修复：获取所有链并隐藏非目标链（原代码只隐藏 ligand/water）
      var allChains = [];
      try {
        var isoHier = isoPlugin.managers.structure.hierarchy;
        if (isoHier && isoHier.current && isoHier.current.structures && isoHier.current.structures[0]) {
          var isoStr = isoHier.current.structures[0].cell.obj;
          if (isoStr && isoStr.data && isoStr.data.model && isoStr.data.model.atomicHierarchy) {
            var isoAh = isoStr.data.model.atomicHierarchy;
            var isoSeen = {};
            for (var ci = 0; ci < isoAh.chains._rowCount; ci++) {
              var cid = isoAh.chains.auth_asym_id.value(ci);
              if (!isoSeen[cid]) { isoSeen[cid] = true; allChains.push(cid); }
            }
          }
        }
      } catch(_e) { log('isolate: 获取链列表失败', 'warn'); }

      log('isolate chain:' + isoChain + ' — 所有链: [' + allChains.join(', ') + ']');

      // 显示目标链
      await executeOp({ op: 'chain_visibility', params: { chain: isoChain, visible: true } });

      // 隐藏其他链
      for (var i = 0; i < allChains.length; i++) {
        if (allChains[i] !== isoChain) {
          await executeOp({ op: 'chain_visibility', params: { chain: allChains[i], visible: false } });
        }
      }

      // 隐藏配体和水
      if (ctx.components.ligand) {
        await isoPlugin.build().to(ctx.components.ligand.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: true });
        }).commit();
      }
      if (ctx.components.water) {
        await isoPlugin.build().to(ctx.components.water.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: true });
        }).commit();
      }
    } else if (isoTarget === 'polymer' || isoTarget === 'protein') {
      if (ctx.components.polymer) {
        await isoPlugin.build().to(ctx.components.polymer.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: false });
        }).commit();
      }
      if (ctx.components.ligand) {
        await isoPlugin.build().to(ctx.components.ligand.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: true });
        }).commit();
      }
      if (ctx.components.water) {
        await isoPlugin.build().to(ctx.components.water.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: true });
        }).commit();
      }
    } else if (isoTarget === 'ligand') {
      if (ctx.components.polymer) {
        await isoPlugin.build().to(ctx.components.polymer.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: true });
        }).commit();
      }
      if (ctx.components.ligand) {
        await isoPlugin.build().to(ctx.components.ligand.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: false });
        }).commit();
      }
      if (ctx.components.water) {
        await isoPlugin.build().to(ctx.components.water.ref).update(function(old) {
          return Object.assign({}, old, { isHidden: true });
        }).commit();
      }
    }
    log('✓ 隔离: ' + isoTarget);
    setStatus('✓ 隔离: ' + isoTarget, 'ok');
    hideStatus();
  } catch(e) { log('isolate 失败: ' + e.message, 'error'); }
}

async function opShowAll(ctx) {
  log('show_all');
  try {
    var saPlugin = ctx.plugin;
    var saUpd = saPlugin.build();
    var saModified = false;
    saPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.params && cell.params.values && cell.params.values.isHidden === true) {
        saUpd.to(ref).update(function(old) {
          return Object.assign({}, old, { isHidden: false });
        });
        saModified = true;
      }
    });
    if (saModified) await saUpd.commit();
    ctx.chainVisibility = {};
    ctx.waterHidden = false;
    log('✓ 所有组件已恢复显示');
    setStatus('✓ 已恢复全部显示', 'ok');
    hideStatus();
  } catch(e) { log('show_all 失败: ' + e.message, 'error'); }
}

async function opHideHydrogens(ctx, p) {
  var hhVisible = (p.visible !== false && p.visible !== 0);
  log('hide_hydrogens → ' + (hhVisible ? '显示' : '隐藏'));
  try {
    var hhPlugin = ctx.plugin;
    var hhPolyRef = ctx.components.polymer ? ctx.components.polymer.ref : null;
    if (!hhPolyRef) { log('hide_hydrogens: 无 polymer 组件', 'warn'); return; }
    var hhReprRefs = [];
    hhPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.transform && cell.transform.parent === hhPolyRef) {
        hhReprRefs.push(ref);
      }
    });
    if (hhReprRefs.length === 0) { log('hide_hydrogens: 未找到表示层', 'warn'); return; }
    var hhReprCell = hhPlugin.state.data.cells.get(hhReprRefs[0]);
    var hhCurType = (hhReprCell && hhReprCell.params && hhReprCell.params.values) ?
      (hhReprCell.params.values.type || { name: 'cartoon' }) : { name: 'cartoon' };
    var hhCurColor = (hhReprCell && hhReprCell.params && hhReprCell.params.values) ?
      (hhReprCell.params.values.color || { name: 'chain-id' }) : { name: 'chain-id' };
    var hhUpd = hhPlugin.build();
    for (var hhi = 0; hhi < hhReprRefs.length; hhi++) hhUpd.delete(hhReprRefs[hhi]);
    hhPlugin.builders.structure.representation.buildRepresentation(
      hhUpd, ctx.components.polymer,
      {
        type: hhCurType.name || 'cartoon',
        typeParams: { ignoreHydrogens: !hhVisible },
        color: (hhCurColor.name || 'chain-id')
      },
      { tag: 'polymer-repr' }
    );
  await hhUpd.commit();
  log('✓ 氢原子' + (hhVisible ? '显示' : '已隐藏'));
  setStatus('✓ 氢原子' + (hhVisible ? '显示' : '隐藏'), 'ok');
  hideStatus();

  // ★ 修复：重建 repr 后恢复链可见性状态
  if (typeof ReapplyChainVisibility === 'function') await ReapplyChainVisibility(ctx);
} catch(e) { log('hide_hydrogens 失败: ' + e.message, 'error'); }
}

async function opShowBackboneOnly(ctx, p) {
  var sboVisible = (p.visible !== false && p.visible !== 0);
  log('show_backbone_only → ' + sboVisible);
  try {
    var sboPlugin = ctx.plugin;
    var sboPolyRef = ctx.components.polymer ? ctx.components.polymer.ref : null;
    if (!sboPolyRef) { log('show_backbone_only: 无 polymer 组件', 'warn'); return; }
    var sboReprRefs = [];
    sboPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.transform && cell.transform.parent === sboPolyRef) {
        sboReprRefs.push(ref);
      }
    });
    var sboUpd = sboPlugin.build();
    for (var sboi = 0; sboi < sboReprRefs.length; sboi++) sboUpd.delete(sboReprRefs[sboi]);
    sboPlugin.builders.structure.representation.buildRepresentation(
      sboUpd, ctx.components.polymer,
      {
        type: 'backbone',
        color: 'chain-id'
      },
      { tag: 'polymer-repr' }
    );
  await sboUpd.commit();
  log('✓ 已切换为主链骨架显示');
  setStatus('✓ 主链骨架模式', 'ok');
  hideStatus();

  // ★ 修复：重建 repr 后恢复链可见性状态
  if (typeof ReapplyChainVisibility === 'function') await ReapplyChainVisibility(ctx);
} catch(e) { log('show_backbone_only 失败: ' + e.message, 'error'); }
}
