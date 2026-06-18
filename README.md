# llm-clip

Feed the system clipboard to [`llm`](https://llm.datasette.io/) as an attachment,
without manually saving a file first.

```
llm-clip -m gpt-4o "describe what's on my clipboard"
```

becomes:

```
llm --at /tmp/llm-clip-xxxx.png image/png -m gpt-4o "describe what's on my clipboard"
```

## How it works

`llm-clip` reads the clipboard, writes it to a temp file, detects its mimetype,
and runs `llm` with `--at <file> <mimetype>`. Every other argument is forwarded
to `llm` unchanged. The temp file is removed after `llm` exits.

When several representations are on the clipboard, it prefers, high to low:
`image/png`, `image/tiff`, `image/jpeg`, `text/html`, `text/plain`. TIFF images
are transcoded to PNG; PNG and JPEG pass through untouched.

## Options

- `--force-type TYPE` — force a clipboard type: a mimetype (`image/png`,
  `text/html`, `text/plain`) or an alias (`image`, `html`, `text`).
- `--keep` — keep the temp file and print its path.
- `--dry-run` — print the `llm` command (and keep the temp file) without running.

## Platforms

- macOS — reads the pasteboard via PyObjC (`NSPasteboard`).
- Linux — reads via `wl-paste`, `xclip`, or `xsel` (whichever is installed).

## Install

```
uv tool install llm-clip
```

## License

AGPL-3.0-or-later.
