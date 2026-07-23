# Tophpc Command Reference

> Version: v2.1.0 | Based on source code analysis

## Global Flags

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--config-path` | `-c` | string | `""` | Config file path (default is `$HOME/.tophpc/config.yaml`) |

## Operational Notes

- Prefer `--format json` for inspection, programmatic parsing, and post-change verification.
- Treat credentials as config-driven state; do not hardcode a credentials file path when constructing commands.
- Many commands accept an optional `[clusterId]`. Runtime resolution typically follows this order:
  1. use the first positional argument when it starts with `hpc-`
  2. otherwise fall back to `certificate.clusterId` in the active config file
  3. fail if neither source provides a cluster ID
- For destructive commands without `--force` such as `queue delete` and `image delete`, inspect targets first and only use explicit stdin confirmation once the deletion target is verified.
- For `fs remove`, run one mount path per command. The Cobra usage string allows `[mountPath...]`, but the current implementation removes one resolved mount path per invocation.

---

## 1. config — Manage Configuration

### `tophpc config init`

Interactively generate the configuration file.

```
tophpc config init [-c <config-file-path>]
```

No additional flags.

### `tophpc config show`

Show the current configuration file content.

```
tophpc config show [-c <config-file-path>]
```

No additional flags.

---

## 2. cluster — Manage Clusters

### `tophpc cluster create`

Create a new HPC cluster.

```
tophpc cluster create [flags]
```

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--dryrun` | `-d` | bool | `false` | Dry run (do not actually create) |
| `--template` | | bool | `false` | Generate a configuration template file |
| `--template-path` | | string | `"cluster-config-template.yaml"` | Path to save the generated template |
| `--cluster-config-path` | `-p` | string | `""` | Specify a configuration file for cluster creation |
| `--cluster-name` | `-n` | string | `"cluster-default"` | Cluster name |
| `--scheduler-type` | `-t` | string | `"SLURM"` | Scheduler type: `SLURM` or `SGE` |
| `--scheduler-version` | `-v` | string | `"23.11.7"` | Scheduler version |
| `--zone` | `-z` | string | `""` | Cluster zone (required at runtime) |
| `--manager-instance-type` | | string | `"S2.SMALL2"` | Manager node instance type |
| `--manager-node-count` | | int | `1` | Manager node count (1 or 2) |
| `--manager-internet-bandwidth` | | int | `0` | Manager node internet bandwidth |
| `--manager-image-id` | | string | `""` | Manager node image ID |
| `--manager-system-disk` | | Disk | `"-100"` | Manager system disk: `<DiskType>-<DiskSizeGB>` |
| `--manager-data-disks` | | DiskSlice | `[]` | Manager data disk (repeatable): `<DiskType>-<DiskSize>` |
| `--manager-instance-id` | | InstanceIdSlice | `[]` | Manager instance IDs (comma-separated) |
| `--login-instance-type` | | string | `"S2.SMALL2"` | Login node instance type |
| `--login-node-count` | | int | `0` | Login node count (0–10) |
| `--login-internet-bandwidth` | | int | `0` | Login node internet bandwidth |
| `--login-image-id` | | string | `""` | Login node image ID |
| `--login-system-disk` | | Disk | `"-100"` | Login system disk: `<DiskType>-<DiskSizeGB>` |
| `--login-data-disks` | | DiskSlice | `[]` | Login data disk (repeatable) |
| `--login-instance-id` | | InstanceIdSlice | `[]` | Login instance IDs (comma-separated) |
| `--compute-instance-type` | | string | `"S2.SMALL2"` | Compute node instance type |
| `--compute-node-count` | | int | `0` | Compute node count |
| `--compute-internet-bandwidth` | | int | `0` | Compute node internet bandwidth |
| `--compute-image-id` | | string | `""` | Compute node image ID |
| `--compute-queue` | | string | `"compute"` | Queue name for compute nodes |
| `--compute-system-disk` | | Disk | `"-100"` | Compute system disk: `<DiskType>-<DiskSizeGB>` |
| `--compute-data-disks` | | DiskSlice | `[]` | Compute data disk (repeatable) |
| `--compute-instance-id` | | InstanceIdSlice | `[]` | Compute instance IDs (comma-separated) |

> **Note**: Disk format is `<DiskType>-<DiskSizeGB>`, e.g., `CLOUD_SSD-100`, `CLOUD_PREMIUM-200`.

### `tophpc cluster list`

List all clusters.

```
tophpc cluster list [flags]
```

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | | string | `""` | Output format: `json`, `yaml` |
| `--size` | | int32 | `10` | Page size |
| `--page` | | int32 | `1` | Page number |

### `tophpc cluster show`

Show cluster detail information.

```
tophpc cluster show [clusterId] [flags]
```

**Positional args**: `[clusterId]` (optional, uses config if omitted)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | string | `"json"` | Output format: `json`, `yaml` |

---

## 3. node — Manage Nodes

### `tophpc node add`

Add nodes to a cluster.

```
tophpc node add [flags]
```

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--template` | | bool | `false` | Generate a configuration template |
| `--template-path` | | string | `"node-config-template.yaml"` | Template file path |
| `--node-config-path` | `-p` | string | `""` | Path to node config file |
| `--cluster-id` | | string | `""` | Cluster ID (uses config if empty) |
| `--zone` | `-z` | string | `""` | Node zone (required) |
| `--count` | | int | `1` | Number of nodes (1–100) |
| `--image-id` | | string | `""` | Image ID (required) |
| `--instance-type` | | string | `""` | Instance type (required) |
| `--queue` | | string | `""` | Queue name (required for COMPUTE_NODE) |
| `--node-role` | | string | `"COMPUTE_NODE"` | Node role: `COMPUTE_NODE` or `LOGIN_NODE` |
| `--node-type` | | string | `"STATIC_NODE"` | Node type: `STATIC_NODE` or `DYNAMIC_NODE` |
| `--subnet-id` | | string | `""` | Subnet ID (required) |
| `--internet-bandwidth` | | int | `0` | Internet bandwidth |
| `--system-disk` | | Disk | `"CLOUD_PREMIUM-100"` | System disk: `<DiskType>-<DiskSizeGB>` |
| `--data-disks` | | DiskSlice | `[]` | Data disk (repeatable) |
| `--hcc-cluster-id` | | string | `""` | HCC cluster ID |

### `tophpc node list`

List nodes in a cluster.

```
tophpc node list [clusterId] [flags]
```

**Positional args**: `[clusterId]` (optional)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | | string | `""` | Output format: `json`, `yaml` |
| `--size` | | int32 | `10` | Page size |
| `--page` | | int32 | `1` | Page number |

### `tophpc node remove`

Remove a node from the cluster.

```
tophpc node remove [clusterId] <instanceId> [flags]
```

**Positional args**: `[clusterId]` (optional), `<instanceId>` (required, e.g., `ins-xxxxxxxx`)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--force` | `-f` | bool | `false` | Force remove without confirmation |

> ⚠️ **Always use `--force` when running non-interactively** to avoid stdin prompts.

---

## 4. queue — Manage Queues

### `tophpc queue add`

Add a queue to a cluster.

```
tophpc queue add [clusterId] <queue-name>
```

**Positional args**: `[clusterId]` (optional), `<queue-name>` (required)

No additional flags.

> **Note**: This only creates a queue in the scheduler. Use `tophpc scale add` to configure auto-scaling.

### `tophpc queue list`

List queues in a cluster.

```
tophpc queue list [clusterId] [flags]
```

**Positional args**: `[clusterId]` (optional)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | | string | `""` | Output format: `json`, `yaml` |
| `--size` | | int32 | `10` | Page size |
| `--page` | | int32 | `1` | Page number |

### `tophpc queue show`

Show a queue's detail information.

```
tophpc queue show [clusterId] <queueName> [flags]
```

**Positional args**: `[clusterId]` (optional), `<queueName>` (required)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | | string | `""` | Output format: `json`, `yaml` |
| `--size` | | int32 | `10` | Page size |
| `--page` | | int32 | `1` | Page number |

### `tophpc queue delete`

Delete a queue from the cluster.

```
tophpc queue delete [clusterId] <queue-name>
```

**Positional args**: `[clusterId]` (optional), `<queue-name>` (required)

No additional flags. Prompts for confirmation and does not provide `--force`.

> **Source note**: the Cobra `Use` string is `delete <clusterId> <queue-name>`, but runtime behavior accepts one or two positional args and resolves `clusterId` from config when omitted.
> 
> **Operational note**: inspect the queue first, then use explicit stdin confirmation only after the deletion target is verified.

---

## 5. scale — Manage Auto-Scaling (CORE FEATURE)

### `tophpc scale add`

Add auto-scale configuration for a queue.

```
tophpc scale add [clusterId] <queue-name> [flags]
```

**Positional args**: `[clusterId]` (optional), `<queue-name>` (required)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--min-node` | `-m` | int32 | *(unset)* | Minimum dynamic node count |
| `--max-node` | `-M` | int32 | *(unset, defaults to 10)* | Maximum dynamic node count |
| `--max-nodes-per-cycle` | `-p` | int32 | *(unset, defaults to 10)* | Max nodes to scale per cycle |
| `--enable-scale-up` | | bool | `true` | Enable auto scale-up |
| `--enable-scale-down` | | bool | `true` | Enable auto scale-down |
| `--hcc-cluster-id` | | string | `""` | HCC cluster ID |
| `--instance-type` | | string | `""` | Instance type (e.g., `S5.LARGE8`). **Mutually exclusive with `--instance-specs`** |
| `--cpu` | | int32 | *(unset)* | CPU cores (required in simple mode) |
| `--memory` | | int32 | *(unset)* | Memory in GB (required in simple mode) |
| `--gpu-type` | | string | `""` | GPU model (e.g., `V100`, `T4`) |
| `--gpu-count` | | int32 | *(unset)* | GPU count (required in simple mode) |
| `--image-id` | | string | `""` | Image ID (required) |
| `--subnet-id` | | string | `""` | Subnet ID (simple mode) |
| `--zone` | | string | `""` | Availability zone (simple mode) |
| `--system-disk` | | Disk | `"CLOUD_PREMIUM-100"` | System disk: `<DiskType>-<DiskSizeGB>` |
| `--instance-specs` | | string | `""` | Multi-instance JSON config. **Mutually exclusive with `--instance-type`** |

**Two modes**:
- **Simple mode**: Use `--instance-type` with `--cpu`, `--memory`, `--gpu-count`, `--subnet-id`, `--zone`
- **Complex mode**: Use `--instance-specs` with JSON array:
  ```json
  [{"type":"S5.LARGE8","cpu":4,"memory":8,"subnetId":"subnet-xxx","zone":"ap-beijing-6"}]
  ```

### `tophpc scale set`

Modify existing auto-scale configuration for a queue.

```
tophpc scale set [clusterId] [queue] [flags]
```

**Positional args**: `[clusterId]` (optional), `[queue]` (optional — required if not using `-p`)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--scale-config-path` | `-p` | string | `""` | Path to scale config file (alternative to specifying queue) |
| `--image-id` | | string | `""` | Image ID |
| `--hcc-cluster-id` | | string | `""` | HCC cluster ID |
| `--max-node` | `-M` | int32 | *(unset)* | Max node count |
| `--min-node` | `-m` | int32 | *(unset)* | Min node count |
| `--max-nodes-per-cycle` | | int32 | *(unset)* | Max nodes to scale per cycle |
| `--enable-scale-up` | | BoolFlag | *(unset)* | Enable/disable auto scale-up (`true`/`false`) |
| `--enable-scale-down` | | BoolFlag | *(unset)* | Enable/disable auto scale-down (`true`/`false`) |
| `--disk-size` | | int32 | *(unset)* | System disk size |
| `--disk-type` | | string | `""` | System disk type |
| `--instance-type` | | string | `""` | Instance type (mutually exclusive with `--instance-specs`) |
| `--cpu` | | int32 | *(unset)* | CPU cores (simple mode) |
| `--memory` | | int32 | *(unset)* | Memory in GB (simple mode) |
| `--gpu-type` | | string | `""` | GPU model (simple mode) |
| `--gpu-count` | | int32 | *(unset)* | GPU count (simple mode) |
| `--subnet-id` | | string | `""` | Subnet ID (simple mode) |
| `--zone` | | string | `""` | Availability zone (simple mode) |
| `--instance-specs` | | string | `""` | Multi-instance JSON config (complex mode) |

> **Note**: `scale set` first fetches the current config, then applies only the flags you specify. Unset flags are not modified.

### `tophpc scale show`

Show the auto-scale configuration for a cluster.

```
tophpc scale show [clusterId] [flags]
```

**Positional args**: `[clusterId]` (optional)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | | string | `""` | Output format: `json`, `yaml` |

### `tophpc scale exec`

Manually trigger a scale action.

```
tophpc scale exec [clusterId] [flags]
```

**Positional args**: `[clusterId]` (optional)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--action` | `-a` | string | `""` | Scale action: `scale-up` or `scale-down` |

### `tophpc scale delete`

Delete auto-scale configuration for a queue.

```
tophpc scale delete [clusterId] <queue-name>
```

**Positional args**: `[clusterId]` (optional), `<queue-name>` (required)

No additional flags.

---

## 6. fs — Manage File Systems

### `tophpc fs add`

Mount a file system to the cluster.

```
tophpc fs add [clusterId] [flags]
```

**Positional args**: `[clusterId]` (optional)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--local-path` | | string | `""` | Local mount path (e.g., `/mnt/data`) — **required** |
| `--remote-path` | | string | `""` | Remote NFS path (e.g., `10.0.0.1:/share`) — **required** |
| `--protocol` | | string | `"NFS 3.0"` | Protocol: `NFS 3.0`, `NFS 4.0`, `NFS_V3`, `NFS_V4`, `TURBO` |
| `--storage-type` | | string | `"cfs"` | Storage type: `cfs` or `cfs-turbo` |
| `--cfs-id` | | string | `""` | CFS file system ID (e.g., `cfs-xxxxxx`) |
| `--option` | | string | `""` | Mount options (e.g., `nfsvers=3,nolock`) |
| `--force` | `-f` | bool | `false` | Add without confirmation |

> For **CFS Turbo**, the `--remote-path` is auto-corrected to `<ip>@tcp0:/<fsId>/cfs` format.

### `tophpc fs list`

List mounted file systems in the cluster.

```
tophpc fs list [clusterId] [flags]
```

**Positional args**: `[clusterId]` (optional)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | | string | `""` | Output format: `json`, `yaml` |
| `--size` | | int32 | `10` | Page size |
| `--page` | | int32 | `1` | Page number |

### `tophpc fs remove`

Unmount a file system from the cluster.

```
tophpc fs remove [clusterId] <mountPath> [flags]
```

**Positional args**: `[clusterId]` (optional), `<mountPath>` (required, must be absolute path)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--force` | `-f` | bool | `false` | Remove without confirmation |

> **Implementation note**: the Cobra usage string allows `[mountPath...]`, but the current implementation removes one resolved mount path per invocation. Repeat the command once per mount point.

---

## 7. image — Manage Images

### `tophpc image create`

Create a custom image from an instance.

```
tophpc image create <instanceId> [flags]
```

**Positional args**: `<instanceId>` (required, e.g., `ins-xxxxxxxx`)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--name` | `-n` | string | `""` | Image name |
| `--desc` | `-d` | string | `""` | Image description |

### `tophpc image list`

List images in the user account.

```
tophpc image list [imageIds...] [flags]
```

**Positional args**: `[imageIds]` (optional, 0–10 image IDs to filter)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | | string | `""` | Output format: `json`, `yaml` |
| `--size` | | int32 | `10` | Page size |
| `--page` | | int32 | `1` | Page number |

### `tophpc image delete`

Delete images from the user account.

```
tophpc image delete <imageId> [imageId...]
```

**Positional args**: `<imageIds>` (required, 1–10 image IDs)

No additional flags. Prompts for confirmation and does not provide `--force`.

> **Operational note**: inspect candidate images first with `tophpc image list ... --format json`, then confirm only the verified targets.
> 
> **Permission note**: images currently used by auto-scale configs cannot be deleted by non-admin users.

---

## 8. log — Manage Log Collection

### `tophpc log add`

Register a log file for collection and reporting.

```
tophpc log add [flags]
```

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--alias` | | string | `""` | Unique alias for the log file — **required** |
| `--path` | | string | `""` | Absolute path to the log file — **required** |
| `--mode` | | string | `"tail"` | Read mode: `tail` (incremental) or `full` (entire file each time) |

### `tophpc log list`

List all registered log files and their status.

```
tophpc log list
```

No additional flags.

### `tophpc log remove`

Remove a log file record by alias.

```
tophpc log remove [flags]
```

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--alias` | | string | `""` | Log file alias to remove — **required** |

### `tophpc log reset`

Reset a log file's read offset to the beginning.

```
tophpc log reset [flags]
```

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--alias` | | string | `""` | Log file alias to reset — **required** |

### `tophpc log report`

Report new log lines to CLS (Cloud Log Service).

```
tophpc log report [flags]
```

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--alias` | | string | `""` | Log file alias to report (optional; reports all if omitted) |

---

## 9. version — Version Management

### `tophpc version`

Display current version and list subcommands.

```
tophpc version
```

### `tophpc version upgrade`

Upgrade tophpc to the latest version from COS.

```
tophpc version upgrade
```

No additional flags. Downloads from the region-specific COS bucket.

### `tophpc version rollback`

Rollback tophpc to a previously installed version.

```
tophpc version rollback [version]
```

**Positional args**: `[version]` (optional, e.g., `v2.0.0`; uses most recent backup if omitted)

No additional flags.

### `tophpc version list`

List all previously installed versions available for rollback.

```
tophpc version list
```

No additional flags. Versions are stored in `~/.tophpc/versions/`.

---

## 10. migration — Cluster Migration

Migrate a cluster between THPC (managed) and TOPHPC (self-managed) modes.

```
tophpc migration [flags]
```

| Flag | Short | Type | Default | Required | Description |
|------|-------|------|---------|----------|-------------|
| `--to` | | string | `""` | **Yes** | Migration target: `thpc` or `tophpc` |
| `--cluster-id` | | string | `""` | No | Cluster ID to migrate |
| `--dryrun` | | bool | `false` | No | Print config without actually migrating |
| `--ssh-id` | | string | `"cluster-ssh-key"` | No | SSH key ID |

---

## 11. debug — Debug Tools

### `tophpc debug ssh`

Test SSH execution on a remote node.

```
tophpc debug ssh <ip> [flags]
```

**Positional args**: `<ip>` (required)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--cmd` | | string | `""` | Command to execute via SSH |
| `--script-path` | | string | `""` | Path to a bash script to execute |
| `--private-key-path` | | string | `""` | Path to SSH private key file |

### `tophpc debug db`

Database debug tool. Subcommands:

#### `tophpc debug db list-buckets`

List all buckets in the bbolt database.

```
tophpc debug db list-buckets
```

No additional flags.

#### `tophpc debug db list-keys`

List all keys in a specific bucket.

```
tophpc debug db list-keys <bucket>
```

**Positional args**: `<bucket>` (required)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--limit` | | int | `100` | Max keys to display (0 = unlimited) |

#### `tophpc debug db get`

Get the value of a specific key in a bucket.

```
tophpc debug db get <bucket> <key>
```

**Positional args**: `<bucket>` (required), `<key>` (required)

No additional flags.

#### `tophpc debug db delete`

Delete a specific key from a bucket.

```
tophpc debug db delete <bucket> <key> [flags]
```

**Positional args**: `<bucket>` (required), `<key>` (required)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--force` | `-f` | bool | `false` | Force delete without confirmation |

#### `tophpc debug db add`

Add or update a key-value pair in a bucket.

```
tophpc debug db add <bucket> <key> <value> [flags]
```

**Positional args**: `<bucket>` (required), `<key>` (required), `<value>` (required — supports JSON string or `@filepath`)

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--force` | `-f` | bool | `false` | Force overwrite existing key |
| `--create-bucket` | `-c` | bool | `false` | Auto-create bucket if not exists |

---

## Disk Format Reference

All disk-related flags use the format: `<DiskType>-<DiskSizeGB>`

Common disk types:
- `CLOUD_PREMIUM` — Premium cloud disk
- `CLOUD_SSD` — SSD cloud disk
- `CLOUD_BSSD` — Balanced SSD
- `CLOUD_HSSD` — Enhanced SSD

Examples: `CLOUD_SSD-100`, `CLOUD_PREMIUM-200`

## Instance Specs JSON Format

For `--instance-specs` flag in scale commands:

```json
[
  {
    "type": "S5.LARGE8",
    "cpu": 4,
    "memory": 8,
    "gpuType": "",
    "gpuCount": 0,
    "subnetId": "subnet-xxxxxxxx",
    "zone": "ap-beijing-6",
    "hccClusterId": ""
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Instance type (e.g., `S5.LARGE8`, `GN10X.LARGE40`) |
| `cpu` | int | CPU cores |
| `memory` | int | Memory in GB |
| `gpuType` | string | GPU model (e.g., `V100`, `T4`), empty for non-GPU |
| `gpuCount` | int | Number of GPUs |
| `subnetId` | string | Subnet ID (required) |
| `zone` | string | Availability zone (required) |
| `hccClusterId` | string | HCC cluster ID (optional) |
