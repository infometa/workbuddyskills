// ========================================================================
// ops/a11-query.js — 结构信息查询
// 负责：opListChains、opListLigands、opListModels、opGetBfactor、opGetInfo
// 依赖：utils.js（log, setStatus）
// ========================================================================

async function opListChains(ctx) {
  log('list_chains');
  try {
    var lcPlugin = ctx.plugin;
    var lcHier = lcPlugin.managers.structure.hierarchy;
    if (!lcHier || !lcHier.current || !lcHier.current.structures || !lcHier.current.structures[0]) {
      log('list_chains: 无结构', 'warn'); return;
    }
    var lcStr = lcHier.current.structures[0].cell.obj;
    var chains = [];
    if (lcStr && lcStr.data && lcStr.data.model && lcStr.data.model.atomicHierarchy) {
      var ah = lcStr.data.model.atomicHierarchy;
      var seen = {};
      for (var lci = 0; lci < ah.chains._rowCount; lci++) {
        var cid = ah.chains.auth_asym_id.value(lci);
        if (!seen[cid]) { seen[cid] = true; chains.push(cid); }
      }
    }
    var chainText = '链列表 (' + chains.length + '): ' + chains.join(', ');
    log('✓ ' + chainText);
    setStatus(chainText, 'ok');
    // 通过 /api/query-result 反馈链列表（供 LLM 读取）
    try {
      fetch('/api/query-result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ op: 'list_chains', result: chains }),
        keepalive: true
      }).catch(function(){});
    } catch(_e) {}
  } catch(e) { log('list_chains 失败: ' + e.message, 'error'); }
}

async function opListLigands(ctx) {
  log('list_ligands');
  try {
    var llPlugin = ctx.plugin;
    var llHier = llPlugin.managers.structure.hierarchy;
    if (!llHier || !llHier.current || !llHier.current.structures || !llHier.current.structures[0]) {
      log('list_ligands: 无结构', 'warn'); return;
    }
    var llStr = llHier.current.structures[0].cell.obj;
    var ligands = {};
    if (llStr && llStr.data && llStr.data.model && llStr.data.model.atomicHierarchy) {
      var llAh = llStr.data.model.atomicHierarchy;
      for (var lli = 0; lli < llAh.residues._rowCount; lli++) {
        var resn = llAh.residues.auth_comp_id ? llAh.residues.auth_comp_id.value(lli) : '';
        // 非标准残基（简单判断：不是常见氨基酸/核苷酸/水）
        var standard = ['ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE',
          'LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL',
          'DA','DC','DG','DT','DU','RA','RC','RG','RT','RU',
          'A','C','G','T','U','HOH','WAT','H2O'];
        if (resn && standard.indexOf(resn) < 0) {
          ligands[resn] = (ligands[resn] || 0) + 1;
        }
      }
    }
    var ligArr = Object.keys(ligands).map(function(k) { return { name: k, count: ligands[k] }; });
    var ligText = '配体列表 (' + ligArr.length + '): ' + ligArr.map(function(l) { return l.name + '×' + l.count; }).join(', ');
    log('✓ ' + ligText);
    setStatus(ligText, 'ok');
    try {
      fetch('/api/query-result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ op: 'list_ligands', result: ligArr }),
        keepalive: true
      }).catch(function(){});
    } catch(_e) {}
  } catch(e) { log('list_ligands 失败: ' + e.message, 'error'); }
}

async function opListModels(ctx) {
  log('list_models');
  try {
    var lmPlugin = ctx.plugin;
    var lmHier = lmPlugin.managers.structure.hierarchy;
    var lmCount = 0;
    if (lmHier && lmHier.current && lmHier.current.structures) {
      lmCount = lmHier.current.structures.length;
    }
    // 从 trajectory 获取模型数
    if (ctx.trajectory && ctx.trajectory.obj && ctx.trajectory.obj.data) {
      lmCount = ctx.trajectory.obj.data.frameCount || lmCount;
    }
    var lmText = '模型数: ' + lmCount;
    log('✓ ' + lmText);
    setStatus(lmText, 'ok');
  } catch(e) { log('list_models 失败: ' + e.message, 'error'); }
}

async function opGetBfactor(ctx, p) {
  var bfChain = (p.chain || 'A').toUpperCase();
  var bfRes = parseInt(p.residue || p.res || 0);
  log('get_bfactor: ' + bfChain + ':' + bfRes);
  try {
    var bfPlugin = ctx.plugin;
    var bfHier = bfPlugin.managers.structure.hierarchy;
    if (!bfHier || !bfHier.current || !bfHier.current.structures || !bfHier.current.structures[0]) {
      log('get_bfactor: 无结构', 'warn'); return;
    }
    var bfStr = bfHier.current.structures[0].cell.obj.data;
    var bfResults = [];
    for (var bu = 0; bu < bfStr.units.length; bu++) {
      var bfUnit = bfStr.units[bu];
      if (!bfUnit.model) continue;
      var bfH = bfUnit.model.atomicHierarchy;
      if (!bfH || !bfH.chainAtomSegments) continue;
      var bfAC = bfH.chains.auth_asym_id, bfLC = bfH.chains.label_asym_id;
      var bfSeqs = bfH.residues.label_seq_id;
      var bfAtomLabels = bfH.atoms.label_atom_id;
      var bfBFactors = bfUnit.model.atomicConformation && bfUnit.model.atomicConformation.B_iso_or_equiv;
      if (!bfBFactors) continue;
      var bfRSegs = bfH.residueAtomSegments, bfCSegs = bfH.chainAtomSegments;
      for (var bfci = 0; bfci < bfAC.rowCount; bfci++) {
        if (bfAC.value(bfci) !== bfChain && bfLC.value(bfci) !== bfChain) continue;
        var bfcS = bfCSegs.offsets[bfci], bfcE = bfCSegs.offsets[bfci + 1];
        for (var bfri = 0; bfri < bfSeqs.rowCount; bfri++) {
          var bfrS = bfRSegs.offsets[bfri];
          if (bfrS < bfcS || bfrS >= bfcE) continue;
          if (bfSeqs.value(bfri) !== bfRes) continue;
          var bfaiS = bfRSegs.offsets[bfri], bfaiE = bfRSegs.offsets[bfri + 1];
          for (var bfai = bfaiS; bfai < bfaiE; bfai++) {
            bfResults.push({ atom: bfAtomLabels.value(bfai), bfactor: bfBFactors.value(bfai) });
          }
        }
      }
    }
    if (bfResults.length === 0) {
      log('get_bfactor: 未找到残基 ' + bfChain + ':' + bfRes, 'warn');
      setStatus('⚠ 未找到残基 ' + bfChain + ':' + bfRes, 'ok');
      return;
    }
    var bfText = bfChain + ':' + bfRes + ' B-factors: ' + bfResults.slice(0,5).map(function(r) {
      return r.atom + '=' + r.bfactor.toFixed(2);
    }).join(', ') + (bfResults.length > 5 ? '...' : '');
    log('✓ ' + bfText);
    setStatus(bfText, 'ok');
  } catch(e) { log('get_bfactor 失败: ' + e.message, 'error'); }
}

async function opGetInfo(ctx) {
  log('get_info');
  try {
    var infoPlugin = ctx.plugin;
    var hier3 = infoPlugin.managers.structure.hierarchy;
    var info = { name: ctx.pdbName };
    if (hier3 && hier3.current && hier3.current.structures && hier3.current.structures[0]) {
      var infoStr = hier3.current.structures[0].cell.obj;
      if (infoStr && infoStr.data) {
        var model2 = infoStr.data;
        if (model2.model && model2.model.atomicHierarchy) {
          var ah = model2.model.atomicHierarchy;
          info.chainCount = ah.chains._rowCount;
          info.residueCount = ah.residues._rowCount;
          info.elementCount = ah.atoms._rowCount;
        } else {
          info.elementCount = model2.elementCount || '?';
          info.residueCount = '?';
          info.chainCount = model2.unitSymmetryGroups ? model2.unitSymmetryGroups.length : '?';
        }
      }
    }
    var infoText = [
      '文件: ' + info.name,
      '链数: ' + info.chainCount,
      '残基数: ' + info.residueCount,
      '原子数: ' + info.elementCount,
    ].join('\n');
    log('✓ 信息: ' + infoText.replace(/\n/g,' | '));
    setStatus(infoText, 'ok');
  } catch(e) { log('get_info 失败: ' + e.message, 'error'); }
}
