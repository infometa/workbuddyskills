// ========================================================================
// ops/a2-select.js — 残基选择/高亮操作
// 负责：opHighlight（case 'highlight_range' + 'highlight_list' fallthrough 统一处理）、
//       opClearHighlights（case 'clear_highlights'）、
//       opSelectByAtom（case 'select_by_atom'）、
//       opSelectByElement（case 'select_by_element'）、
//       opSelectLigand（case 'select_ligand'）、
//       opSelectWithin（case 'select_within'）、
//       opSelectByBfactor（case 'select_by_bfactor'）
// 依赖：utils.js（log, setStatus, hideStatus）
// ========================================================================

// opHighlight — 统一处理 highlight_range（→转换为列表后）和 highlight_list
async function opHighlight(ctx, p, op) {
  var hlChain2, hlResidues, hlColor2;
  if (op === 'highlight_range') {
    var hlChain = (p.chain || 'A').toUpperCase();
    var hlStart = parseInt(p.start || p.from || 1);
    var hlEnd   = parseInt(p.end || p.to || hlStart);
    hlColor2 = p.color || '#ff4444';
    log('highlight_range: ' + hlChain + ':' + hlStart + '-' + hlEnd);
    var hlRangeList = [];
    for (var rri = hlStart; rri <= hlEnd; rri++) hlRangeList.push(rri);
    hlChain2 = hlChain;
    hlResidues = hlRangeList;
  } else {
    hlChain2 = (p.chain || 'A').toUpperCase();
    hlResidues = (p.residues || []).map(function(r){ return parseInt(r); });
    hlColor2 = p.color || '#ff4444';
    log('highlight_list: ' + hlChain2 + ' [' + hlResidues.join(',') + ']');
  }

  if (!hlResidues.length) { log('残基列表为空', 'warn'); return; }

  try {
    var hlPlugin = ctx.plugin;

    var hlStrData = ctx.structure.obj && ctx.structure.obj.data;
    if (!hlStrData) { log('highlight: ctx.structure.obj.data 为空', 'error'); return; }

    var SE = null;
    if (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement) {
      SE = molstar.lib.structure.StructureElement;
    }
    if (!SE && molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure) {
      SE = molstar.lib['mol-model'].structure.StructureElement;
    }
    if (!SE) { log('highlight: 无法找到 StructureElement', 'error'); return; }

    function makeOrderedSet(arr) {
      return { size: arr.length, indices: new Int32Array(arr) };
    }

    var seqSet = {};
    hlResidues.forEach(function(r){ seqSet[r] = true; });

    var unitElements = [];
    var units = hlStrData.units;
    var modelHierarchy = hlStrData.model ? hlStrData.model.atomicHierarchy : null;

    for (var u = 0; u < units.length; u++) {
      var unit = units[u];
      var h = modelHierarchy;

      var authChains  = h.chains.auth_asym_id;
      var labelChains = h.chains.label_asym_id;
      var labelSeqs   = h.residues.label_seq_id;
      var authSeqs    = h.residues.auth_seq_id;
      var resSegs     = h.residueAtomSegments;
      var chainAtomSegs = h.chainAtomSegments;

      var matchedAtoms = [];
      for (var ci = 0; ci < authChains.rowCount; ci++) {
        var actualAuth = authChains.value(ci);
        var actualLabel = labelChains.value(ci);
        if (hlChain2 !== 'ALL' && actualAuth !== hlChain2 && actualLabel !== hlChain2) continue;
        var caStart = chainAtomSegs.offsets[ci];
        var caEnd   = chainAtomSegs.offsets[ci + 1];
        for (var ri = 0; ri < labelSeqs.rowCount; ri++) {
          var raStart = resSegs.offsets[ri];
          if (raStart < caStart || raStart >= caEnd) continue;
          if (!seqSet[labelSeqs.value(ri)] && !seqSet[authSeqs.value(ri)]) continue;
          var aiS = resSegs.offsets[ri];
          var aiE = resSegs.offsets[ri + 1];
          for (var ai = aiS; ai < aiE; ai++) {
            matchedAtoms.push(ai);
          }
        }
      }
      if (matchedAtoms.length > 0) {
        unitElements.push({ unit: unit, indices: makeOrderedSet(matchedAtoms) });
      }
    }

    if (unitElements.length === 0) {
      log('highlight: 未找到残基 [' + hlResidues.join(',') + '] 在链 ' + hlChain2, 'warn');
      return;
    }

    var loci = SE.Loci(hlStrData, unitElements);

    if (hlPlugin.managers.interactivity.lociSelects && hlPlugin.managers.interactivity.lociSelects.select) {
      hlPlugin.managers.interactivity.lociSelects.select({ loci: loci });
    } else if (hlPlugin.managers.interactivity.lociSelects) {
      hlPlugin.managers.interactivity.lociSelects.selectOnly({ loci: loci });
    } else if (hlPlugin.managers.interactivity.selection) {
      hlPlugin.managers.interactivity.selection.trigger({ loci: loci });
    }
    if (hlPlugin.managers.camera) {
      hlPlugin.managers.camera.focusLoci(loci);
    }

    ctx.highlights.push({ loci: loci, chain: hlChain2, residues: hlResidues });
    log('✓ 高亮 ' + hlResidues.length + ' 个残基: ' + hlResidues.join(','));
    setStatus('✓ 高亮 ' + hlResidues.length + ' 个残基', 'ok');
    hideStatus();
  } catch(e) { log('highlight_list 失败: ' + e.message, 'error'); }
}

async function opClearHighlights(ctx) {
  log('clear_highlights');
  try {
    var clPlugin = ctx.plugin;
    if (clPlugin.managers.interactivity.lociSelects && clPlugin.managers.interactivity.lociSelects.deselectAll) {
      clPlugin.managers.interactivity.lociSelects.deselectAll();
    } else if (clPlugin.managers.interactivity.lociSelects && clPlugin.managers.interactivity.lociSelects.select) {
      clPlugin.managers.interactivity.lociSelects.select({ loci: molstar.lib.structure.StructureElement.Loci.empty });
    } else if (clPlugin.managers.interactivity.selection) {
      clPlugin.managers.interactivity.clearSelects();
    } else {
      clPlugin.managers.camera.focusLoci(molstar.lib.structure.StructureElement.Loci.empty);
    }
    ctx.highlights = [];
    log('✓ 高亮已清除');
    setStatus('✓ 高亮已清除', 'ok');
    hideStatus();
  } catch(e) { log('clear_highlights 失败: ' + e.message, 'error'); }
}

async function opSelectByAtom(ctx, p) {
  var sbaAtom = (p.atom_name || p.atom || 'CA').toUpperCase();
  log('select_by_atom: ' + sbaAtom);
  try {
    var sbaPlugin = ctx.plugin;
    var sbaStr = ctx.structure && ctx.structure.obj && ctx.structure.obj.data;
    if (!sbaStr) { log('select_by_atom: 无结构', 'warn'); return; }
    var _sbaSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_sbaSE) { log('select_by_atom: 无 StructureElement', 'error'); return; }

    var sbaUnitElements = [];
    for (var sbau = 0; sbau < sbaStr.units.length; sbau++) {
      var sbaUnit = sbaStr.units[sbau];
      if (!sbaUnit.model) continue;
      var sbaH = sbaUnit.model.atomicHierarchy;
      if (!sbaH) continue;
      var sbaAL = sbaH.atoms.label_atom_id;
      var sbaMatchAtoms = [];
      for (var sbaai = 0; sbaai < sbaAL.rowCount; sbaai++) {
        if (sbaAL.value(sbaai) === sbaAtom) sbaMatchAtoms.push(sbaai);
      }
      if (sbaMatchAtoms.length > 0) {
        sbaUnitElements.push({ unit: sbaUnit, indices: { size: sbaMatchAtoms.length, indices: new Int32Array(sbaMatchAtoms) } });
      }
    }
    if (sbaUnitElements.length === 0) {
      log('select_by_atom: 未找到原子 ' + sbaAtom, 'warn');
      setStatus('⚠ 未找到原子: ' + sbaAtom, 'ok');
      return;
    }
    var sbaLoci = _sbaSE.Loci(sbaStr, sbaUnitElements);
    if (sbaPlugin.managers.interactivity && sbaPlugin.managers.interactivity.lociSelects) {
      sbaPlugin.managers.interactivity.lociSelects.selectOnly({ loci: sbaLoci });
    }
    if (sbaPlugin.managers.camera) sbaPlugin.managers.camera.focusLoci(sbaLoci);
    ctx.highlights.push({ loci: sbaLoci, chain: 'ALL', residues: [] });
    var totalAtoms = sbaUnitElements.reduce(function(s, ue) { return s + ue.indices.size; }, 0);
    log('✓ 选中 ' + totalAtoms + ' 个 ' + sbaAtom + ' 原子');
    setStatus('✓ 选中 ' + totalAtoms + ' 个 ' + sbaAtom + ' 原子', 'ok');
    hideStatus();
  } catch(e) { log('select_by_atom 失败: ' + e.message, 'error'); }
}

async function opSelectByElement(ctx, p) {
  var sbeElem = (p.element || 'ZN').toUpperCase();
  log('select_by_element: ' + sbeElem);
  try {
    var sbePlugin = ctx.plugin;
    var sbeStr = ctx.structure && ctx.structure.obj && ctx.structure.obj.data;
    if (!sbeStr) { log('select_by_element: 无结构', 'warn'); return; }
    var _sbeSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_sbeSE) { log('select_by_element: 无 StructureElement', 'error'); return; }

    var sbeUnitElements = [];
    for (var sbeu = 0; sbeu < sbeStr.units.length; sbeu++) {
      var sbeUnit = sbeStr.units[sbeu];
      if (!sbeUnit.model) continue;
      var sbeH = sbeUnit.model.atomicHierarchy;
      if (!sbeH) continue;
      var sbeAE = sbeH.atoms.type_symbol;
      if (!sbeAE) continue;
      var sbeMatchAtoms = [];
      for (var sbeai = 0; sbeai < sbeAE.rowCount; sbeai++) {
        if ((sbeAE.value(sbeai) || '').toUpperCase() === sbeElem) sbeMatchAtoms.push(sbeai);
      }
      if (sbeMatchAtoms.length > 0) {
        sbeUnitElements.push({ unit: sbeUnit, indices: { size: sbeMatchAtoms.length, indices: new Int32Array(sbeMatchAtoms) } });
      }
    }
    if (sbeUnitElements.length === 0) {
      log('select_by_element: 未找到元素 ' + sbeElem, 'warn');
      setStatus('⚠ 未找到元素: ' + sbeElem, 'ok');
      return;
    }
    var sbeLoci = _sbeSE.Loci(sbeStr, sbeUnitElements);
    if (sbePlugin.managers.interactivity && sbePlugin.managers.interactivity.lociSelects) {
      sbePlugin.managers.interactivity.lociSelects.selectOnly({ loci: sbeLoci });
    }
    if (sbePlugin.managers.camera) sbePlugin.managers.camera.focusLoci(sbeLoci);
    ctx.highlights.push({ loci: sbeLoci, chain: 'ALL', residues: [] });
    var totalSbeAtoms = sbeUnitElements.reduce(function(s, ue) { return s + ue.indices.size; }, 0);
    log('✓ 选中 ' + totalSbeAtoms + ' 个 ' + sbeElem + ' 元素原子');
    setStatus('✓ 选中 ' + totalSbeAtoms + ' 个 ' + sbeElem, 'ok');
    hideStatus();
  } catch(e) { log('select_by_element 失败: ' + e.message, 'error'); }
}

async function opSelectLigand(ctx, p) {
  var slCompId = (p.component_id || p.name || 'ATP').toUpperCase();
  log('select_ligand: ' + slCompId);
  try {
    var slPlugin = ctx.plugin;
    var slStr = ctx.structure && ctx.structure.obj && ctx.structure.obj.data;
    if (!slStr) { log('select_ligand: 无结构', 'warn'); return; }
    var _slSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_slSE) { log('select_ligand: 无 StructureElement', 'error'); return; }

    var slUnitElements = [];
    for (var slu = 0; slu < slStr.units.length; slu++) {
      var slUnit = slStr.units[slu];
      if (!slUnit.model) continue;
      var slH = slUnit.model.atomicHierarchy;
      if (!slH) continue;
      var slCompIds = slH.residues.auth_comp_id || slH.residues.label_comp_id;
      if (!slCompIds) continue;
      var slRSegs = slH.residueAtomSegments;
      var slMatchAtoms = [];
      for (var slri = 0; slri < slCompIds.rowCount; slri++) {
        if ((slCompIds.value(slri) || '').toUpperCase() !== slCompId) continue;
        var slaiS = slRSegs.offsets[slri], slaiE = slRSegs.offsets[slri + 1];
        for (var slai = slaiS; slai < slaiE; slai++) slMatchAtoms.push(slai);
      }
      if (slMatchAtoms.length > 0) {
        slUnitElements.push({ unit: slUnit, indices: { size: slMatchAtoms.length, indices: new Int32Array(slMatchAtoms) } });
      }
    }
    if (slUnitElements.length === 0) {
      log('select_ligand: 未找到配体 ' + slCompId, 'warn');
      setStatus('⚠ 未找到配体: ' + slCompId, 'ok');
      return;
    }
    var slLoci = _slSE.Loci(slStr, slUnitElements);
    if (slPlugin.managers.interactivity && slPlugin.managers.interactivity.lociSelects) {
      slPlugin.managers.interactivity.lociSelects.selectOnly({ loci: slLoci });
    }
    if (slPlugin.managers.camera) slPlugin.managers.camera.focusLoci(slLoci);
    ctx.highlights.push({ loci: slLoci, chain: 'ALL', residues: [] });
    var totalSlAtoms = slUnitElements.reduce(function(s, ue) { return s + ue.indices.size; }, 0);
    log('✓ 选中 ' + slCompId + '：' + totalSlAtoms + ' 个原子（' + slUnitElements.length + ' 个实例）');
    setStatus('✓ 选中 ' + slCompId + ' (' + slUnitElements.length + ' 实例)', 'ok');
    hideStatus();
  } catch(e) { log('select_ligand 失败: ' + e.message, 'error'); }
}

async function opSelectWithin(ctx, p) {
  var swAnchor = (p.anchor_ligand || p.anchor || '').toUpperCase();
  var swDist = parseFloat(p.distance || p.within || 5.0);
  var swChain = (p.chain || '').toUpperCase();
  log('select_within: anchor=' + swAnchor + ' dist=' + swDist);
  try {
    var swPlugin = ctx.plugin;
    var swStr = ctx.structure && ctx.structure.obj && ctx.structure.obj.data;
    if (!swStr) { log('select_within: 无结构', 'warn'); return; }
    var _swSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_swSE) { log('select_within: 无 StructureElement', 'error'); return; }

    // Step 1: 获取锚点原子坐标
    var swXYZ = swStr.units[0] && swStr.units[0].model && swStr.units[0].model.atomicConformation;
    if (!swXYZ) { log('select_within: 无原子坐标', 'warn'); return; }
    var swAnchorAtoms = []; // [{x,y,z}]
    for (var swu = 0; swu < swStr.units.length; swu++) {
      var swUnit = swStr.units[swu];
      if (!swUnit.model) continue;
      var swH = swUnit.model.atomicHierarchy;
      var swConf = swUnit.model.atomicConformation;
      if (!swH || !swConf) continue;
      var swCompIds = swH.residues.auth_comp_id || swH.residues.label_comp_id;
      if (!swCompIds) continue;
      var swRSegs = swH.residueAtomSegments;
      for (var swri = 0; swri < swCompIds.rowCount; swri++) {
        if ((swCompIds.value(swri) || '').toUpperCase() !== swAnchor) continue;
        var swaiS2 = swRSegs.offsets[swri], swaiE2 = swRSegs.offsets[swri + 1];
        for (var swai2 = swaiS2; swai2 < swaiE2; swai2++) {
          swAnchorAtoms.push({
            x: swConf.x.value(swai2),
            y: swConf.y.value(swai2),
            z: swConf.z.value(swai2)
          });
        }
      }
    }
    if (swAnchorAtoms.length === 0) {
      log('select_within: 未找到锚点 ' + swAnchor, 'warn');
      setStatus('⚠ 未找到锚点配体: ' + swAnchor, 'ok');
      return;
    }

    // Step 2: 找所有 swDist Å 内的残基
    var swDistSq = swDist * swDist;
    var swResSet = {}; // unit_idx -> [atomIdx]
    for (var swu2 = 0; swu2 < swStr.units.length; swu2++) {
      var swUnit2 = swStr.units[swu2];
      if (!swUnit2.model) continue;
      var swH2 = swUnit2.model.atomicHierarchy;
      var swConf2 = swUnit2.model.atomicConformation;
      if (!swH2 || !swConf2) continue;
      var swChainAC = swH2.chains.auth_asym_id;
      var swCompIds2 = swH2.residues.auth_comp_id || swH2.residues.label_comp_id;
      var swRSegs2 = swH2.residueAtomSegments;
      var swCSegs2 = swH2.chainAtomSegments;
      var standard2 = ['HOH','WAT','H2O'];

      for (var swri2 = 0; swri2 < swRSegs2.offsets.length - 1; swri2++) {
        var swResName = swCompIds2 ? swCompIds2.value(swri2) : '';
        if (swResName.toUpperCase() === swAnchor) continue; // 排除锚点自身
        if (standard2.indexOf(swResName.toUpperCase()) >= 0 && !p.include_water) continue;

        var swaiS3 = swRSegs2.offsets[swri2], swaiE3 = swRSegs2.offsets[swri2 + 1];
        var isNear = false;
        for (var swai3 = swaiS3; swai3 < swaiE3 && !isNear; swai3++) {
          var ax = swConf2.x.value(swai3);
          var ay = swConf2.y.value(swai3);
          var az = swConf2.z.value(swai3);
          for (var swanc = 0; swanc < swAnchorAtoms.length && !isNear; swanc++) {
            var dx = ax - swAnchorAtoms[swanc].x;
            var dy = ay - swAnchorAtoms[swanc].y;
            var dz = az - swAnchorAtoms[swanc].z;
            if (dx*dx + dy*dy + dz*dz <= swDistSq) isNear = true;
          }
        }
        if (isNear) {
          if (!swResSet[swu2]) swResSet[swu2] = { unit: swUnit2, atoms: [] };
          for (var swai4 = swaiS3; swai4 < swaiE3; swai4++) swResSet[swu2].atoms.push(swai4);
        }
      }
    }

    var swUE = Object.keys(swResSet).map(function(k) {
      var item = swResSet[k];
      return { unit: item.unit, indices: { size: item.atoms.length, indices: new Int32Array(item.atoms) } };
    });

    if (swUE.length === 0) {
      log('select_within: ' + swAnchor + ' 周围 ' + swDist + ' Å 内无残基', 'warn');
      setStatus('⚠ 未选中任何残基', 'ok');
      return;
    }
    var swLoci = _swSE.Loci(swStr, swUE);
    if (swPlugin.managers.interactivity && swPlugin.managers.interactivity.lociSelects) {
      swPlugin.managers.interactivity.lociSelects.selectOnly({ loci: swLoci });
    }
    if (swPlugin.managers.camera) swPlugin.managers.camera.focusLoci(swLoci);
    ctx.highlights.push({ loci: swLoci, chain: 'ALL', residues: [] });
    var swTotalAtoms = swUE.reduce(function(s, ue) { return s + ue.indices.size; }, 0);
    log('✓ ' + swAnchor + ' 周围 ' + swDist + ' Å：' + swUE.length + ' 个残基，共 ' + swTotalAtoms + ' 个原子');
    setStatus('✓ 选中 ' + swUE.length + ' 个残基（' + swDist + ' Å 内）', 'ok');
    hideStatus();
  } catch(e) { log('select_within 失败: ' + e.message, 'error'); }
}

async function opSelectByBfactor(ctx, p) {
  var sbfOp = (p.op || 'gt').toLowerCase();
  var sbfVal = parseFloat(p.value || 50);
  log('select_by_bfactor: B-factor ' + sbfOp + ' ' + sbfVal);
  try {
    var sbfPlugin = ctx.plugin;
    var sbfStr = ctx.structure && ctx.structure.obj && ctx.structure.obj.data;
    if (!sbfStr) { log('select_by_bfactor: 无结构', 'warn'); return; }
    var _sbfSE = (molstar.lib && molstar.lib.structure && molstar.lib.structure.StructureElement)
      || (molstar.lib && molstar.lib['mol-model'] && molstar.lib['mol-model'].structure && molstar.lib['mol-model'].structure.StructureElement);
    if (!_sbfSE) { log('select_by_bfactor: 无 StructureElement', 'error'); return; }

    var sbfUE = [];
    for (var sbfu = 0; sbfu < sbfStr.units.length; sbfu++) {
      var sbfUnit = sbfStr.units[sbfu];
      if (!sbfUnit.model) continue;
      var sbfConf = sbfUnit.model.atomicConformation;
      if (!sbfConf || !sbfConf.B_iso_or_equiv) continue;
      var sbfBF = sbfConf.B_iso_or_equiv;
      var sbfMatchAtoms = [];
      for (var sbfai = 0; sbfai < sbfBF.rowCount; sbfai++) {
        var bfv = sbfBF.value(sbfai);
        var match = sbfOp === 'gt' ? bfv > sbfVal
                  : sbfOp === 'lt' ? bfv < sbfVal
                  : sbfOp === 'gte' ? bfv >= sbfVal
                  : sbfOp === 'lte' ? bfv <= sbfVal
                  : bfv === sbfVal;
        if (match) sbfMatchAtoms.push(sbfai);
      }
      if (sbfMatchAtoms.length > 0) {
        sbfUE.push({ unit: sbfUnit, indices: { size: sbfMatchAtoms.length, indices: new Int32Array(sbfMatchAtoms) } });
      }
    }
    if (sbfUE.length === 0) {
      log('select_by_bfactor: 无匹配原子', 'warn');
      setStatus('⚠ 无 B-factor 匹配原子', 'ok');
      return;
    }
    var sbfLoci = _sbfSE.Loci(sbfStr, sbfUE);
    if (sbfPlugin.managers.interactivity && sbfPlugin.managers.interactivity.lociSelects) {
      sbfPlugin.managers.interactivity.lociSelects.selectOnly({ loci: sbfLoci });
    }
    if (sbfPlugin.managers.camera) sbfPlugin.managers.camera.focusLoci(sbfLoci);
    ctx.highlights.push({ loci: sbfLoci, chain: 'ALL', residues: [] });
    var sbfTotal = sbfUE.reduce(function(s, ue) { return s + ue.indices.size; }, 0);
    log('✓ B-factor ' + sbfOp + ' ' + sbfVal + '：选中 ' + sbfTotal + ' 个原子');
    setStatus('✓ B-factor ' + sbfOp + ' ' + sbfVal + '：' + sbfTotal + ' 原子', 'ok');
    hideStatus();
  } catch(e) { log('select_by_bfactor 失败: ' + e.message, 'error'); }
}
