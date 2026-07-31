// ========================================================================
// ops/a7-label.js — 标签管理
// 负责：opAddLabel、opAutoLabelSelection、opClearLabels
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

async function opAddLabel(ctx, p) {
  var lblChain = (p.chain || 'A').toUpperCase();
  var lblRes = parseInt(p.residue || p.res || 0);
  var lblText = p.text || '';
  log('add_label: ' + lblChain + ':' + lblRes + ' text=' + lblText);
  try {
    var lblPlugin = ctx.plugin;
    var lblHier = lblPlugin.managers.structure.hierarchy;
    if (!lblHier || !lblHier.current || !lblHier.current.structures || !lblHier.current.structures[0]) {
      log('add_label: 无结构对象', 'warn'); return;
    }
    var lblStr = lblHier.current.structures[0].cell.obj.data;
    var _lblSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_lblSE) { log('add_label: 无 StructureElement', 'error'); return; }

    // 找到残基第一个原子
    var lblUnits = lblStr.units;
    var lblFoundUnit = null, lblFoundAtomIdx = -1;
    for (var lu = 0; lu < lblUnits.length; lu++) {
      var lblUnit = lblUnits[lu];
      if (!lblUnit.model) continue;
      var lblH = lblUnit.model.atomicHierarchy;
      if (!lblH || !lblH.chainAtomSegments) continue;
      var lblAC = lblH.chains.auth_asym_id, lblLC = lblH.chains.label_asym_id;
      var lblSeqs = lblH.residues.label_seq_id;
      var lblRSegs = lblH.residueAtomSegments, lblCSegs = lblH.chainAtomSegments;
      for (var lci = 0; lci < lblAC.rowCount; lci++) {
        if (lblAC.value(lci) !== lblChain && lblLC.value(lci) !== lblChain) continue;
        var lcS = lblCSegs.offsets[lci], lcE = lblCSegs.offsets[lci + 1];
        for (var lri = 0; lri < lblSeqs.rowCount; lri++) {
          var lrS = lblRSegs.offsets[lri];
          if (lrS < lcS || lrS >= lcE) continue;
          if (lblSeqs.value(lri) !== lblRes) continue;
          lblFoundUnit = lblUnit;
          lblFoundAtomIdx = lblRSegs.offsets[lri];
          break;
        }
        if (lblFoundUnit) break;
      }
      if (lblFoundUnit) break;
    }

    if (!lblFoundUnit || lblFoundAtomIdx < 0) {
      log('add_label: 未找到 ' + lblChain + ':' + lblRes, 'warn');
      setStatus('⚠ 未找到残基 ' + lblChain + ':' + lblRes, 'ok');
      return;
    }

    var lblLoci = _lblSE.Loci(lblStr, [{
      unit: lblFoundUnit,
      indices: { size: 1, indices: new Int32Array([lblFoundAtomIdx]) }
    }]);

    await lblPlugin.managers.structure.measurement.addLabel(lblLoci, lblText ? { customText: lblText } : {});
    log('✓ 标签已添加: ' + lblChain + ':' + lblRes + (lblText ? ' "' + lblText + '"' : ''));
    setStatus('✓ 标签已添加', 'ok');
    hideStatus();
  } catch(e) { log('add_label 失败: ' + e.message, 'error'); }
}

async function opAutoLabelSelection(ctx) {
  log('auto_label_selection');
  try {
    var alsPlugin = ctx.plugin;
    if (!ctx.highlights || ctx.highlights.length === 0) {
      log('auto_label_selection: 无选区，请先高亮残基', 'warn');
      setStatus('⚠ 请先选择残基', 'ok');
      return;
    }
    var alsHl = ctx.highlights[ctx.highlights.length - 1];
    if (alsHl && alsHl.loci) {
      await alsPlugin.managers.structure.measurement.addLabel(alsHl.loci);
      log('✓ 批量标签已添加 (' + (alsHl.residues ? alsHl.residues.length : '?') + ' 个残基)');
      setStatus('✓ 批量标签已添加', 'ok');
      hideStatus();
    }
  } catch(e) { log('auto_label_selection 失败: ' + e.message, 'error'); }
}

async function opClearLabels(ctx) {
  log('clear_labels');
  try {
    var clbPlugin = ctx.plugin;
    var clbFound = [];
    clbPlugin.state.data.cells.forEach(function(cell, ref) {
      var tags = (cell && cell.transform && cell.transform.tags) || [];
      for (var ti = 0; ti < tags.length; ti++) {
        if (typeof tags[ti] === 'string' && tags[ti].indexOf('label') >= 0) {
          clbFound.push(ref); break;
        }
      }
      // 也检查 obj tags
      if (cell && cell.obj && cell.obj.tags) {
        var otags = cell.obj.tags;
        for (var oti = 0; oti < otags.length; oti++) {
          if (typeof otags[oti] === 'string' && otags[oti].indexOf('label') >= 0) {
            if (!clbFound.includes(ref)) clbFound.push(ref); break;
          }
        }
      }
    });
    if (clbFound.length > 0) {
      var clbUpd = clbPlugin.build();
      for (var clbi = 0; clbi < clbFound.length; clbi++) clbUpd.to(clbFound[clbi]).delete();
      await clbUpd.commit();
      log('✓ 标签已清除 (' + clbFound.length + ' 个)');
      setStatus('✓ 标签已清除', 'ok');
    } else {
      setStatus('⚠ 无标签可清除', 'ok');
    }
    hideStatus();
  } catch(e) { log('clear_labels 失败: ' + e.message, 'error'); }
}
