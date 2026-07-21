import Imap from 'imap';
import { simpleParser } from 'mailparser';

const account = process.env.QQ_EMAIL_ACCOUNT;
const authCode = process.env.QQ_EMAIL_AUTH_CODE;

if (!account || !authCode) {
  console.error('请设置环境变量 QQ_EMAIL_ACCOUNT 和 QQ_EMAIL_AUTH_CODE');
  process.exit(1);
}

const imapConfig = {
  user: account,
  password: authCode,
  host: 'imap.qq.com',
  port: 993,
  tls: true,
  tlsOptions: { rejectUnauthorized: false },
};

function parseArgs() {
  const args = process.argv.slice(2);
  let limit = 10;
  let days = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--limit' && args[i + 1]) {
      limit = Math.max(1, parseInt(args[i + 1], 10) || 10);
      i++;
    } else if (args[i] === '--days' && args[i + 1]) {
      days = Math.max(1, parseInt(args[i + 1], 10) || 7);
      i++;
    }
  }
  return { limit, days };
}

function openInbox(imap) {
  return new Promise((resolve, reject) => {
    imap.openBox('INBOX', false, (err, box) => {
      if (err) reject(err);
      else resolve(box);
    });
  });
}

function getPreview(text, maxLen = 200) {
  if (!text || typeof text !== 'string') return '';
  const oneLine = text.replace(/\s+/g, ' ').trim();
  return oneLine.length <= maxLen ? oneLine : oneLine.slice(0, maxLen) + '…';
}

async function fetchEmails(limit, sinceDate) {
  const imap = new Imap(imapConfig);

  return new Promise((resolve, reject) => {
    const emails = [];

    imap.once('ready', () => {
      openInbox(imap)
        .then(() => {
          const searchCriteria = sinceDate ? [['SINCE', sinceDate]] : ['ALL'];
          imap.search(searchCriteria, (err, uids) => {
            if (err) {
              imap.end();
              return reject(err);
            }
            if (uids.length === 0) {
              imap.end();
              return resolve(emails);
            }
            const slice = uids.slice(-limit);
            const fetch = imap.fetch(slice, { bodies: '' });
            const parsePromises = [];

            fetch.on('message', (msg) => {
              let resolveP;
              parsePromises.push(new Promise((r) => { resolveP = r; }));
              const state = { parsed: null, uid: undefined, pushed: false };
              function maybePush() {
                if (state.parsed != null && state.uid !== undefined && !state.pushed) {
                  state.pushed = true;
                  emails.push({ parsed: state.parsed, uid: state.uid });
                  resolveP();
                }
              }
              msg.once('attributes', (attrs) => {
                state.uid = attrs && attrs.uid;
                maybePush();
              });
              msg.on('body', (stream) => {
                simpleParser(stream, (parseErr, parsed) => {
                  if (!parseErr) state.parsed = parsed;
                  maybePush();
                });
              });
              msg.once('end', () => {
                if (!state.pushed && state.parsed != null) {
                  state.pushed = true;
                  emails.push({ parsed: state.parsed, uid: state.uid });
                  resolveP();
                }
              });
            });
            fetch.once('error', (e) => {
              imap.end();
              reject(e);
            });
            fetch.once('end', () => {
              Promise.all(parsePromises).then(() => imap.end());
            });
          });
        })
        .catch((e) => {
          imap.end();
          reject(e);
        });
    });

    imap.once('error', reject);
    imap.once('end', () => resolve(emails));
    imap.connect();
  });
}

async function main() {
  const { limit, days } = parseArgs();
  let sinceDate = null;
  if (days) {
    sinceDate = new Date();
    sinceDate.setDate(sinceDate.getDate() - days);
  }

  try {
    const emails = await fetchEmails(limit, sinceDate);
    if (emails.length === 0) {
      console.log('暂无邮件');
      return;
    }
    // 按日期倒序，1 = 最新一封
    emails.sort((a, b) => {
      const da = a.parsed.date ? new Date(a.parsed.date).getTime() : 0;
      const db = b.parsed.date ? new Date(b.parsed.date).getTime() : 0;
      return db - da;
    });
    emails.forEach((item, i) => {
      const e = item.parsed;
      const from = e.from?.text || e.from?.value?.[0]?.address || '';
      const date = e.date ? new Date(e.date).toLocaleString() : '';
      const preview = getPreview(e.text || e.html);
      console.log(`--- ${i + 1} ---`);
      console.log('主题:', e.subject || '(无主题)');
      console.log('发件人:', from);
      console.log('日期:', date);
      console.log('UID:', item.uid ?? '(无)');
      console.log('摘要:', preview);
      console.log('');
    });
  } catch (err) {
    console.error('收信失败:', err.message);
    process.exit(1);
  }
}

main();
