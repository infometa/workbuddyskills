# HPC Supported Instance Types

This file lists all instance types supported by the Tencent Cloud HPC platform. Use this reference when:
- The user asks what node/instance types are available
- Building `tophpc node add` or `tophpc scale add/set` commands that require `--instance-type`
- Validating a user-provided instance type string

## Table of Contents

- [Standard Instances (标准型)](#standard-instances)
  - [SA9](#sa9) | [S9](#s9) | [S8](#s8) | [SA5](#sa5) | [SA4](#sa4) | [S6](#s6) | [SA3](#sa3) | [S5](#s5)
- [Memory-Optimized Instances (内存型)](#memory-optimized-instances)
  - [M8](#m8) | [MA5](#ma5) | [MA4](#ma4) | [MA3](#ma3) | [M6](#m6) | [M5](#m5)
- [Compute-Optimized Instances (计算型)](#compute-optimized-instances)
  - [C6](#c6) | [C5](#c5) | [C4](#c4)
- [GPU / Heterogeneous Instances (GPU / 异构计算)](#gpu--heterogeneous-instances)
  - [GT4](#gt4) | [GN10Xp](#gn10xp) | [GN10X](#gn10x) | [GN8](#gn8) | [GN7](#gn7) | [GI3X](#gi3x) | [PNV4](#pnv4) | [PNV5b](#pnv5b) | [PNV6](#pnv6)

---

## Standard Instances

### SA9

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| SA9.MEDIUM2 | 2 | 2 |
| SA9.MEDIUM4 | 2 | 4 |
| SA9.MEDIUM8 | 2 | 8 |
| SA9.LARGE8 | 4 | 8 |
| SA9.LARGE16 | 4 | 16 |
| SA9.2XLARGE16 | 8 | 16 |
| SA9.2XLARGE32 | 8 | 32 |
| SA9.4XLARGE32 | 16 | 32 |
| SA9.4XLARGE64 | 16 | 64 |
| SA9.8XLARGE64 | 32 | 64 |
| SA9.8XLARGE128 | 32 | 128 |
| SA9.16XLARGE128 | 64 | 128 |
| SA9.16XLARGE256 | 64 | 256 |
| SA9.32XLARGE256 | 128 | 256 |
| SA9.32XLARGE512 | 128 | 512 |
| SA9.48XLARGE576 | 192 | 576 |
| SA9.96XLARGE1152 | 384 | 1152 |
| SA9.192XLARGE2304 | 768 | 2304 |

### S9

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| S9.MEDIUM2 | 2 | 2 |
| S9.MEDIUM4 | 2 | 4 |
| S9.MEDIUM8 | 2 | 8 |
| S9.LARGE8 | 4 | 8 |
| S9.LARGE16 | 4 | 16 |
| S9.2XLARGE16 | 8 | 16 |
| S9.2XLARGE32 | 8 | 32 |
| S9.4XLARGE32 | 16 | 32 |
| S9.4XLARGE64 | 16 | 64 |
| S9.8XLARGE64 | 32 | 64 |
| S9.8XLARGE128 | 32 | 128 |
| S9.16XLARGE128 | 64 | 128 |
| S9.16XLARGE256 | 64 | 256 |
| S9.18XLARGE288 | 72 | 288 |
| S9.36XLARGE576 | 144 | 576 |
| S9.72XLARGE1152 | 288 | 1152 |

### S8

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| S8.MEDIUM2 | 2 | 2 |
| S8.MEDIUM4 | 2 | 4 |
| S8.MEDIUM8 | 2 | 8 |
| S8.LARGE8 | 4 | 8 |
| S8.LARGE16 | 4 | 16 |
| S8.2XLARGE16 | 8 | 16 |
| S8.2XLARGE32 | 8 | 32 |
| S8.4XLARGE32 | 16 | 32 |
| S8.4XLARGE64 | 16 | 64 |
| S8.8XLARGE64 | 32 | 64 |
| S8.8XLARGE128 | 32 | 128 |
| S8.14XLARGE256 | 56 | 256 |
| S8.16XLARGE256 | 64 | 256 |
| S8.28XLARGE512 | 112 | 512 |
| S8.56XLARGE1024 | 224 | 1024 |

### SA5

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| SA5.MEDIUM2 | 2 | 2 |
| SA5.MEDIUM4 | 2 | 4 |
| SA5.LARGE8 | 4 | 8 |
| SA5.LARGE16 | 4 | 16 |
| SA5.2XLARGE16 | 8 | 16 |
| SA5.2XLARGE32 | 8 | 32 |
| SA5.4XLARGE32 | 16 | 32 |
| SA5.4XLARGE64 | 16 | 64 |
| SA5.8XLARGE64 | 32 | 64 |
| SA5.8XLARGE128 | 32 | 128 |
| SA5.12XLARGE96 | 48 | 96 |
| SA5.12XLARGE192 | 48 | 192 |
| SA5.16XLARGE256 | 64 | 256 |
| SA5.16XLARGE288 | 64 | 288 |
| SA5.32XLARGE576 | 128 | 576 |
| SA5.64XLARGE1152 | 256 | 1152 |
| SA5.128XLARGE2304 | 512 | 2304 |

### SA4

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| SA4.MEDIUM4 | 2 | 4 |
| SA4.MEDIUM8 | 2 | 8 |
| SA4.LARGE8 | 4 | 8 |
| SA4.LARGE16 | 4 | 16 |
| SA4.2XLARGE16 | 8 | 16 |
| SA4.2XLARGE32 | 8 | 32 |
| SA4.4XLARGE32 | 16 | 32 |
| SA4.4XLARGE64 | 16 | 64 |
| SA4.8XLARGE64 | 32 | 64 |
| SA4.8XLARGE128 | 32 | 128 |
| SA4.12XLARGE96 | 48 | 96 |
| SA4.12XLARGE192 | 48 | 192 |
| SA4.16XLARGE128 | 64 | 128 |
| SA4.16XLARGE256 | 64 | 256 |
| SA4.24XLARGE192 | 96 | 192 |
| SA4.48XLARGE768 | 192 | 768 |
| SA4.96XLARGE1536 | 384 | 1536 |

### S6

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| S6.MEDIUM2 | 2 | 2 |
| S6.MEDIUM4 | 2 | 4 |
| S6.MEDIUM8 | 2 | 8 |
| S6.LARGE8 | 4 | 8 |
| S6.LARGE16 | 4 | 16 |
| S6.2XLARGE16 | 8 | 16 |
| S6.2XLARGE32 | 8 | 32 |
| S6.4XLARGE32 | 16 | 32 |
| S6.4XLARGE64 | 16 | 64 |
| S6.8XLARGE64 | 32 | 64 |
| S6.8XLARGE128 | 32 | 128 |
| S6.12XLARGE96 | 48 | 96 |
| S6.12XLARGE192 | 48 | 192 |
| S6.16XLARGE216 | 64 | 216 |
| S6.32XLARGE432 | 128 | 432 |

### SA3

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| SA3.MEDIUM2 | 2 | 2 |
| SA3.MEDIUM4 | 2 | 4 |
| SA3.MEDIUM8 | 2 | 8 |
| SA3.LARGE8 | 4 | 8 |
| SA3.LARGE16 | 4 | 16 |
| SA3.2XLARGE16 | 8 | 16 |
| SA3.2XLARGE32 | 8 | 32 |
| SA3.4XLARGE32 | 16 | 32 |
| SA3.4XLARGE64 | 16 | 64 |
| SA3.8XLARGE64 | 32 | 64 |
| SA3.8XLARGE128 | 32 | 128 |
| SA3.12XLARGE96 | 48 | 96 |
| SA3.12XLARGE192 | 48 | 192 |
| SA3.16XLARGE128 | 64 | 128 |
| SA3.16XLARGE256 | 64 | 256 |
| SA3.20XLARGE160 | 80 | 160 |
| SA3.20XLARGE320 | 80 | 320 |
| SA3.24XLARGE192 | 96 | 192 |
| SA3.24XLARGE384 | 96 | 384 |
| SA3.29XLARGE216 | 116 | 216 |
| SA3.29XLARGE470 | 116 | 470 |
| SA3.40XLARGE320 | 160 | 320 |
| SA3.40XLARGE640 | 160 | 640 |
| SA3.58XLARGE432 | 232 | 432 |
| SA3.58XLARGE940 | 232 | 940 |

### S5

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| S5.SMALL1 | 1 | 1 |
| S5.SMALL2 | 1 | 2 |
| S5.SMALL4 | 1 | 4 |
| S5.MEDIUM2 | 2 | 2 |
| S5.MEDIUM4 | 2 | 4 |
| S5.MEDIUM8 | 2 | 8 |
| S5.LARGE4 | 4 | 4 |
| S5.LARGE8 | 4 | 8 |
| S5.LARGE16 | 4 | 16 |
| S5.2XLARGE16 | 8 | 16 |
| S5.2XLARGE32 | 8 | 32 |
| S5.4XLARGE32 | 16 | 32 |
| S5.4XLARGE64 | 16 | 64 |
| S5.6XLARGE48 | 24 | 48 |
| S5.6XLARGE96 | 24 | 96 |
| S5.8XLARGE64 | 32 | 64 |
| S5.8XLARGE128 | 32 | 128 |
| S5.12XLARGE96 | 48 | 96 |
| S5.12XLARGE192 | 48 | 192 |
| S5.16XLARGE256 | 64 | 256 |
| S5.21XLARGE320 | 84 | 320 |

---

## Memory-Optimized Instances

### M8

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| M8.MEDIUM16 | 2 | 16 |
| M8.LARGE32 | 4 | 32 |
| M8.2XLARGE64 | 8 | 64 |
| M8.4XLARGE128 | 16 | 128 |
| M8.8XLARGE256 | 32 | 256 |
| M8.16XLARGE512 | 64 | 512 |

### MA5

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| MA5.LARGE32 | 4 | 32 |
| MA5.2XLARGE64 | 8 | 64 |
| MA5.4XLARGE128 | 16 | 128 |
| MA5.8XLARGE256 | 32 | 256 |
| MA5.16XLARGE512 | 64 | 512 |

### MA4

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| MA4.LARGE32 | 4 | 32 |
| MA4.2XLARGE64 | 8 | 64 |
| MA4.4XLARGE128 | 16 | 128 |
| MA4.8XLARGE256 | 32 | 256 |
| MA4.16XLARGE512 | 64 | 512 |

### MA3

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| MA3.SMALL8 | 1 | 8 |
| MA3.MEDIUM16 | 2 | 16 |
| MA3.LARGE32 | 4 | 32 |
| MA3.2XLARGE64 | 8 | 64 |
| MA3.4XLARGE128 | 16 | 128 |
| MA3.8XLARGE256 | 32 | 256 |

### M6

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| M6.SMALL8 | 1 | 8 |
| M6.MEDIUM16 | 2 | 16 |
| M6.LARGE32 | 4 | 32 |
| M6.2XLARGE64 | 8 | 64 |
| M6.4XLARGE128 | 16 | 128 |
| M6.8XLARGE256 | 32 | 256 |
| M6.31MEDIUM470 | 62 | 470 |
| M6.31XLARGE940 | 124 | 940 |

### M5

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| M5.SMALL8 | 1 | 8 |
| M5.MEDIUM16 | 2 | 16 |
| M5.LARGE32 | 4 | 32 |
| M5.2XLARGE64 | 8 | 64 |
| M5.3XLARGE96 | 12 | 96 |
| M5.4XLARGE128 | 16 | 128 |
| M5.8XLARGE256 | 32 | 256 |
| M5.16XLARGE512 | 64 | 512 |

---

## Compute-Optimized Instances

### C6

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| C6.LARGE8 | 4 | 8 |
| C6.LARGE16 | 4 | 16 |
| C6.2XLARGE16 | 8 | 16 |
| C6.2XLARGE32 | 8 | 32 |
| C6.4XLARGE32 | 16 | 32 |
| C6.4XLARGE64 | 16 | 64 |
| C6.8XLARGE128 | 32 | 128 |
| C6.23MEDIUM216 | 46 | 216 |
| C6.16XLARGE256 | 64 | 256 |
| C6.20XLARGE320 | 80 | 320 |
| C6.23XLARGE432 | 92 | 432 |

### C5

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| C5.LARGE8 | 4 | 8 |
| C5.LARGE16 | 4 | 16 |
| C5.2XLARGE16 | 8 | 16 |
| C5.2XLARGE32 | 8 | 32 |
| C5.4XLARGE32 | 16 | 32 |
| C5.4XLARGE64 | 16 | 64 |
| C5.8XLARGE64 | 32 | 64 |
| C5.8XLARGE128 | 32 | 128 |
| C5.12XLARGE96 | 48 | 96 |
| C5.12XLARGE192 | 48 | 192 |
| C5.13XLARGE184 | 52 | 184 |
| C5.16XLARGE256 | 64 | 256 |
| C5.26XLARGE368 | 104 | 368 |

### C4

| Instance Type | vCPU | Memory (GB) |
|---|---|---|
| C4.LARGE8 | 4 | 8 |
| C4.LARGE16 | 4 | 16 |
| C4.2XLARGE16 | 8 | 16 |
| C4.2XLARGE32 | 8 | 32 |
| C4.4XLARGE64 | 16 | 64 |
| C4.8XLARGE174 | 32 | 174 |
| C4.16XLARGE348 | 64 | 348 |

---

## GPU / Heterogeneous Instances

### GT4

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| GT4.4XLARGE96 | NVIDIA A100 × 1 | 40GB × 1 | 16 | 96 |
| GT4.8XLARGE192 | NVIDIA A100 × 2 | 40GB × 2 | 32 | 192 |
| GT4.20XLARGE474 | NVIDIA A100 × 4 | 40GB × 4 | 82 | 474 |
| GT4.41XLARGE948 | NVIDIA A100 × 8 | 40GB × 8 | 164 | 948 |

### GN10Xp

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| GN10Xp.2XLARGE40 | NVIDIA V100 × 1 | 32GB × 1 | 10 | 40 |
| GN10Xp.5XLARGE80 | NVIDIA V100 × 2 | 32GB × 2 | 20 | 80 |
| GN10Xp.10XLARGE160 | NVIDIA V100 × 4 | 32GB × 4 | 40 | 160 |
| GN10Xp.20XLARGE320 | NVIDIA V100 × 8 | 32GB × 8 | 80 | 320 |

### GN10X

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| GN10X.2XLARGE40 | NVIDIA V100 × 1 | 32GB × 1 | 8 | 40 |
| GN10X.4XLARGE80 | NVIDIA V100 × 2 | 32GB × 2 | 18 | 80 |
| GN10X.9XLARGE160 | NVIDIA V100 × 4 | 32GB × 4 | 36 | 160 |
| GN10X.18XLARGE320 | NVIDIA V100 × 8 | 32GB × 8 | 72 | 320 |

### GN8

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| GN8.LARGE56 | NVIDIA P40 × 1 | 24GB × 1 | 6 | 56 |
| GN8.3XLARGE112 | NVIDIA P40 × 2 | 24GB × 2 | 14 | 112 |
| GN8.7XLARGE224 | NVIDIA P40 × 4 | 24GB × 4 | 28 | 224 |
| GN8.14XLARGE448 | NVIDIA P40 × 8 | 24GB × 8 | 56 | 448 |

### GN7

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| GN7.2XLARGE32 | NVIDIA T4 × 1 | 16GB × 1 | 8 | 32 |
| GN7.5XLARGE80 | NVIDIA T4 × 1 | 16GB × 1 | 20 | 80 |
| GN7.8XLARGE128 | NVIDIA T4 × 1 | 16GB × 1 | 32 | 128 |
| GN7.10XLARGE160 | NVIDIA T4 × 2 | 16GB × 2 | 40 | 160 |
| GN7.20XLARGE320 | NVIDIA T4 × 4 | 16GB × 4 | 80 | 320 |

### GI3X

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| GI3X.8XLARGE64 | NVIDIA T4 × 1 | 16GB × 1 | 32 | 64 |
| GI3X.22XLARGE226 | NVIDIA T4 × 2 | 16GB × 2 | 90 | 226 |
| GI3X.45XLARGE452 | NVIDIA T4 × 4 | 16GB × 4 | 180 | 452 |

### PNV4

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| PNV4.7XLARGE116 | NVIDIA A10 × 1 | 24GB × 1 | 28 | 116 |
| PNV4.14XLARGE232 | NVIDIA A10 × 2 | 24GB × 2 | 56 | 232 |
| PNV4.28XLARGE466 | NVIDIA A10 × 4 | 24GB × 4 | 112 | 466 |
| PNV4.56XLARGE932 | NVIDIA A10 × 8 | 24GB × 8 | 224 | 932 |

### PNV5b

Note: PNV5b is in invite-only testing (邀测).

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| PNV5b.8XLARGE96 | NVIDIA GPU × 1 | 48GB × 1 | 32 | 96 |
| PNV5b.12XLARGE192 | NVIDIA GPU × 1 | 48GB × 1 | 48 | 192 |
| PNV5b.16XLARGE192 | NVIDIA GPU × 2 | 48GB × 2 | 64 | 192 |
| PNV5b.24XLARGE384 | NVIDIA GPU × 2 | 48GB × 2 | 96 | 384 |
| PNV5b.32XLARGE384 | NVIDIA GPU × 4 | 48GB × 4 | 128 | 384 |
| PNV5b.48XLARGE768 | NVIDIA GPU × 4 | 48GB × 4 | 192 | 768 |
| PNV5b.64XLARGE768 | NVIDIA GPU × 8 | 48GB × 8 | 256 | 768 |
| PNV5b.96XLARGE1536 | NVIDIA GPU × 8 | 48GB × 8 | 384 | 1536 |

### PNV6

Note: PNV6 is in invite-only testing (邀测).

| Instance Type | GPU | GPU Memory | vCPU | Memory (GiB) |
|---|---|---|---|---|
| PNV6.4XLARGE160 | NVIDIA GPU × 1 | 96GB × 1 | 16 | 160 |
| PNV6.8XLARGE320 | NVIDIA GPU × 2 | 96GB × 2 | 32 | 320 |
| PNV6.16XLARGE640 | NVIDIA GPU × 4 | 96GB × 4 | 64 | 640 |
| PNV6.32XLARGE1280 | NVIDIA GPU × 8 | 96GB × 8 | 128 | 1280 |
| PNV6.96XLARGE2304 | NVIDIA GPU × 8 | 96GB × 8 | 384 | 2304 |
