// ========================================================================
// executor.js — 操作执行器（核心分发器）
// 负责：executeOp(cmd) — 解析命令，分发到各 ops/ 模块函数
// 依赖：utils.js（log, setStatus）、所有 ops/ 模块（需在本文件前加载）
// ========================================================================

async function executeOp(cmd) {
  var ctx = window.__pdbCtx;
  // 兼容旧格式 {action, ...} 和新格式 {op, params}
  var op = cmd.op || cmd.action || '';
  var p = cmd.params || cmd;

  log('[OP] ' + op + ' ' + JSON.stringify(p).substring(0, 60));
  setStatus('[' + op + ']', 'loading');

  if (!ctx || !ctx.plugin) {
    if (op === 'reset_view' || op === 'screenshot' || op === 'get_pdb') {
      // 这些操作不依赖结构上下文（get_pdb 负责创建上下文）
    } else {
      log('上下文未就绪，跳过: ' + op, 'warn');
      return;
    }
  }

  switch(op) {

  // ---- a1-load ----
  case 'get_pdb': {
    await opGetPdb(ctx, p);
    break;
  }

  // ---- a4-repr ----
  case 'set_repr': {
    await opSetRepr(ctx, p);
    break;
  }
  case 'set_repr_by_component': {
    await opSetReprByComponent(ctx, p);
    break;
  }

  // ---- a5-color-opacity ----
  case 'set_color': {
    await opSetColor(ctx, p);
    break;
  }
  case 'set_color_selection': {
    await opSetColorSelection(ctx, p);
    break;
  }
  case 'set_opacity': {
    await opSetOpacity(ctx, p);
    break;
  }
  case 'set_bg': {
    await opSetBg(ctx, p);
    break;
  }

  // ---- a3-visibility ----
  case 'set_water': {
    await opSetWater(ctx, p);
    break;
  }
  case 'chain_visibility': {
    await opChainVisibility(ctx, p);
    break;
  }
  case 'ligand_visibility': {
    await opLigandVisibility(ctx, p);
    break;
  }
  case 'isolate': {
    await opIsolate(ctx, p);
    break;
  }
  case 'show_all': {
    await opShowAll(ctx);
    break;
  }
  case 'hide_hydrogens': {
    await opHideHydrogens(ctx, p);
    break;
  }
  case 'show_backbone_only': {
    await opShowBackboneOnly(ctx, p);
    break;
  }

  // ---- a8-camera ----
  case 'focus_chain': {
    await opFocusChain(ctx, p);
    break;
  }
  case 'focus_selection': {
    await opFocusSelection(ctx);
    break;
  }

  // ---- a2-select ----
  case 'highlight_range':
  case 'highlight_list': {
    await opHighlight(ctx, p, op);
    break;
  }
  case 'clear_highlights': {
    await opClearHighlights(ctx);
    break;
  }

  // ---- a9-measure ----
  case 'measure_dist': {
    await opMeasureDist(ctx, p);
    break;
  }
  case 'measure_angle': {
    await opMeasureAngle(ctx, p);
    break;
  }
  case 'measure_dihedral': {
    await opMeasureDihedral(ctx, p);
    break;
  }
  case 'clear_measurements': {
    await opClearMeasurements(ctx);
    break;
  }

  // ---- a12-export ----
  case 'screenshot_transparent':
  case 'screenshot': {
    await opScreenshot(ctx, p, op);
    break;
  }
  case 'export_selection': {
    await opExportSelection(ctx, p);
    break;
  }
  case 'export_filtered': {
    await opExportFiltered(ctx, p);
    break;
  }
  case 'save_scene': {
    await opSaveScene(ctx, p);
    break;
  }
  case 'load_scene': {
    await opLoadScene(ctx, p);
    break;
  }
  case 'save_pdb': {
    await opSavePdb(ctx, p);
    break;
  }

  // ---- a8-camera (续) ----
  case 'save_view': {
    await opSaveView(ctx, p);
    break;
  }
  case 'restore_view': {
    await opRestoreView(ctx, p);
    break;
  }
  case 'set_projection': {
    await opSetProjection(ctx, p);
    break;
  }

  // ---- a10-interact ----
  case 'show_hbonds':
  case 'show_metal_coord':
  case 'show_salt_bridges':
  case 'show_hydrophobic':
  case 'show_clashes': {
    await opShowInteractions(ctx, op);
    break;
  }
  case 'clear_interactions': {
    await opClearInteractions(ctx);
    break;
  }

  // ---- a7-label ----
  case 'add_label': {
    await opAddLabel(ctx, p);
    break;
  }
  case 'auto_label_selection': {
    await opAutoLabelSelection(ctx);
    break;
  }
  case 'clear_labels': {
    await opClearLabels(ctx);
    break;
  }

  // ---- a11-query ----
  case 'list_chains': {
    await opListChains(ctx);
    break;
  }
  case 'list_ligands': {
    await opListLigands(ctx);
    break;
  }
  case 'list_models': {
    await opListModels(ctx);
    break;
  }
  case 'get_bfactor': {
    await opGetBfactor(ctx, p);
    break;
  }
  case 'get_info': {
    await opGetInfo(ctx);
    break;
  }

  // ---- a2-select (续) ----
  case 'select_by_atom': {
    await opSelectByAtom(ctx, p);
    break;
  }
  case 'select_by_element': {
    await opSelectByElement(ctx, p);
    break;
  }
  case 'select_ligand': {
    await opSelectLigand(ctx, p);
    break;
  }
  case 'select_within': {
    await opSelectWithin(ctx, p);
    break;
  }
  case 'select_by_bfactor': {
    await opSelectByBfactor(ctx, p);
    break;
  }

  // ---- a8-camera (续) ----
  case 'spin': {
    await opSpin(ctx, p);
    break;
  }
  case 'reset_view': {
    await opResetView(ctx);
    break;
  }

  // ---- 引导使用内置录制 ----
  case 'record_video': {
    log('record_video (引导使用 Mol* 内置录制 UI)');
    setStatus('请使用 Mol* 内置录制功能（右上角相机图标）', 'loading');
    setTimeout(function() { hideStatus(0); }, 3000);
    break;
  }

  default:
    log('未知操作: ' + op, 'warn');
  }
}
