// 给定一组编号字符串(如 ["01","03"],已按数值升序排列),返回从最小号到最大号之间
// 缺失的号(补齐位宽,如 "02")。不足 2 个号无所谓连续性,返回 []。
// check-slots.mjs(掏钱前的 NN.scene.json 编号)与 build-manifest.mjs(NN.* 任意资源编号)共用同一份逻辑,
// 保证"编号连续性"的判定口径一致:以现有号里最小到最大之间不缺为准,不要求从 01 开始。
export function findMissingNumbers(numbers) {
  if (numbers.length < 2) return [];
  const width = numbers[0].length;
  const present = new Set(numbers.map(Number));
  const min = Number(numbers[0]);
  const max = Number(numbers[numbers.length - 1]);
  const missing = [];
  for (let i = min; i <= max; i++) {
    if (!present.has(i)) missing.push(String(i).padStart(width, "0"));
  }
  return missing;
}

// scenes.json 的场景校验(纯逻辑)。manifest = resolveBundle().manifestPath 指向的那份
//(免费 manifest 只含 serious-dark 一个主题;完整 manifest 含 50 个,run.mjs unlock 解锁后生效)。
export function validateScenes(scenes, manifest) {
  const byId = new Map(manifest.layouts.map((l) => [l.id, l]));
  // 版式(layout)全部免费,不受门禁——只有主题(theme)按 manifest.themes 认。manifest 没带
  // themes 字段(如部分老测试 fixture)时不校验主题,保持向后兼容。
  const themeIds = Array.isArray(manifest.themes) ? new Set(manifest.themes.map((t) => t.id)) : null;
  const errors = [];
  scenes.forEach((s, i) => {
    const n = i + 1;
    if (!(s.durationInFrames > 0)) errors.push({ n, reason: "durationInFrames 必须为正" });
    if (themeIds && s.themeId != null && s.themeId !== "" && !themeIds.has(s.themeId)) {
      errors.push({ n, reason: `主题 "${s.themeId}" 不可用 —— 该主题属完整主题库,连接 VibeKnow(免费)即可解锁 50 个主题` });
    }
    const L = byId.get(s.layout);
    if (!L) { errors.push({ n, reason: `未知 layout: ${s.layout}` }); return; }
    for (const slot of L.slots) {
      const v = s.slots?.[slot.name];
      if (slot.required && (v == null || v === "" || (Array.isArray(v) && v.length === 0)))
        errors.push({ n, reason: `缺必填 slot: ${slot.name}` });
      if (slot.type === "text" && v != null && typeof v !== "string")
        errors.push({ n, reason: `${slot.name} 类型应为文本(得 ${typeof v})` });
      if (slot.type === "text" && typeof v === "string" && slot.maxLength && v.length > slot.maxLength)
        errors.push({ n, reason: `${slot.name} 超长(${v.length}>${slot.maxLength})` });
      if (slot.type === "textArray" && Array.isArray(v) && slot.maxItems && v.length > slot.maxItems)
        errors.push({ n, reason: `${slot.name} 超 maxItems(${v.length}>${slot.maxItems})` });
    }
  });
  return { ok: errors.length === 0, errors };
}
