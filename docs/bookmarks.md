# Chrome bookmarks

Shell-based export and import for Chrome bookmarks ([issue #1](https://github.com/gardusig/shuttle-cli/issues/1)).

## Requirements

- macOS with Google Chrome installed
- Default `~/Downloads` directory (or set `SHUTTLE_DOWNLOADS_DIR`)
- Accessibility permissions for Terminal if using GUI automation

## Export

```bash
./scripts/chrome/export-bookmarks.sh
```

Creates or replaces `data/bookmarks/bookmarks.html`.

## Import

```bash
./scripts/chrome/import-bookmarks.sh
```

Restores from `data/bookmarks/bookmarks.html`. Chrome may merge bookmarks with existing ones.

## Environment overrides

| Variable | Purpose |
| --- | --- |
| `SHUTTLE_ROOT` | Repository root (default: auto-detected) |
| `SHUTTLE_DOWNLOADS_DIR` | Downloads folder to poll |
| `SHUTTLE_BOOKMARKS_FILE` | Backup file path |
| `SHUTTLE_SKIP_CHROME_AUTOMATION` | Set to `1` to skip GUI steps (tests) |
| `SHUTTLE_BOOKMARKS_FIXTURE` | Use a local HTML file instead of waiting for download |

## Future CLI

These scripts will later be wrapped by:

```bash
shuttle bookmarks export
shuttle bookmarks import
```
