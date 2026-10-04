'use strict';

const has = value => value !== undefined && value !== null && value !== '';
const first = (...values) => values.find(has);

function priceNumber(value) {
  const text = String(value == null ? '' : value).trim();
  if (!/^(?:[¥￥$€£]|CNY\s*|RMB\s*|USD\s*)?\d+(?:,\d{3})*(?:\.\d+)?(?:元)?(?:起)?$/i.test(text)) return null;
  const number = Number(text.replace(/^(?:[¥￥$€£]|CNY\s*|RMB\s*|USD\s*)/i, '').replace(/元?起?$|,/g, ''));
  return Number.isFinite(number) && number >= 0 ? number : null;
}

function durationMinutes(value) {
  const match = String(value || '').trim().match(/^(?:(\d+)\s*(?:小时|时|h))?\s*(?:(\d+)\s*(?:分钟|分|m))?$/i);
  if (!match || (!match[1] && !match[2])) return null;
  const minutes = Number(match[1] || 0) * 60 + Number(match[2] || 0);
  return minutes > 0 ? minutes : null;
}

function scoreNumber(value) {
  const match = String(value == null ? '' : value).match(/(?:^|[^\d])(\d(?:\.\d+)?)(?:分)?(?:$|[^\d])/);
  const number = match ? Number(match[1]) : null;
  return Number.isFinite(number) && number >= 0 && number <= 10 ? number : null;
}

function countNumber(value) {
  const text = String(value == null ? '' : value).trim().replace(/,/g, '');
  const match = text.match(/^(\d+(?:\.\d+)?)\s*(万)?\s*(?:条|人次|次|评论|点评)?$/);
  if (!match) return null;
  const number = Number(match[1]) * (match[2] ? 10000 : 1);
  return Number.isFinite(number) && number >= 0 ? Math.round(number) : null;
}

// Only normalize one explicit distance. Ranges such as “158至669米” are not a
// single comparable point and stay in the original facts for the model.
function distanceMeters(value) {
  const text = String(value == null ? '' : value).trim();
  if (!text || /\d+(?:\.\d+)?\s*(?:至|[-~—])\s*\d/.test(text)) return null;
  const matches = [...text.matchAll(/(\d+(?:\.\d+)?)\s*(公里|千米|km|米|m)(?![a-z])/ig)];
  if (matches.length !== 1) return null;
  const number = Number(matches[0][1]);
  if (!Number.isFinite(number) || number < 0) return null;
  return /公里|千米|km/i.test(matches[0][2]) ? Math.round(number * 1000) : Math.round(number);
}

function clockMinutes(value) {
  const match = String(value == null ? '' : value).trim().match(/(?:^|\s)([01]?\d|2[0-3]):([0-5]\d)(?:\s|$)/);
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

function timeBucket(minutes) {
  if (!Number.isInteger(minutes) || minutes < 0 || minutes >= 24 * 60) return undefined;
  if (minutes < 6 * 60) return '凌晨 00:00–05:59';
  if (minutes < 12 * 60) return '上午 06:00–11:59';
  if (minutes < 18 * 60) return '下午 12:00–17:59';
  return '晚间 18:00–23:59';
}

function availabilityStatus(value) {
  if (!has(value)) return 'unknown';
  if (typeof value === 'number') return value > 0 ? 'available' : value === 0 ? 'sold_out' : 'unknown';
  const text = String(value).trim();
  if (/^\d+$/.test(text)) return Number(text) > 0 ? 'available' : 'sold_out';
  if (/^(?:有|有票|充足|可订|少量|紧张)$/i.test(text)) return 'available';
  if (/^(?:无|无票|售罄|已售罄)$/i.test(text)) return 'sold_out';
  return 'unknown';
}

function seatOptions(raw = {}) {
  const list = [raw.ticketList, raw.seatList, raw.priceList].find(Array.isArray) || [];
  const rows = list.map(option => {
    const seat = first(option.ticketType, option.seatName, option.seatType, option.name);
    if (!seat) return null;
    const left = first(option.leftTicketNum, option.ticketLeftNum, option.leftNum,
      option.remainCount, option.ticketNum, option.stock, option.inventory, option.status);
    const price = priceNumber(first(option.ticketPrice, option.seatPrice, option.price));
    return { seat: String(seat), ...(price !== null ? { price } : {}), status: availabilityStatus(left) };
  }).filter(Boolean);
  if (rows.length) return rows;
  const seat = first(raw.seatName, raw.ticketType, raw.seatType);
  if (!seat) return [];
  const left = first(raw.leftTicketNum, raw.ticketLeftNum, raw.leftNum, raw.remainCount, raw.ticketNum, raw.stock);
  const price = priceNumber(first(raw.ticketPrice, raw.seatPrice, raw.price));
  return [{ seat: String(seat), ...(price !== null ? { price } : {}), status: availabilityStatus(left) }];
}

function inventoryStatus(raw = {}, seats = seatOptions(raw)) {
  const explicit = first(raw.leftTicketNum, raw.ticketLeftNum, raw.leftNum,
    raw.remainCount, raw.ticketNum, raw.stock, raw.inventory, raw.saleStatus);
  const direct = availabilityStatus(explicit);
  if (direct !== 'unknown') return direct;
  if (seats.some(option => option.status === 'available')) return 'available';
  if (seats.length && seats.every(option => option.status === 'sold_out')) return 'sold_out';
  return 'unknown';
}

module.exports = {
  availabilityStatus,
  clockMinutes,
  countNumber,
  distanceMeters,
  durationMinutes,
  inventoryStatus,
  priceNumber,
  scoreNumber,
  seatOptions,
  timeBucket
};
