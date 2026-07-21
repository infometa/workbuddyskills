import http from 'k6/http';
import { check } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BRIDGE_URL = __ENV.REGION_INSIGHT_BRIDGE_URL || 'http://127.0.0.1:8787';
const MODE = __ENV.REGION_INSIGHT_K6_MODE || 'full';
const SMOKE_RATE = Number(__ENV.REGION_INSIGHT_SMOKE_RATE || 1);

const toolLatency = new Trend('region_insight_tool_latency', true);
const toolFailed = new Rate('region_insight_tool_failed');
const toolTimeout = new Rate('region_insight_tool_timeout');

const toolMetrics = {
  post_region_insight_poi_location: {
    latency: new Trend('poi_location_latency', true),
    failed: new Rate('poi_location_failed'),
  },
  post_region_insight_fence_poi_overview: {
    latency: new Trend('fence_poi_overview_latency', true),
    failed: new Rate('fence_poi_overview_failed'),
  },
  post_region_insight_fence_poi_list: {
    latency: new Trend('fence_poi_list_latency', true),
    failed: new Rate('fence_poi_list_failed'),
  },
};

const steady = {
  executor: 'constant-arrival-rate',
  rate: MODE === 'smoke' ? SMOKE_RATE : 50,
  timeUnit: '1s',
  duration: MODE === 'smoke' ? (__ENV.REGION_INSIGHT_SMOKE_DURATION || '30s') : '10m',
  preAllocatedVUs: MODE === 'smoke' ? Math.max(10, SMOKE_RATE * 2) : 200,
  maxVUs: MODE === 'smoke' ? Math.max(20, SMOKE_RATE * 5) : 300,
};

export const options = {
  scenarios: MODE === 'smoke' ? { smoke: steady } : {
    steady_50qps: steady,
    burst_100qps: {
      executor: 'constant-arrival-rate',
      rate: 100,
      timeUnit: '1s',
      duration: '30s',
      startTime: '10m30s',
      preAllocatedVUs: 400,
      maxVUs: 600,
    },
  },
  thresholds: MODE === 'smoke' ? {} : {
    'iterations{scenario:steady_50qps}': ['count>=30000'],
    'iterations{scenario:burst_100qps}': ['count>=3000'],
    dropped_iterations: ['count==0'],
    region_insight_tool_failed: ['rate<=0.005'],
    region_insight_tool_timeout: ['rate<0.01'],
    region_insight_tool_latency: ['p(50)<=500', 'p(99)<=3000'],
    checks: ['rate>=0.995'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(50)', 'p(95)', 'p(99)', 'max'],
};

// Coordinates supplied and confirmed as GCJ-02 for this load-test dataset.
const locations = [
  {
    city: '济南市',
    keyword: '银座超市(莱芜嬴牟店)',
    gcj02_longitude: 117.668218620004,
    gcj02_latitude: 36.24313317078225,
  },
  {
    city: '上海市',
    keyword: '上海妇女用品商店',
    gcj02_longitude: 121.47109199892107,
    gcj02_latitude: 31.22163775558385,
  },
  {
    city: '成都市',
    keyword: '成都建设路邻里生活广场',
    gcj02_longitude: 104.10736584704829,
    gcj02_latitude: 30.680800721556984,
  },
];

function randomItem(values) {
  return values[Math.floor(Math.random() * values.length)];
}

function toolCall() {
  const location = randomItem(locations);
  const circle = [{
    gcj02_longitude: location.gcj02_longitude,
    gcj02_latitude: location.gcj02_latitude,
    radius: 1000,
  }];
  const listCircle = [{
    gcj02_longitude: location.gcj02_longitude,
    gcj02_latitude: location.gcj02_latitude,
    radius: 100,
  }];
  const value = Math.random() * 100;
  if (value < 46) {
    return {
      name: 'post_region_insight_poi_location',
      arguments: { city_name: location.city, keyword: location.keyword, page: 1, page_size: 20 },
    };
  }
  if (value < 82) {
    return {
      name: 'post_region_insight_fence_poi_overview',
      arguments: { circle_fences: circle, group_by_fields: ['category_id'], bucket_size: 100 },
    };
  }
  return { name: 'post_region_insight_fence_poi_list', arguments: { circle_fences: listCircle } };
}

export default function () {
  const call = toolCall();
  const response = http.post(`${BRIDGE_URL}/call`, JSON.stringify({ call }), {
    headers: { 'Content-Type': 'application/json' },
    timeout: '35s',
    tags: { mcp_tool: call.name },
  });

  let result;
  try {
    result = response.json();
  } catch (_error) {
    result = null;
  }
  const duration = Number(result?.duration_ms || response.timings.duration);
  const errorText = String(result?.error || response.error || '').toLowerCase();
  const timedOut = errorText.includes('timeout');
  const success = response.status === 200 && result?.ok === true && result?.result?.isError !== true;
  const metrics = toolMetrics[call.name];

  toolLatency.add(duration, { mcp_tool: call.name });
  toolFailed.add(!success, { mcp_tool: call.name });
  toolTimeout.add(timedOut, { mcp_tool: call.name });
  metrics.latency.add(duration);
  metrics.failed.add(!success);
  check(response, {
    'MCP tool success': () => success,
  });
}
