# Cloud Vendor Agent Allowlist

This directory contains user-extensible configuration that the preanalyzers consult
to **suppress noise** introduced by cloud-vendor security/monitoring agents during
log condensation.

## Why is this configurable?

Different cloud platforms ship their own host-based intrusion detection / monitoring
agents (HIDS, security daemons, monitoring agents, iptables firewalls, init.d
scripts, log paths, …). Their processes, services, firewall chains and file paths
are **legitimate but high-volume** artefacts that would otherwise crowd out genuine
attack indicators in the analyst-facing report.

The preanalyzers therefore filter known cloud-vendor noise out of:

- `ESTABLISHED` connection lists
- listening port owners
- `PPID=1` orphan-process scans
- `iptables -L` chain dumps
- `init.d` script dumps
- `mtime / ctime` recently-modified file lists

The **shipped configuration is intentionally empty** so that this skill does not
embed the brand identifiers of any specific cloud vendor. Operators deploying this
skill on a particular cloud platform should populate
`cloud_vendor_processes.json` with the agent identifiers used by their platform.

## File: `cloud_vendor_processes.json`

| Field | Match type | Purpose |
|---|---|---|
| `agent_processes` | **substring** of process name | Suppress agent procs in `ss`, `netstat`, `ps`, PPID=1 scans |
| `agent_services` | **substring** of systemd unit name | Suppress agent services in `systemctl list-units` style dumps |
| `iptables_chains` | **exact** chain name | Suppress vendor HIDS firewall chains in `iptables -L` |
| `initd_scripts` | **substring** of script name | Suppress agent `/etc/init.d/<name>` script bodies |
| `file_path_noise` | **substring** of file path | Suppress agent log/data paths in mtime/ctime sensitive-file scans |

### Example

```json
{
    "agent_processes": ["my-cloud-agent", "vendorhids-"],
    "agent_services": ["mycloud-", "vendorhids"],
    "iptables_chains": ["VENDORHIDS_IN", "VENDORHIDS_OUT"],
    "initd_scripts": ["my-cloud-agent"],
    "file_path_noise": ["/etc/mycloud/", "/var/log/mycloud/"]
}
```

## Loading semantics

- File is read **once** on first use (cached).
- If the file is missing, malformed, or any field is absent, the loader silently
  returns empty lists for the missing fields and the rest of the skill continues
  to function (no crash, just no extra noise filtering for that category).
- Unknown extra fields are ignored (forward-compatible).
