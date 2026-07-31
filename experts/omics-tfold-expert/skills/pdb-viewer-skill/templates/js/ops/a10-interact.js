// ========================================================================
// ops/a10-interact.js — 相互作用分析
// 负责：opShowInteractions（case 'show_hbonds'/'show_metal_coord'/'show_salt_bridges'/
//       'show_hydrophobic'/'show_clashes' 统一处理）、opClearInteractions
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

async function opShowInteractions(ctx, op) {
  var interactType = op; // show_hbonds / show_metal_coord / etc.
  log(interactType);
  try {
    var iaPlugin = ctx.plugin;
    var iaHier = iaPlugin.managers.structure.hierarchy;
    if (!iaHier || !iaHier.current || !iaHier.current.structures || !iaHier.current.structures[0]) {
      log(interactType + ': 无结构对象', 'warn'); return;
    }
    // Mol* interactions 通过 structure.apply InteractionsRepresentation
    var iaStructRef = iaHier.current.structures[0].cell.ref;
    var iaTypeMap = {
      'show_hbonds': 'hydrogen-bond',
      'show_metal_coord': 'metal-coordination',
      'show_salt_bridges': 'ionic',
      'show_hydrophobic': 'hydrophobic',
      'show_clashes': 'clash',
    };
    var iaReprType = iaTypeMap[interactType] || 'hydrogen-bond';
    var iaTag = 'interaction-' + iaReprType;

    // 检查是否已有该相互作用表示层
    var iaExisting = null;
    iaPlugin.state.data.cells.forEach(function(cell, ref) {
      if (cell && cell.transform && cell.transform.tags &&
          cell.transform.tags.indexOf(iaTag) >= 0) {
        iaExisting = ref;
      }
    });

    if (iaExisting) {
      // 切换显隐
      var iaCell = iaPlugin.state.data.cells.get(iaExisting);
      var iaHidden = iaCell && iaCell.params && iaCell.params.values && iaCell.params.values.isHidden;
      await iaPlugin.build().to(iaExisting).update(function(old) {
        return Object.assign({}, old, { isHidden: !iaHidden });
      }).commit();
      log('✓ ' + interactType + ' 切换显隐');
    } else {
      // 使用 Mol* InteractionsRepresentation（通过 structure.apply）
      var iaTransforms = molstar.lib && molstar.lib['mol-plugin-state'] &&
        molstar.lib['mol-plugin-state'].transforms;
      if (!iaTransforms) {
        log(interactType + ': mol-plugin-state transforms 不可用', 'warn');
        setStatus('⚠ 相互作用分析需要 Mol* 5.x 完整版', 'ok');
        return;
      }
      var iaRepres = iaTransforms.representation;
      if (!iaRepres || !iaRepres.StructureRepresentation3D) {
        log(interactType + ': StructureRepresentation3D 不可用', 'warn');
        return;
      }
      // 构建 interactions component
      var iaBuild = iaPlugin.build();
      iaBuild.to(iaStructRef).apply(
        iaRepres.StructureRepresentation3D,
        { type: { name: 'interactions', params: { interactions: { types: [iaReprType] } } } },
        { tags: [iaTag] }
      );
      await iaBuild.commit();
      log('✓ ' + interactType + ' 已显示（基于几何阈值）');
    }
    setStatus('✓ ' + interactType, 'ok');
    hideStatus();
  } catch(e) {
    log(interactType + ' 失败: ' + e.message, 'error');
    setStatus('⚠ ' + interactType + ' 不可用（需 Mol* 完整 interactions 模块）', 'ok');
  }
}

async function opClearInteractions(ctx) {
  log('clear_interactions');
  try {
    var ciPlugin = ctx.plugin;
    var ciFound = [];
    ciPlugin.state.data.cells.forEach(function(cell, ref) {
      var tags = (cell && cell.transform && cell.transform.tags) || [];
      for (var ti = 0; ti < tags.length; ti++) {
        if (typeof tags[ti] === 'string' && tags[ti].startsWith('interaction-')) {
          ciFound.push(ref);
          break;
        }
      }
    });
    if (ciFound.length > 0) {
      var ciUpd = ciPlugin.build();
      for (var cii = 0; cii < ciFound.length; cii++) ciUpd.to(ciFound[cii]).delete();
      await ciUpd.commit();
      log('✓ 相互作用标注已清除 (' + ciFound.length + ' 个)');
      setStatus('✓ 相互作用已清除', 'ok');
    } else {
      setStatus('⚠ 无相互作用标注', 'ok');
    }
    hideStatus();
  } catch(e) { log('clear_interactions 失败: ' + e.message, 'error'); }
}
