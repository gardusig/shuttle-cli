# Configuration

Config loads from (first match):

1. `$SHUTTLE_CONFIG_DIR` if set
2. Repo `config/` directory (development)
3. `~/.config/shuttle-cli/`

## Files

| File | Purpose |
| --- | --- |
| `config.yaml` | Notion + Chrome defaults |
| `repositories.yaml` | Repository roots for future backup |
| `drives.yaml` | Drive provider toggles |

Example `repositories.yaml`:

```yaml
repositories:
  - ~/engineering
  - ~/private
```

Git shortcuts do not require config today.
