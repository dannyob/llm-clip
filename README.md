# llm-clip

Take whatever is on your clipboard, hand it to [`llm`](https://llm.datasette.io/) as an attachment, and forward the rest of your command line untouched.

Copy a screenshot, then:

```sh
$ llm-clip -m gpt-4o "what's the error in this stack trace?"
The NullPointerException is thrown at line 42 because `user` is null when
the session has expired. Guard with `if user is None: return` before the call.
```

`llm-clip` figures out the clipboard's mimetype, writes it to a temp file, and runs `llm --at <file> <mimetype> ...`. To see exactly what it would run without calling the model, use `--dry-run`:

```sh
$ printf 'def add(a, b):\n    return a + b\n' | pbcopy
$ llm-clip --dry-run -m gpt-4o "explain this code"
llm-clip: kept /var/folders/.../T/llm-clip-3bvrummu.txt
llm --at /var/folders/.../T/llm-clip-3bvrummu.txt text/plain -m gpt-4o 'explain this code'
```

Everything after `llm-clip`'s own flags goes straight to `llm`, in order, so `-m`, `-s`, `--schema`, and friends all work.

## Install

```sh
uv tool install git+https://github.com/dannyob/llm-clip
```

You need [`llm`](https://llm.datasette.io/en/stable/setup.html) installed and configured separately.

## Picking a representation

The clipboard usually holds the same thing several ways at once (a copied web image arrives as PNG *and* TIFF *and* a URL string). `llm-clip` picks one, highest priority first:

```
image/png  >  image/tiff  >  image/jpeg  >  text/html  >  text/plain
```

TIFF gets transcoded to PNG, because older macOS apps love putting TIFF on the pasteboard and most models won't take it. PNG and JPEG pass through byte-for-byte.

Override the choice with `--force-type`, which takes a mimetype or a short alias:

```sh
llm-clip --force-type text "summarise the plain-text version, ignore the rich copy"
llm-clip --force-type image "transcribe this"
```

Other flags: `--keep` leaves the temp file on disk and prints its path; `--dry-run` shows the command and keeps the file without running anything.

## Limitations

- It sends one clipboard item, not a selection of several.
- Reading images on macOS needs a logged-in GUI session (it goes through `NSPasteboard`/`osascript`). Over a bare SSH session with no window server, image grabs fail and you're limited to text.
- On Linux you need `wl-paste`, `xclip`, or `xsel` on PATH; it tries them in that order.
- Windows is untested. There's no Windows clipboard backend.

## Development

```sh
git clone https://github.com/dannyob/llm-clip
cd llm-clip
uv run pytest          # unit tests
./scripts/smoke.sh     # real end-to-end test (macOS; overwrites your clipboard)
```

The logic worth testing is pure and lives away from the OS: `select.py` (priority choice), `images.py` (TIFF transcode), and the argument-splitting in `cli.py`. The clipboard itself is a thin backend behind `clipboard.py`, exercised by the smoke test.

## License

AGPL-3.0-or-later.
