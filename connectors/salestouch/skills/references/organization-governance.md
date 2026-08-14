# Organization governance workflow

Use this workflow when an authorized consultant or enterprise owner asks WorkBuddy to establish or maintain the SalesTouch organization foundation: company background, units, roles and permissions, employee access, member relationships, or the governed sales process.

Always call `salestouch_whoami` and `salestouch_get_capabilities` first. Treat the returned fixed organization, scopes, permissions, readiness, and formal-authorization flags as authoritative. Before each write, call capabilities again with `includeOperationSchemas: true` and the selected operation's stable `operationId` in `operationIds`; construct `input` only from that returned schema.

## First organization and OAuth return

The MCP grant is organization-bound, so MCP cannot create the user's first organization outside an existing tenant boundary. When the user has no organization, use the first-party SalesTouch OAuth create-organization path offered by the authorization page. After creation, SalesTouch must resume the same OAuth return path so the user can authorize WorkBuddy for the new fixed organization. Then call identity and capabilities again before reading or writing governance data.

Do not imitate this flow with a cross-tenant tool call, arbitrary API, organization ID supplied by the user, or hidden organization switch.

## Read before configuration

Call `salestouch_read_organization_governance_context` for the current organization. Review the organization profile, runtime/company background, unit tree, roles, permission catalog, members, manager-scope summaries, pending invitations, account-provisioning capability, sales-process versions, bindings, source health, and gaps. Resolve authoritative IDs from this response; never invent them.

If a required slice reports `unavailable`, retry the same bounded read at most twice with a short backoff. If it remains unavailable, report the exact source gap and do not execute a mutation that depends on that slice. Do not replace missing source facts with guesses or a server-side planner.

## Configuration sequence

Use `salestouch_operate_organization_governance` only with an operation advertised as ready by capabilities.

1. Company foundation: use `update_organization_profile` for legal/display and contact information, then `update_runtime_profile` for company background used by operating workflows. Verify both readbacks before continuing.
2. Organization units: use `create_unit` and `update_unit` to form the department hierarchy. Before `delete_unit`, inspect child units and member assignments, explain the effect, and complete any required formal authorization.
3. Roles and permissions: review the permission catalog and existing role detail before `create_role`, `update_role_permissions`, or `delete_role`. Classify sales versus non-sales by the resulting capability set, never by the role name. In the current SalesTouch catalog, codes `8` or `17` carry sales execution, while `14` or `18` carry manager workbench access; re-check the live permission catalog before writing because labels and templates remain authoritative. A non-sales employee role must omit both sales and manager capabilities. A non-sales manager role may include manager capability while still omitting sales capability. Show the exact permission delta and require the authorization level returned by capabilities.
4. Employee access: use `invite_member`. Never request, accept, store, or forward an initial plaintext password. Account creation uses invitation and activation, and the employee sets their own credential in the first-party SalesTouch flow. Do not report the account as active until authoritative readback confirms activation or enabled status.
5. Member relationships: resolve the real member, role, and unit before `assign_member_role` or `assign_member_unit`. Use `set_member_account_enabled` and `remove_member` only after showing the impact and completing formal authorization. Never infer that an owner account is safe to disable or remove.
6. Manager reporting scope: after role and unit assignment, read `manager_scopes` with the target manager's canonical local `org.member` ObjectRef. Retain the returned `versionToken` as `expectedVersionToken`, then use `configure_manager_scope` for an active non-owner manager. Choose exactly one mode: `self_only`, `same_dept`, `selected_users`, `selected_roles`, or `selected_depts`. The single `targets` entry and `input.managerRef` must be the same manager ObjectRef. The input contract uses exactly `managerRef`, `scopeMode`, `expectedVersionToken`, `resetToDefault` when applicable, `managedMemberRefs`, `managedRoleKeys`, `managedUnitRefs`, `consequencePreview`, and `scopeConfirmed: true`. For `selected_users`, put canonical local subordinate `org.member` ObjectRefs in `managedMemberRefs` and leave both other selector arrays empty. For `selected_roles`, use only live role keys in `managedRoleKeys`. For `selected_depts`, use only canonical local `org.unit` ObjectRefs in `managedUnitRefs`. Never send legacy `managedUserIds`, `managedDeptIds`, `userIds`, or `deptIds`. Show whose records become visible, require browser-bound formal authorization, and verify the exact stored configuration plus effective scope. A manager cannot include themself as a selected subordinate, and a delegated manager cannot change their own scope unless they also have organization-governance administration authority. If the configuration changed after it was read, reload instead of overwriting it. To restore a manager whose original source was `default_self`, call the same operation with `scopeMode: self_only`, the latest `expectedVersionToken`, `resetToDefault: true`, all three canonical selector arrays empty, and `scopeConfirmed: true`; then verify `versionToken: absent`.
7. Sales process: use `save_sales_process_draft`, read back the exact version and stages, then use `publish_sales_process` and `bind_sales_process` only after the user reviews the publish/binding effect and completes any required browser confirmation. Verify the published version and active binding.

## Write and completion rules

For every mutation, show the target, important field or relationship change, evidence basis, reversibility, and expected effect. Obtain explicit conversational approval, use one stable `clientRequestId`, and follow the browser-bound formal authorization flow when required. Retry only the byte-equivalent intended mutation with the same ID. A changed target or payload requires new approval and a new ID.

If MCP returns `operation_input_contract_invalid`, no formal authorization has been created and no business write has occurred. Re-read the selected operation schema, correct only the reported missing, unknown, or invalid fields, obtain a new conversational approval if the intended payload changed, and use a new `clientRequestId`. Never ask the user to approve a stale or structurally invalid browser request.

Finish with the fixed organization, completed operations, authoritative readback, invitation/activation state, resulting role and unit relationships, sales/non-sales capability classification, manager reporting scopes, active sales-process version/binding, unresolved gaps, and any operation still awaiting authorization. Never include credentials, invite tokens, internal traces, or inaccessible employee data.
