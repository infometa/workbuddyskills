/** Adapter for confirmed PDF pages. The original RecitePage UI remains unchanged. */
export interface RecitationBlank {
  start: number;
  end: number;
  text?: string;
}

export interface RecitationPage {
  pageNumber: number;
  index?: number;
  chapterId?: string;
  title?: string;
  originalText: string;
  blanks: RecitationBlank[];
  imageUrl?: string;
}

export interface RecitationMaterial {
  title: string;
  confirmed: true;
  pages: RecitationPage[];
}

declare global {
  interface Window {
    __BSJ_RECITATION__?: RecitationMaterial | null;
  }
}

export function getInjectedMaterial(): RecitationMaterial | null {
  const value = window.__BSJ_RECITATION__;
  return value?.confirmed === true && Array.isArray(value.pages) && value.pages.length > 0
    ? value
    : null;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character] ?? character);
}

export function pageToRichText(page: RecitationPage): string {
  let content = "";
  let cursor = 0;
  for (const [index, blank] of page.blanks.entries()) {
    content += escapeHtml(page.originalText.slice(cursor, blank.start));
    content += `<customclickablespan data-cloze-group="pdf-${page.pageNumber}-${index}">${escapeHtml(page.originalText.slice(blank.start, blank.end))}</customclickablespan>`;
    cursor = blank.end;
  }
  content += escapeHtml(page.originalText.slice(cursor));
  let image = "";
  if (page.imageUrl && /^(https:\/\/|data:image\/(?:png|jpeg|webp);base64,)/i.test(page.imageUrl)) {
    image = `<figure class="blk-img"><img src="${escapeHtml(page.imageUrl)}" alt="第 ${page.pageNumber} 页原图" /></figure>`;
  }
  return `<div class="bsj-import-text" style="white-space:pre-wrap;overflow-wrap:anywhere">${content}</div>${image}`;
}

export function createMaterialBook(material: RecitationMaterial) {
  return {
    title: material.title,
    chapters: material.pages.map((page) => ({
      id: `material-page-${page.pageNumber}`,
      chapterId: page.chapterId,
      pageNumber: page.pageNumber,
      title: page.title || `第 ${page.pageNumber} 页`,
      blocks: [{
        id: `material-block-${page.pageNumber}`,
        pageNumber: page.pageNumber,
        title: page.title || `第 ${page.pageNumber} 页`,
        dataBaseBean: {
          bookDataType: "TXT",
          importedRecitationPage: true,
          richTxt: pageToRichText(page),
          txt: page.originalText,
        },
      }],
    })),
  };
}
