// ========================================================================
// loader.js — 结构加载流程
// 负责：loadStructure（Mol* 手动 builder 链式加载）、fetchAndLoad（获取 PDB 数据）
// 依赖：utils.js（log, setStatus, hideStatus, guessFormat）
// ========================================================================

// 核心上下文（持久化，全生命周期使用）
// window.__pdbCtx = {
//   plugin,          // PluginUIContext (viewer.plugin)
//   viewer,          // Viewer wrapper
//   structure,       // StateObjectCell - structure 节点引用
//   trajectory,      // StateObjectCell - trajectory 节点引用
//   components: {    // polymer/ligand/water 等组件引用
//     polymer, ligand, water
//   },
//   highlights: [],  // highlight 组件 ref 数组
//   pdbName,         // 文件名
//   pdbPath,         // 服务端绝对路径（用于保存）
//   waterHidden,     // 水分子当前可见状态
//   chainVisibility, // { 'A': true/false }
// }

window.__pdbCtx = null;

async function loadStructure(plugin, pdbText, fmt, name, path) {
  log('开始加载: ' + name + ' (' + fmt + ')');
  setStatus('解析结构数据…', 'loading');

  // Step 1: 上传原始文本数据
  var data = await plugin.builders.data.rawData(
    { data: pdbText, label: name },
    { state: { isGhost: true } }
  );
  log('Step1 data node OK');

  // Step 2: 解析轨迹
  var trajectory = await plugin.builders.structure.parseTrajectory(data, fmt);
  log('Step2 trajectory OK');

  // Step 3: 创建模型
  var model = await plugin.builders.structure.createModel(trajectory);
  log('Step3 model OK');

  // Step 4: 创建结构
  var structure = await plugin.builders.structure.createStructure(model);
  log('Step4 structure OK');

  // Step 5: 创建分组件（polymer / ligand / water）
  var polymer = await plugin.builders.structure.tryCreateComponentStatic(structure, 'polymer');
  var ligand  = await plugin.builders.structure.tryCreateComponentStatic(structure, 'ligand');
  var water   = await plugin.builders.structure.tryCreateComponentStatic(structure, 'water');
  log('Step5 components: polymer=' + !!polymer + ' ligand=' + !!ligand + ' water=' + !!water);

  // Step 6: 添加默认表示
  var reprBuilder = plugin.builders.structure.representation;
  var update = plugin.build();
  if (polymer) reprBuilder.buildRepresentation(update, polymer, { type: 'cartoon', color: 'chain-id' }, { tag: 'polymer-repr' });
  if (ligand)  reprBuilder.buildRepresentation(update, ligand,  { type: 'ball-and-stick', color: 'element-symbol' }, { tag: 'ligand-repr' });
  if (water)   reprBuilder.buildRepresentation(update, water,   { type: 'ball-and-stick', typeParams: { alpha: 0.4 } }, { tag: 'water-repr' });
  await update.commit();
  log('Step6 representations OK');

  // 自动对焦相机
  setTimeout(function() {
    try { plugin.canvas3d && plugin.canvas3d.requestCameraReset(); } catch(e){}
  }, 200);

  // 持久化上下文
  window.__pdbCtx = {
    plugin: plugin,
    viewer: window.__molstarViewer,
    structure: structure,
    trajectory: trajectory,
    components: { polymer: polymer, ligand: ligand, water: water },
    highlights: [],
    pdbName: name,
    pdbPath: path || null,
    waterHidden: false,
    chainVisibility: {},
  };

  log('✓ 加载完成: ' + name);
  setStatus('✓ ' + name, 'ok');
  hideStatus(2000);
}

async function fetchAndLoad(plugin) {
  var params = new URLSearchParams(location.search);
  var pdbParam = params.get('pdb');
  var nameParam = params.get('name');

  // ★ 优先：检查服务端预加载缓存（LLM 在 present_files 前已调用 /api/preload）
  try {
    var preResp = await fetch('/api/preloaded-pdb', { cache: 'no-store' });
    if (preResp.ok) {
      var preData = await preResp.json();
      if (preData.data && preData.name) {
        log('使用预加载缓存: ' + preData.name);
        var pdbText = atob(preData.data);
        var fmt = guessFormat(preData.name);
        await loadStructure(plugin, pdbText, fmt, preData.name, null);
        return;
      }
    }
  } catch(_e) {}

  if (!pdbParam) {
    // 从 API 获取默认 PDB（serve_pdb.py 启动时 --pdb-file 指定的文件）
    try {
      var r = await fetch('/api/pdb-url', { cache: 'no-store' });
      var d = await r.json();
      if (!d.url) { setStatus('未指定 PDB 文件', 'error'); return; }
      pdbParam = d.url;
      nameParam = nameParam || d.name;
    } catch(e) {
      setStatus('获取 PDB URL 失败: ' + e.message, 'error'); return;
    }
  }

  var name = nameParam || pdbParam.split('/').pop() || 'structure.pdb';
  var fmt = guessFormat(name);

  // 确定 fetch URL 和路径类型
  var fetchUrl;
  var serverPath = null;
  var isProxied = false;

  if (pdbParam.indexOf('cos://') === 0) {
    // cos:// 协议 → 通过 /__cos 代理（omics 认证 + GetObjectData）
    fetchUrl = '/__cos?uri=' + encodeURIComponent(pdbParam);
    isProxied = true;
  } else if (pdbParam.indexOf('/__file?path=') === 0 || pdbParam.indexOf('/__cos?uri=') === 0) {
    // 已经是代理 URL（/api/pdb-url 返回的格式），直接使用
    fetchUrl = pdbParam;
    isProxied = true;
    // 从 /__file?path=... 中提取原始路径，用于保存
    var pathMatch = pdbParam.match(/\/__file\?path=(.+)/);
    if (pathMatch) serverPath = decodeURIComponent(pathMatch[1]);
  } else if (pdbParam.indexOf('/') === 0) {
    // 绝对路径（如 /Users/...）→ 通过 /__file 代理
    serverPath = pdbParam;
    fetchUrl = '/__file?path=' + encodeURIComponent(pdbParam);
    isProxied = true;
  } else {
    // 相对路径或完整 HTTP URL → 直接 fetch
    fetchUrl = pdbParam;
    isProxied = false;
  }

  setStatus('正在获取 ' + name + '…', 'loading');

  try {
    var resp = await fetch(fetchUrl, { cache: 'no-store' });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);

    var pdbText;
    if (isProxied) {
      var obj = await resp.json();
      if (obj.error) throw new Error(obj.error);
      // base64 → text（与 serve_pdb.py 返回的 { data, name, path } 对应）
      pdbText = atob(obj.data);
      name = obj.name || name;
      serverPath = obj.path || serverPath;
    } else {
      pdbText = await resp.text();
    }

    await loadStructure(plugin, pdbText, fmt, name, serverPath);
  } catch(e) {
    log('获取失败: ' + e.message, 'error');
    setStatus('加载失败: ' + e.message, 'error');
  }
}
