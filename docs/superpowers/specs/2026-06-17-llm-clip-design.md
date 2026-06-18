# llm-clip — design

Date: 2026-06-17

## Purpose

Feed the system clipboard to Simon Willison's [`llm`](https://llm.datasette.io/)
as an attachment without a manual save-to-file dance. `llm-clip` reads whatever
is on the clipboard, writes it to a temp file, detects its mimetype, and runs
`llm` with that file attached — passing every other argument straight through.

```
llm-clip -m foogpt-4 "convert the text in this to ascii"
  → llm --at /tmp/llm-clip-xxxx.png image/png -m foogpt-4 "convert the text in this to ascii"
```

`--at PATH MIMETYPE` (the two-argument `--attachment-type` form) is used rather
than `-a`, because `llm-clip` always knows the mimetype explicitly. `llm-clip`
exits with `llm`'s return code, and the temp file is deleted after `llm` exits.

## Scope

- Platforms: macOS and Linux.
- A single new CLI, `llm-clip`, distributed as a uv package with a console-script
  entry point. Home on GitHub at `dannyob/llm-clip`.
- Out of scope (v1): Windows, clipboard *writing*, streaming stdin, multiple
  simultaneous attachments.

## Behaviour

### Format selection

The clipboard may hold the same content in several representations. `llm-clip`
picks one mimetype by priority, high to low:

1. `image/png`
2. `image/tiff`
3. `image/jpeg`
4. `text/html`
5. `text/plain`

This encodes the rule "image over html over plaintext", with png preferred
among image variants. The first priority-list entry that is actually present on
the clipboard wins.

`--force-type` overrides auto-selection. It accepts either a mimetype
(`image/png`, `text/html`, `text/plain`) or a short alias (`image`, `html`,
`text`). Aliases resolve to the highest-priority present type in that family
(`image` → first available of png/tiff/jpeg). If the forced type is not present
on the clipboard, `llm-clip` errors.

### Image normalisation

Because Tiff images are not commonly accepted (but are often provided on older MacOS programs), they are transcoded to PNG with [Pillow](https://pillow.readthedocs.io/)
before being attached.
PNG and JPEG data is passed through untouched.

### Argument passing

All arguments other than `llm-clip`'s own flags are forwarded to `llm`
verbatim, in order. `llm-clip`'s own flags are:

- `--force-type TYPE` (also `--force-type=TYPE`)
- `--keep` — do not delete the temp file; print its path to stderr
- `--dry-run` — print the `llm` command that would run (and keep the temp file)
  to stdout, without executing `llm`
- `-h` / `--help` — usage

To keep forwarding bulletproof, `cli.py` does a **manual argv split** rather
than handing argv to an option parser. A parser (click/argparse) would try to
interpret `llm`'s own flags (e.g. `-m`, abbreviations) and misfire. The split is
a pure function: it scans for the known `llm-clip` flags above and routes
everything else to the passthrough list. The flag names are deliberately
distinctive to avoid collision with `llm`'s options.

## Architecture

A pure core plus thin platform backends, so the selection and argument logic are
testable without a real clipboard.

```
src/llm_clip/
  cli.py        orchestration + manual argv split + running llm
  select.py     pure: choose mimetype from (available types, forced type)
  clipboard.py  Backend interface + Mac/Linux implementations + get_backend()
  images.py     normalise_image(data, mimetype) -> (bytes, mimetype)
```

### `select.py` (pure)

- `PRIORITY: list[str]` — the mimetype priority list above.
- `IMAGE_ALIASES`, alias map for `--force-type`.
- `choose(available: list[str], forced: str | None) -> str` — returns the chosen
  mimetype or raises a `NoUsableContent` / `ForcedTypeAbsent` error.

### `cli.py`

- `split_args(argv: list[str]) -> tuple[Options, list[str]]` — pure; returns
  parsed `llm-clip` options and the passthrough remainder.
- `main()`:
  1. `opts, passthrough = split_args(sys.argv[1:])`
  2. `backend = get_backend()`
  3. `mimetype = choose(backend.available_types(), opts.force_type)`
  4. `data = backend.read(mimetype)`
  5. if `mimetype == "image/tiff"`: `data, mimetype = normalise_image(data, mimetype)`
  6. write `data` to a `NamedTemporaryFile` with an extension from `mimetypes`
  7. build `["llm", "--at", path, mimetype, *passthrough]`
  8. `--dry-run`: print command, keep file, exit 0. Otherwise `subprocess.run`,
     inheriting stdio; clean up the temp file in a `finally` (unless `--keep`);
     exit with `llm`'s return code.

### `clipboard.py`

`Backend` protocol:

- `available_types() -> list[str]` — mimetypes currently on the clipboard.
- `read(mimetype: str) -> bytes` — raw bytes for that mimetype.

`get_backend()` selects by `sys.platform`.

- **MacBackend** — PyObjC `NSPasteboard.generalPasteboard()`. `types()` returns
  UTIs; map to mimetypes via a small table (`public.png`→`image/png`,
  `public.tiff`→`image/tiff`, `public.jpeg`→`image/jpeg`, `public.html`→`text/html`,
  `public.utf8-plain-text`/`public.plain-text`→`text/plain`). `read` calls
  `dataForType_` with the UTI for the requested mimetype and returns the bytes.
- **LinuxBackend** — chooses a clipboard tool at runtime: `wl-paste` (Wayland)
  if present, else `xclip`, else `xsel`. These speak mimetypes directly:
  `wl-paste --list-types`; `xclip -selection clipboard -t TARGETS -o`. Map X
  atoms `UTF8_STRING`/`STRING`/`TEXT` → `text/plain`. `read` runs
  `wl-paste --type <mime>` or `xclip -selection clipboard -t <mime> -o`.

### `images.py`

- `normalise_image(data: bytes, mimetype: str) -> tuple[bytes, str]` — if
  `mimetype` is `image/tiff`, open with Pillow and re-encode to PNG, returning
  `(png_bytes, "image/png")`. Any other mimetype (including `image/png` and
  `image/jpeg`) is returned unchanged.

## Error handling

All errors print a message to stderr and exit non-zero:

- Empty clipboard / no type in the priority list present.
- `--force-type` requests a type that is not on the clipboard.
- `llm` not found on PATH.
- On Linux, no clipboard tool (`wl-paste`/`xclip`/`xsel`) installed — message
  includes an install hint.
- Pillow fails to decode/transcode an image.

## Packaging

- uv package adapted from Danny's `py-template`; build backend `uv_build`.
- `requires-python = ">=3.10"`.
- Dependencies:
  - `pillow`
  - `pyobjc-framework-Cocoa; sys_platform == "darwin"`
  - (the template's `click` dependency is dropped — manual argv split instead.)
- `[project.scripts]`: `llm-clip = "llm_clip.cli:main"`.
- License: AGPL-3.0-or-later.

## Testing

pytest, TDD red/green. The pure units carry the coverage:

- `select.choose` — priority selection, alias resolution, forced-type-absent,
  empty-clipboard.
- `cli.split_args` — flags extracted, passthrough preserved in order,
  `--force-type=VALUE` and `--force-type VALUE` forms, our flags interleaved
  with `llm` flags.
- command building + temp-file lifecycle against a **fake backend** and a fake
  subprocess runner (assert the `llm` argv, assert cleanup / `--keep` / `--dry-run`).
- `images.normalise_image` — a small generated TIFF transcodes to valid PNG;
  PNG and JPEG are returned byte-for-byte unchanged.

Platform backends (PyObjC / shelling out) are thin and exercised by an
end-to-end smoke test: copy known content to the clipboard, run the built
`llm-clip --dry-run`, assert the chosen file + mimetype. Per Danny's rule, the
real binary gets a smoke test, not just unit tests.
