# pyavcontrol (Legacy)

> **This repository is superseded by [avprotocol](https://github.com/rsnodgrass/avprotocol).**
> All new protocol work, features, and bug fixes happen there.

## Status

| | pyavcontrol (this repo) | avprotocol |
|---|---|---|
| **Status** | Legacy / maintenance-only | Active development |
| **Package** | `pyavcontrol` v0.x | `pyavcontrol` 1.0.0 (v2 rewrite) |
| **Remote** | `rsnodgrass/pyavcontrol` | `rsnodgrass/avprotocol` |
| **Local** | `~/Code/ha/pyavcontrol/` | `~/Documents/Code/ha/avcontrol/` |
| **Protocol files** | ~14 YAML files, v1 schema | 448+ YAML files, v2 schema with inheritance |
| **API** | `DeviceModelLibrary`, `DeviceClient` | `ProtocolClient`, `CommandBuilder`, `ProtocolLibrary`, `EmulatorClient` |

## What NOT to do here

- **Don't add new protocols** - add them in avprotocol instead
- **Don't build new features** - the v2 rewrite in avprotocol is the active codebase
- **Don't create sync scripts** - avprotocol fully replaces this repo

## Schema differences (v1 vs v2)

- **v1** (this repo): flat YAML, no inheritance, limited metadata
- **v2** (avprotocol): `_base.yaml` / `_modern.yaml` inheritance, 6-layer documentation model, connection/protocol sections, rich command families

## For active development

Go to the avprotocol monorepo:

```
~/Documents/Code/ha/avcontrol/
  avcontrol/          # core pyavcontrol library (v2)
  avcontrol-docs/     # documentation site
  avcontrol-magic/    # orchestration and tooling
  avemu/              # device emulator
  conductor/          # multi-device orchestration
```
