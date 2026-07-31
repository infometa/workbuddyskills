// ========================================================================
// ops/a9-measure.js — 测量工具
// 负责：opMeasureDist、opMeasureAngle、opMeasureDihedral、opClearMeasurements
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

async function opMeasureDist(ctx, p) {
  var mc1 = (p.chain1 || p.chain || 'A').toUpperCase();
  var mr1 = parseInt(p.res1 || p.residue1 || 1);
  var mc2 = (p.chain2 || p.chain || 'A').toUpperCase();
  var mr2 = parseInt(p.res2 || p.residue2 || 1);
  var ma1 = (p.atom1 || p.atom || 'CA').toUpperCase();
  var ma2 = (p.atom2 || p.atom || 'CA').toUpperCase();
  log('measure_dist: ' + mc1 + ':' + mr1 + ':' + ma1 + ' → ' + mc2 + ':' + mr2 + ':' + ma2);

  try {
    var mPlugin = ctx.plugin;
    var hier2 = mPlugin.managers.structure.hierarchy;
    if (!hier2 || !hier2.current || !hier2.current.structures || !hier2.current.structures[0]) {
      log('测量: 无法获取结构对象', 'warn'); return;
    }
    var mStrObj = hier2.current.structures[0].cell.obj;
    if (!mStrObj || !mStrObj.data) { log('测量: structure data 为空', 'warn'); return; }
    var mStr = mStrObj.data;

    var _mSE = null;
    if (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement) {
      _mSE = molstar.lib.structure.StructureElement;
    } else if (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure) {
      _mSE = molstar.lib['mol-model'].structure.StructureElement;
    }
    if (!_mSE) { log('测量: 无法找到 StructureElement', 'error'); return; }

    function getAtomLoci(structure, chainId, seqId, atomName) {
      try {
        var units = structure.units;
        for (var u = 0; u < units.length; u++) {
          var unit = units[u];
          if (!unit.model) continue;
          var h = unit.model.atomicHierarchy;
          if (!h) continue;
          var authChains = h.chains.auth_asym_id;
          var labelChains = h.chains.label_asym_id;
          var labelSeqs  = h.residues.label_seq_id;
          var atomLabels = h.atoms.label_atom_id;
          var resSegs    = h.residueAtomSegments;
          var chainAtomSegs = h.chainAtomSegments;
          if (!chainAtomSegs) continue;
          for (var ci = 0; ci < authChains.rowCount; ci++) {
            if (authChains.value(ci) !== chainId && labelChains.value(ci) !== chainId) continue;
            var caStart = chainAtomSegs.offsets[ci];
            var caEnd   = chainAtomSegs.offsets[ci + 1];
            for (var ri = 0; ri < labelSeqs.rowCount; ri++) {
              var raStart = resSegs.offsets[ri];
              if (raStart < caStart || raStart >= caEnd) continue;
              if (labelSeqs.value(ri) !== seqId) continue;
              var aiStart = resSegs.offsets[ri];
              var aiEnd   = resSegs.offsets[ri + 1];
              // 优先精确匹配 atomName，否则回退 CA
              var firstAtomIdx = -1;
              for (var ai = aiStart; ai < aiEnd; ai++) {
                var an = atomLabels.value(ai);
                if (firstAtomIdx < 0) firstAtomIdx = ai;
                if (an === atomName) {
                  return _mSE.Loci(structure, [{ unit: unit, indices: { size: 1, indices: new Int32Array([ai]) } }]);
                }
              }
              // 未找到指定原子名，回退到该残基第一个原子
              if (firstAtomIdx >= 0) {
                return _mSE.Loci(structure, [{ unit: unit, indices: { size: 1, indices: new Int32Array([firstAtomIdx]) } }]);
              }
            }
          }
        }
      } catch(le) { log('getAtomLoci err: ' + le.message, 'warn'); }
      return null;
    }

    var loci1 = getAtomLoci(mStr, mc1, mr1, ma1);
    var loci2 = getAtomLoci(mStr, mc2, mr2, ma2);

    if (!loci1 || !loci2) {
      log('测量: 无法定位原子，请在 Mol* 左侧面板手动测量', 'warn');
      setStatus('提示: 请在 Mol* 左侧面板手动点选两个残基后测量距离', 'ok');
      return;
    }

    await mPlugin.managers.structure.measurement.addDistance(loci1, loci2);
    log('✓ 距离测量已添加: ' + mc1 + ':' + mr1 + ':' + ma1 + ' ↔ ' + mc2 + ':' + mr2 + ':' + ma2);
    setStatus('✓ 距离测量已添加', 'ok');
    hideStatus();
  } catch(e) { log('measure_dist 失败: ' + e.message, 'error'); }
}

async function opMeasureAngle(ctx, p) {
  log('measure_angle');
  try {
    var maPlugin = ctx.plugin;
    var maHier = maPlugin.managers.structure.hierarchy;
    if (!maHier || !maHier.current || !maHier.current.structures || !maHier.current.structures[0]) {
      log('measure_angle: 无结构对象', 'warn'); return;
    }
    var maStr = maHier.current.structures[0].cell.obj.data;
    var _maSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_maSE) { log('measure_angle: 无 StructureElement', 'error'); return; }

    function getAtomLociHelper(structure, chainId, seqId, atomName, SE) {
      try {
        for (var u = 0; u < structure.units.length; u++) {
          var unit = structure.units[u];
          if (!unit.model) continue;
          var h = unit.model.atomicHierarchy;
          if (!h || !h.chainAtomSegments) continue;
          var authC = h.chains.auth_asym_id, labelC = h.chains.label_asym_id;
          var labelSeqs = h.residues.label_seq_id;
          var atomLabels = h.atoms.label_atom_id;
          var resSegs = h.residueAtomSegments, chainSegs = h.chainAtomSegments;
          for (var ci = 0; ci < authC.rowCount; ci++) {
            if (authC.value(ci) !== chainId && labelC.value(ci) !== chainId) continue;
            var cS = chainSegs.offsets[ci], cE = chainSegs.offsets[ci + 1];
            for (var ri = 0; ri < labelSeqs.rowCount; ri++) {
              var rS = resSegs.offsets[ri];
              if (rS < cS || rS >= cE) continue;
              if (labelSeqs.value(ri) !== seqId) continue;
              var aiS = resSegs.offsets[ri], aiE = resSegs.offsets[ri + 1];
              for (var ai = aiS; ai < aiE; ai++) {
                if (atomLabels.value(ai) === atomName) {
                  return SE.Loci(structure, [{ unit: unit, indices: { size: 1, indices: new Int32Array([ai]) } }]);
                }
              }
              // fallback: first atom
              if (aiS < aiE) return SE.Loci(structure, [{ unit: unit, indices: { size: 1, indices: new Int32Array([aiS]) } }]);
            }
          }
        }
      } catch(e) {}
      return null;
    }

    function parseLoci(locStr, str, SE) {
      var parts = (locStr || '').split(':');
      if (parts.length < 2) return null;
      var ch = parts[0].toUpperCase(), ri = parseInt(parts[1]), at = (parts[2] || 'CA').toUpperCase();
      return getAtomLociHelper(str, ch, ri, at, SE);
    }

    var al1 = parseLoci(p.loci1, maStr, _maSE);
    var al2 = parseLoci(p.loci2, maStr, _maSE);
    var al3 = parseLoci(p.loci3, maStr, _maSE);
    if (!al1 || !al2 || !al3) {
      log('measure_angle: 无法定位原子，参数格式: loci1=A:57:NE2', 'warn');
      setStatus('⚠ 无法定位原子（格式: chain:res:atom）', 'ok');
      return;
    }
    await maPlugin.managers.structure.measurement.addAngle(al1, al2, al3);
    log('✓ 角度测量已添加');
    setStatus('✓ 角度测量已添加', 'ok');
    hideStatus();
  } catch(e) { log('measure_angle 失败: ' + e.message, 'error'); }
}

async function opMeasureDihedral(ctx, p) {
  log('measure_dihedral');
  try {
    var mdPlugin = ctx.plugin;
    var mdHier = mdPlugin.managers.structure.hierarchy;
    if (!mdHier || !mdHier.current || !mdHier.current.structures || !mdHier.current.structures[0]) {
      log('measure_dihedral: 无结构对象', 'warn'); return;
    }
    var mdStr = mdHier.current.structures[0].cell.obj.data;
    var _mdSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_mdSE) { log('measure_dihedral: 无 StructureElement', 'error'); return; }

    function parseMdLoci(locStr, str, SE) {
      var parts = (locStr || '').split(':');
      if (parts.length < 2) return null;
      var ch = parts[0].toUpperCase(), ri = parseInt(parts[1]), at = (parts[2] || 'CA').toUpperCase();
      for (var u = 0; u < str.units.length; u++) {
        var unit = str.units[u];
        if (!unit.model) continue;
        var h = unit.model.atomicHierarchy;
        if (!h || !h.chainAtomSegments) continue;
        var authC = h.chains.auth_asym_id, lC = h.chains.label_asym_id;
        var lSeqs = h.residues.label_seq_id, aLabels = h.atoms.label_atom_id;
        var rSegs = h.residueAtomSegments, cSegs = h.chainAtomSegments;
        for (var ci = 0; ci < authC.rowCount; ci++) {
          if (authC.value(ci) !== ch && lC.value(ci) !== ch) continue;
          var cS = cSegs.offsets[ci], cE = cSegs.offsets[ci + 1];
          for (var ri2 = 0; ri2 < lSeqs.rowCount; ri2++) {
            var rS = rSegs.offsets[ri2];
            if (rS < cS || rS >= cE) continue;
            if (lSeqs.value(ri2) !== ri) continue;
            var aiS = rSegs.offsets[ri2], aiE = rSegs.offsets[ri2 + 1];
            for (var ai = aiS; ai < aiE; ai++) {
              if (aLabels.value(ai) === at) return SE.Loci(str, [{ unit: unit, indices: { size: 1, indices: new Int32Array([ai]) } }]);
            }
            if (aiS < aiE) return SE.Loci(str, [{ unit: unit, indices: { size: 1, indices: new Int32Array([aiS]) } }]);
          }
        }
      }
      return null;
    }

    var dl1 = parseMdLoci(p.loci1, mdStr, _mdSE);
    var dl2 = parseMdLoci(p.loci2, mdStr, _mdSE);
    var dl3 = parseMdLoci(p.loci3, mdStr, _mdSE);
    var dl4 = parseMdLoci(p.loci4, mdStr, _mdSE);
    if (!dl1 || !dl2 || !dl3 || !dl4) {
      log('measure_dihedral: 需要 4 个 loci，格式: chain:res:atom', 'warn');
      setStatus('⚠ 需要 4 个原子（格式: loci1=A:5:N）', 'ok');
      return;
    }
    await mdPlugin.managers.structure.measurement.addDihedral(dl1, dl2, dl3, dl4);
    log('✓ 二面角测量已添加');
    setStatus('✓ 二面角测量已添加', 'ok');
    hideStatus();
  } catch(e) { log('measure_dihedral 失败: ' + e.message, 'error'); }
}

async function opClearMeasurements(ctx) {
  log('clear_measurements');
  try {
    var cmPlugin = ctx.plugin;
    var state = cmPlugin.state.data;
    var found = [];

    state.cells.forEach(function(cell, ref) {
      if (cell && cell.obj) {
        var tags = cell.obj.tags || [];
        for (var ti = 0; ti < tags.length; ti++) {
          if (typeof tags[ti] === 'string' && tags[ti].indexOf('measurement') >= 0) {
            found.push({ ref: ref });
            break;
          }
        }
      }
      if (cell && cell.transform && cell.transform.tags) {
        var ttags = cell.transform.tags;
        for (var tti = 0; tti < ttags.length; tti++) {
          if (typeof ttags[tti] === 'string' && ttags[tti].indexOf('measurement') >= 0) {
            if (!found.some(function(f) { return f.ref === ref; })) {
              found.push({ ref: ref });
            }
          }
        }
      }
    });

    if (found.length > 0) {
      var cmUpd = cmPlugin.build();
      for (var fi2 = 0; fi2 < found.length; fi2++) {
        cmUpd.to(found[fi2].ref).delete();
      }
      await cmUpd.commit();
      log('✓ 测量已清除 (' + found.length + ' 个)');
      setStatus('✓ 测量已清除', 'ok');
    } else {
      log('测量: 未找到 measurement 标签的 cells', 'warn');
      setStatus('⚠ 无测量可清除', 'ok');
    }
    hideStatus();
  } catch(e) { log('clear_measurements 失败: ' + e.message, 'error'); }
}
