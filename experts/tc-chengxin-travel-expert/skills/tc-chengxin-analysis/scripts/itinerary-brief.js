'use strict';

const { buildSelectionBrief } = require('./selection-brief');

const CATEGORY_RULES = [
  ['transport', '交通', new Set(['flight', 'train', 'bus'])],
  ['hotel', '住宿', new Set(['hotel'])],
  ['scenery', '景点', new Set(['scenery'])],
  ['travel', '度假产品', new Set(['travel'])],
  ['sourcePlan', '接口原始攻略', new Set(['plan'])]
];

function hasOpeningHours(resource) {
  return (resource.details || []).some(detail => detail.label === '开放时间' && detail.value);
}

function buildItineraryBrief(snapshot, records, resources) {
  const resourceByRef = new Map(resources.map(resource => [resource.ref, resource]));
  const categories = {};
  const candidateSets = [];

  for (const [key, label, types] of CATEGORY_RULES) {
    const categoryRecords = records.filter(record => types.has(record.item.type));
    if (!categoryRecords.length) continue;
    const categoryResources = categoryRecords.map(record => resourceByRef.get(record.ref)).filter(Boolean);
    const selection = buildSelectionBrief(snapshot, categoryRecords, categoryResources);
    categories[key] = {
      label,
      count: categoryRecords.length,
      comparisons: selection.overview.comparisons,
      columns: selection.overview.columns,
      focusRefs: selection.overview.focusRefs,
      focusRows: selection.overview.focusRows,
      candidateKey: key
    };
    candidateSets.push({ key, label, count: categoryRecords.length, candidates: selection.candidates });
  }

  const transport = resources.filter(resource => ['flight', 'train', 'bus'].includes(resource.type));
  const scenery = resources.filter(resource => resource.type === 'scenery');
  const hotels = resources.filter(resource => resource.type === 'hotel');
  const scheduleSignals = {
    transportCount: transport.length,
    transportTimeKnownCount: transport.filter(resource => resource.date && resource.time).length,
    crossDayTransportCount: transport.filter(resource => Number(resource.arrival?.daySpan) > 0).length,
    hotelCount: hotels.length,
    sceneryCount: scenery.length,
    sceneryOpeningHoursKnownCount: scenery.filter(hasOpeningHours).length,
    sceneryOpeningHoursUnknownCount: scenery.filter(resource => !hasOpeningHours(resource)).length,
    sourcePlanCount: resources.filter(resource => resource.type === 'plan').length,
    sourcePlanActivityCount: records.filter(record => record.fromPlan).length
  };

  return {
    overview: {
      format: 'itinerary-overview-v2',
      snapshotId: snapshot.snapshotId,
      request: snapshot.requestParams,
      note: '这是程序生成的行程决策首页，不是最终行程。按 categories 分别选择交通、住宿和景点；comparisons/focusRows 是机械摘要。先用首页排出可执行节奏，只有某一类硬条件或排期字段不足时才读取该 candidateKey 对应的 candidateGroups，不默认读取全部候选。接口原始攻略仅作参考，不能覆盖专家最终行程。完整HTML与完整MD仍保留全部原始资源。',
      coverage: Object.fromEntries(Object.entries(categories).map(([key, value]) => [key, value.count])),
      scheduleSignals,
      categories
    },
    candidateSets
  };
}

module.exports = { buildItineraryBrief, CATEGORY_RULES };
