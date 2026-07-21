import { registerOAuthTools } from "./oauth.js";
import { registerAdvertiserTools } from "./advertiser.js";
import { registerAdgroupTools } from "./adgroups.js";
import { registerCreativeTools } from "./creatives.js";
import { registerImageTools } from "./images.js";
import { registerVideoTools } from "./videos.js";
import { registerReportTools } from "./reports.js";
import { registerAudienceTools } from "./audiences.js";
import { registerFundTools } from "./funds.js";
import { registerLeadTools } from "./leads.js";
// import { registerGeneratedTools } from "./generated/index.js"; // 358 generated tools disabled
export function registerAllTools(server) {
    registerOAuthTools(server);
    registerAdvertiserTools(server);
    registerAdgroupTools(server);
    registerCreativeTools(server);
    registerImageTools(server);
    registerVideoTools(server);
    registerReportTools(server);
    registerAudienceTools(server);
    registerFundTools(server);
    registerLeadTools(server);
    // registerGeneratedTools(server); // disabled: 358 auto-generated tools
}
//# sourceMappingURL=index.js.map