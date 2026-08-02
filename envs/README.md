# Service environment

`common.env`, `api.env`, `bot.env` and `worker.env` hold the **shipped
defaults**. They are tracked by git and are meant to stay untouched — editing
them makes every later `git pull` stop with:

```
error: Your local changes to the following files would be overwritten by merge
```

Put your own settings in a `*.local.env` beside them instead. Those are
gitignored, Compose loads them last, and last one wins:

| Edit this | Not this | Loaded by |
|---|---|---|
| `common.local.env` | `common.env` | every service |
| `api.local.env` | `api.env` | `yt_api` |
| `bot.local.env` | `bot.env` | `yt_bot` |
| `worker.local.env` | `worker.env` | `yt_worker` |

Only the keys you want to change need to be there:

```sh
cat > envs/worker.local.env <<'EOF'
MAX_SIMULTANEOUS_DOWNLOADS=1
DOWNLOAD_RATE_LIMIT=2M
METADATA_LANGUAGE=ru
EOF
```

The files are optional — with none of them present the stack runs on the
defaults. `./redeploy.sh` creates the missing ones empty, which also keeps
Compose older than 2.24 happy, since it treats a missing `env_file` as an error
rather than skipping it.

## Moving settings you already changed in place

```sh
git diff envs/          # what you changed, and in which file
                        # copy those lines into the matching *.local.env
git checkout -- envs/   # restore the tracked defaults
```

Nothing about the running stack changes: the values end up in the container
either way.
