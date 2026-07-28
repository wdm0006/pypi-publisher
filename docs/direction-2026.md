# Direction 2026: does `ppp` still have a reason to exist?

**Recommendation: archive.** Every step `ppp` automates today is now well served by tools
that are maintained, and the one part of its pitch that is still distinctive — writing
credentials into `~/.pypirc` — has become a liability rather than a feature; the two release
steps that genuinely remain unserved (post-publish install verification, and yanking a bad
release) are respectively too small to justify a package and blocked upstream at PyPI.

- **Status of this document:** decision input for the maintainer. It changes no code.
- **Research date:** all tool versions, behaviours and issue states below were checked on
  **2026-07-27**. Every claim is version-qualified so it can be re-checked later.
- **Scope:** the complete release journey, not package building in isolation.
- **Runner-up option and the conditions that would flip the call:** see
  [What would change this decision](#what-would-change-this-decision).

---

## 1. What `ppp` actually does today

Establishing the baseline precisely matters, because the gap analysis is against *this*, not
against the README's aspiration.

| Capability | Where | Notes |
|---|---|---|
| Upsert a server into `~/.pypirc` | `ppp/ppp.py:58-126` | Writes `repository`, `username`, `password` in cleartext; file mode is now `0600` (`ppp/ppp.py:40-55`). |
| Lint the package directory | `ppp/ppp.py:22-37` | Asserts exactly three files exist: `MANIFEST.in`, `setup.py`, `setup.cfg`. |
| Read the version | `ppp/ppp.py:129-144` | Textual scan of `setup.py` for the first line starting `version` / `__version`. |
| Create and push a git tag | `ppp/ppp.py:147-173` | Annotated tag named after the parsed version; refuses duplicates; `git push --tags`. |
| Build and upload | `ppp/ppp.py:176-212` | `python -m build`, then `python -m twine upload -r <server> dist/*`. |
| List configured servers | `ppp/ppp.py:215-243` | Prints `[distutils] index-servers` from `~/.pypirc`. |

The pitch in the README's Overview section is that these are combined into one command
("upsert into your .pypirc file … create the git tag … lint the directory … then register and
push it all up"). Two structural
facts follow from the table and they drive most of what comes later:

1. **`ppp` only works on legacy setuptools layouts.** `lint_dir()` hard-fails a project without
   `MANIFEST.in`, `setup.py` *and* `setup.cfg`, and `get_version()` can only read a version out
   of `setup.py`. A `pyproject.toml`-only project — the shape PEP 621 has made standard, and the
   shape every tool below emits by default — cannot use `ppp` at all. This is not a small gap to
   close; it is most of the tool's preflight and version logic.
2. **`ppp`'s remaining differentiator is `.pypirc` management**, since build and upload are now
   a thin shell around `build` and `twine`, and tagging is a thin shell around `git tag`.

---

## 2. Ecosystem survey

Versions are the latest on PyPI as of 2026-07-27 unless noted.

### Summary

| Tool | Version (2026-07-27) | Builds? | Uploads? | Reads `~/.pypirc`? | Trusted Publishing? |
|---|---|---|---|---|---|
| `uv` | 0.11.32 (2026-07-23) | `uv build` | `uv publish` | **No** (open request) | Yes |
| `hatch` | 1.17.1 (2026-07-08) | `hatch build` | `hatch publish` | Yes | Yes (recommends the PyPA action) |
| `flit` | 3.12.0 (2025-03-25) | `flit build` | `flit publish` | Yes | Via env vars / CI |
| `twine` | 7.0.0 (2026-07-27) | No | `twine upload` | Yes | Via CI token injection |
| `build` | 1.5.0 (2026-04-30) | Yes | No | n/a | n/a |
| `python-semantic-release` | 10.6.1 (2026-07-06) | Delegates | Delegates | n/a | n/a |
| `pypa/gh-action-pypi-publish` | `release/v1` | **No** | Yes | n/a | Yes, default |

### `uv` 0.11.32

`uv build` produces sdist and wheel into `dist/` by default; `uv publish` uploads and does not
build. `uv publish` accepts `--username` / `--password` / `--token`, `--publish-url`,
`--keyring-provider`, `--index <name>` (resolved against `[[tool.uv.index]]` in
`pyproject.toml`), and `--check-url`, which skips files already identical on the target index.
The docs are explicit that on a Trusted Publisher "you don't need to set any credentials."

Two details matter for this decision:

- **`uv publish` does not read `~/.pypirc`.** [astral-sh/uv#7676](https://github.com/astral-sh/uv/issues/7676),
  filed 2024-09-24, asks for `-r/--repository` backed by `.pypirc`; it is still open and
  labelled `needs-decision` as of 2026-07-27. A third-party wrapper, `uv-publish` 1.4
  (2026-04-05), exists solely to read `~/.pypirc` and forward the credentials to `uv publish`.
- **`uv version --bump {major,minor,patch,…}`** edits the version in `pyproject.toml`, so the
  version-bump step is covered by the same tool.

### `hatch` 1.17.1

`hatch publish` uploads `.whl` and `.tar.gz` from `dist/` via the default `index` publisher, and
is pluggable through a publisher plugin API. Its authentication resolves in order —
`--user`/`-u`, `HATCH_INDEX_USER`, the `repos` config tables, **`~/.pypirc`**, an interactive
prompt, then `__token__` — with the password preferentially taken from `~/.pypirc` when the
username came from there, and otherwise from `--auth`, `HATCH_INDEX_AUTH`, config, or the OS
keyring. Hatch's own guidance for automation is to use "Trusted Publishing with OIDC (e.g.
PyPA's `pypi-publish` GitHub Action) or per-project API tokens."

So `.pypirc` reading — the interoperability `ppp` writes for — is already handled natively, and
the tool that handles it recommends *not* relying on stored credentials for automation.

### `flit` 3.12.0

`flit publish` builds a wheel and an sdist *and* uploads them, which makes it the closest
single-command analogue to `ppp publish` in the modern set. It selects a repository with
`--repository <name>` against a section of `~/.pypirc` (path overridable with `--pypirc`), and
also accepts `FLIT_USERNAME` / `FLIT_PASSWORD` / `FLIT_INDEX_URL`, with token uploads done by
setting `FLIT_USERNAME=__token__`. `flit install` exists but installs the working tree, not a
downloaded artifact, so it is not a post-publish verification step.

### `twine` 7.0.0

The reference uploader, and the thing `ppp publish` actually shells out to. Commands are
`upload`, `check`, and `register` (the last is only meaningful for non-PyPI indexes; PyPI
removed registration). `--repository` selects a `.pypirc` section; keyring is supported.

Two limits are load-bearing for section 3:

- **`twine check` validates only that the long description will render on PyPI** (`--strict`
  fails on warnings). It does not install anything, does not import anything, and says nothing
  about whether the wheel contains the package.
- **`--skip-existing` is PyPI/TestPyPI-only** as of twine 6.2.0 (2025-09-04), which removed it
  for other indexes over compatibility problems, and also dropped MD5 digests. twine 6.1.0
  (2025-01-21) dropped egg, wininst and `.tar.bz2` uploads.

### `python-semantic-release` 10.6.1

Determines the next version by parsing commit messages, generates a changelog from them (with
Markdown and reStructuredText templates), commits the bump, creates the tag, and publishes a
release to GitHub / GitLab / Gitea / Bitbucket. It runs a **configured build command** rather
than building itself, and it does **not** upload to PyPI — that stays with twine, `uv publish`
or the PyPA action in your pipeline. It performs no install verification.

This covers the front half of the journey (`bump → changelog → tag`) far more thoroughly than
`ppp`'s `check_tag()`, which derives a tag from a hand-edited `setup.py` version and writes no
changelog at all.

### PyPI Trusted Publishing (OIDC)

PyPI exchanges a short-lived OIDC identity token from a trusted CI provider for a PyPI API
token that is **valid for 15 minutes**, removing the need for a long-lived token in the release
path. PyPI's own framing of the risk is that "an attacker who compromises a package's release
token can use it until its legitimate user notices and manually revokes it."

This is the finding that most directly undercuts `ppp`'s core feature. `ppp`'s job is to persist
a username and password into `~/.pypirc`; the ecosystem's direction of travel is to hold no
durable upload credential at all. Note also that `ppp` takes the secret as `-p/--password` on the
command line (`ppp/ppp.py:273`), so it lands in shell history and in the process table.

### `pypa/gh-action-pypi-publish` (`release/v1`)

Uploads whatever is already in `dist/`. It is emphatic that it does not build: "This GitHub
Action has nothing to do with *building package distributions*. Users are responsible for
preparing dists for upload by putting them into the `dist/` folder prior to running this
Action." Trusted Publishing works by default given `id-token: write` and no explicit
credentials. `verify-metadata` (runs `twine check`) is **on** by default; `skip-existing` is
**off** by default; PEP 740 attestations are generated and uploaded **by default** on Trusted
Publishing flows and can be turned off with `attestations: false`.

PEP 740 ("Index Support for Digital Attestations") is Final, resolved 2024-07-17, and defines
how signed provenance is uploaded and served. `ppp` produces no attestations and has no path to
them, because it is designed to run on a maintainer's laptop with a stored password rather than
under an OIDC identity.

### Adjacent quality tools, for completeness

`check-manifest` 0.51 (2025-10-15) checks `MANIFEST.in` completeness against version control —
i.e. it does the job `lint_dir()` gestures at, properly. `check-wheel-contents` 0.6.3
(2025-08-02) checks that a built wheel contains what it should. `pyroma` 5.0.1 (2025-12-09)
scores packaging metadata quality. All three are more capable than `ppp`'s three-file existence
check, and none of them require a `setup.py`.

---

## 3. Journey gap analysis

The unit of analysis is the maintainer's full path from "I have a change worth releasing" to
"a user can install it, and I can recover if it is broken."

| # | Step | Verdict | Who serves it |
|---|---|---|---|
| 1 | Decide and apply the version bump | **Served** | `uv version --bump`, `hatch version`, `python-semantic-release`, `bump-my-version` |
| 2 | Generate a changelog | **Served** | `python-semantic-release`, `towncrier`, `git-cliff` |
| 3 | Create and push the tag | **Served** | `python-semantic-release`, plain `git`, `gh release create` |
| 4 | Preflight the package | **Partly served** | `twine check` (rendering only), `check-manifest`, `check-wheel-contents`, `pyroma` — capable but unbundled |
| 5 | Build sdist + wheel | **Served** | `build`, `uv build`, `hatch build`, `flit build` |
| 6 | Publish to a test index | **Served** | `twine -r testpypi`, `uv publish --publish-url`, `hatch -r test`, `flit --repository` |
| 7 | **Verify the artifact installs and runs** | **Unserved** | Nobody. Documented as a manual recipe; no tool does it |
| 8 | Promote the same artifacts to prod | **Partly served** | Mechanically trivial; nothing enforces "same bytes you verified" |
| 9 | **Recover from a bad release** | **Unserved, and blocked upstream** | No API exists |

### Step 4 — preflight: partly served

`twine check` is the only preflight bundled into the publish path, and it checks long-description
rendering, nothing more. The real checks live in separate tools (`check-manifest`,
`check-wheel-contents`, `pyroma`) that a maintainer has to know about and wire up individually.
There is a genuine "nobody runs the right preflights" gap here — but it is a *discovery and
convention* gap, not a missing-capability gap, and `ppp`'s contribution to it
(`lint_dir()`, `ppp/ppp.py:22-37`) is strictly worse than any of the three: it asserts the
existence of three legacy files and inspects the contents of none of them.

### Step 7 — verify the artifact installs and runs: unserved

This is the strongest finding in the survey, and it is the step `CONTRIBUTING.md` already
identified ("A testing command for attempting to install a package from the test pypi server
after upload").

- `twine check` does not install.
- `flit install` installs the working tree, not the published artifact.
- `uv publish` uploads and stops. The uv docs *recommend* verifying by hand —
  `uv run --with <PACKAGE> --no-project -- python -c "import <PACKAGE>"` — which is an
  admission that the tool does not do it. uv's GitHub Actions guide likewise shows smoke tests
  as workflow steps the user writes.
- `pypa/gh-action-pypi-publish` uploads and stops.

So the state of the art is a documented recipe the maintainer copies into CI. That is a real
gap: a wheel that installs but is missing its package directory, or an sdist that cannot be
built from, passes every automated check in the list above and fails only for users.

Two things complicate exploiting it, and both are load-bearing for the recommendation:

- **TestPyPI is a poor verification substrate.** Packaging's own guide notes its database "may
  be periodically pruned, so it is not unusual for user accounts to be deleted," and that
  installing from it needs `--index-url https://test.pypi.org/simple/ --extra-index-url
  https://pypi.org/simple/` because dependencies generally are not there. Verifying against
  TestPyPI therefore tests a different dependency graph than production.
- **The useful version of the check does not need an index at all.** Installing the local
  `dist/*.tar.gz` and `dist/*.whl` into clean environments and importing is strictly better
  evidence, available before anything is uploaded, and is roughly three lines of `uv run`.

### Step 8 — promote to prod: partly served

Re-uploading the artifacts you already verified is a one-liner (`twine upload -r pypi dist/*`).
What no tool provides is the guardrail — nothing records that the bytes going to production are
the bytes that passed the test-index install. `uv publish --check-url` is the nearest thing, and
it is about not re-uploading *different* content under the same name, not about promotion. `ppp`
does not address this: `publish()` rebuilds and uploads from `dist/`, so a `ppp publish` to prod
after a `ppp publish` to test produces fresh artifacts.

### Step 9 — recover from a bad release: unserved and blocked

This is where the wishlist's "rollback command (remove a release)" runs into PyPI policy rather
than a tooling gap:

- **Deletion is not a rollback.** PyPI: "Deletion of a project, release or file on PyPI is
  permanent and irreversible, without exception," and "PyPI does not allow for a filename to be
  reused, even once a project has been deleted and recreated." The documented remedy is to bump
  the version and upload a new one.
- **Yanking is the actual recovery mechanism** (PEP 592) — installers skip a yanked release
  unless it is the only match — and PyPI recommends it for a release that is "broken or
  uninstallable," violates its compatibility guarantees, or contains a vulnerability.
- **Yanking cannot be automated.** It is available only through the PyPI web UI.
  [pypa/packaging-problems#633](https://github.com/pypa/packaging-problems/issues/633) (opened
  2022-12-20) and [pypi/warehouse#12708](https://github.com/pypi/warehouse/issues/12708) (opened
  2022-12-21) both request programmatic yanking and both are **still open as of 2026-07-27**.
  PyPI's documented APIs cover index, JSON, integrity, stats, BigQuery, RSS and secret
  reporting; the only documented write endpoint is upload.

A `ppp rollback` cannot be built correctly today by anyone. This is not a niche `ppp` is
declining to fill; it is a niche that is closed at the registry.

---

## 4. Candidate niches

Taking the unserved and partly-served steps in turn, and asking honestly whether `ppp` is a
plausible home for each.

### A. Post-publish (or pre-publish) install-and-run verification — step 7

**Who feels the pain.** A solo maintainer with many small packages, who releases each one
rarely enough that the release process is never muscle memory, and for whom a broken wheel is
discovered by a user rather than by CI. Secondarily, anyone publishing to a private/internal
index, where there is no community to notice a broken artifact quickly.

**What the tool would be.** Given a built `dist/`, create a clean environment per artifact and
per target Python, install the sdist and the wheel *separately*, import the top-level modules,
run each declared console script with `--help`, and report. Optionally repeat against the
uploaded copy on the target index.

**Is `ppp` a plausible home?** Weakly. The gap is real, but the implementation is small enough
that its value is mostly in *convention* — and convention is carried by discoverability. A
package named `pypi-publisher`, whose PyPI description is "A cli for publishing packages to
pypi, without the hassle" and whose README leads with `.pypirc` upsert, is not where anyone
looks for a verifier. Delivering this from `ppp` means keeping the name and discarding
essentially all of `ppp/ppp.py` — the `.pypirc` code, `lint_dir()`, `get_version()`,
`check_tag()`, and `publish()`. That is a new tool wearing a misleading name.

### B. `.pypirc` as a compatibility shim for `uv` — steps 6 and 8

**Who feels the pain.** A maintainer with a long-standing `~/.pypirc` full of named private
indexes who is migrating to `uv` and finds `uv publish` cannot see any of it
(astral-sh/uv#7676).

**Is `ppp` a plausible home?** No. This is the narrowest reading of `ppp`'s existing
differentiator, and it is already occupied: `uv-publish` 1.4 does exactly this and nothing else.
It is also a bet against the ecosystem — uv may simply implement `-r`, at which point the shim
is dead. And it is a bet on durable stored credentials at the moment Trusted Publishing is
removing them.

### C. Bundled preflight — step 4

**Who feels the pain.** Maintainers who do not know `check-manifest`, `check-wheel-contents` and
`pyroma` exist.

**Is `ppp` a plausible home?** No, in the sense that matters: aggregating three well-maintained
tools behind one command is a preferences file, not a package. And if it were worth packaging,
it belongs with capability A, not with a publisher.

### D. Rollback — step 9

Not available to anyone. See step 9 above. Closed until PyPI ships a write API.

### E. Monorepo / multi-package release orchestration

Considered and rejected as out of scope for this evaluation's evidence base: the survey did not
find this to be unserved so much as *solved differently per stack* (workspace-aware release
tooling, `uv` workspaces), and nothing in `ppp` — which assumes a single `setup.py` in the
current working directory — is a starting point for it.

---

## 5. Recommendation: archive

**Archive `pypi-publisher`.** No defensible niche remains for it in its current shape, and the
two niches that do exist are not ones this package can credibly occupy.

The reasoning traces to specific findings above:

1. **Its differentiator has become an anti-feature.** `ppp`'s distinct contribution is writing
   credentials into `~/.pypirc` (`ppp/ppp.py:58-126`), with the password supplied on argv
   (`ppp/ppp.py:273`). Trusted Publishing replaces durable upload credentials with 15-minute
   OIDC-minted tokens (§2), and the maintainer of the one other tool that natively reads
   `.pypirc` for publishing — hatch — recommends Trusted Publishing or per-project tokens for
   automation. Meanwhile the tool that *doesn't* read `.pypirc` (uv) already has a dedicated
   third-party shim. There is no version of this feature that is both wanted and unoccupied.
2. **It cannot run on the projects it would be recommended for.** `lint_dir()`
   (`ppp/ppp.py:22-37`) requires `MANIFEST.in` + `setup.py` + `setup.cfg`, and `get_version()`
   (`ppp/ppp.py:129-144`) can only read a version from `setup.py`. A `pyproject.toml`-only
   project cannot use `ppp` at all. Fixing this is not a patch; it replaces the preflight and
   version logic outright.
3. **The steps it does automate are the well-served ones.** Steps 1, 2, 3, 5 and 6 of the
   journey table are all marked served, by multiple maintained tools, several of which
   (`flit publish`, `hatch publish`) already collapse build-and-upload into one command the way
   `ppp publish` does — without requiring a legacy layout.
4. **The steps that are unserved are not ones it can take.** Step 9 is blocked at PyPI (two
   open upstream issues since 2022; no write API beyond upload). Step 7 is real but small, and
   capturing it means discarding the whole current codebase while keeping a name that actively
   misdirects — which is a worse starting position than a new project with an accurate name.
5. **There is no user base pulling the other way.** The last release, 0.0.4, was uploaded
   2016-03-02 and the package is still classified `Development Status :: 3 - Alpha`. It shows
   ~2.7k downloads in the last 30 days, but PyPI download counts include mirrors, scanners and
   CI, so for a package with no release in ten years this is not evidence of human users. The
   repository has 47 stars, 1 fork and 2 watchers.

A negative result was an explicitly acceptable outcome here, and this is one. The recent repair
work — duplicate-tag detection, the GitPython pin, the `build` + `twine` migration, the `0600`
`.pypirc` mode, the dry-run fix — was worth doing to reach a state where this question could be
answered honestly rather than around a broken tool. It does not obligate a revival.

### Suggested archive note

If the maintainer accepts this recommendation, this replaces the "Project direction under
review" banner currently at the top of `README.md`:

> **This project is archived and is no longer maintained.**
>
> `ppp` was written in 2016 to combine `.pypirc` management, a directory check, git tagging and
> a `setup.py` upload into one command. All of those steps are now covered by maintained tools,
> and its central feature — storing an index username and password in `~/.pypirc` — has been
> superseded by PyPI Trusted Publishing, which issues short-lived tokens instead. `ppp` also
> only works on legacy `setup.py` projects and cannot read a version from `pyproject.toml`.
>
> See [`docs/direction-2026.md`](docs/direction-2026.md) for the full assessment, and the
> section below for what to use instead.
>
> The repository stays public and read-only. Version 0.0.4 remains installable from PyPI; it
> will not be yanked, since it is not broken so much as obsolete.

---

## 6. If you are using `ppp` today: what to do instead

Replace `ppp publish` with two commands and one decision. Build with `uv build` (or
`python -m build`, `hatch build`, `flit build` — any of them; they are interchangeable for this
purpose and all produce `dist/`). Then either upload from your laptop with
`twine upload -r <server> dist/*`, which reads the same `~/.pypirc` `ppp` was writing so your
existing server sections keep working unchanged — or, better, stop holding an upload credential
at all: configure a PyPI Trusted Publisher for the project and let
`pypa/gh-action-pypi-publish` upload from a tagged CI run, which additionally gets you PEP 740
attestations by default. For tagging, use `git tag`/`gh release create` directly, or adopt
`python-semantic-release` if you want the version bump, changelog and tag derived from commit
messages. Before any of that, run `uv run --with dist/<your-package>-<version>-py3-none-any.whl
--no-project -- python -c "import <your_package>"` against the built wheel and again against the
sdist — the install-and-run check nothing in the toolchain does for you, and the one habit from
`ppp`'s wishlist genuinely worth keeping.

---

## What would change this decision

Stated explicitly so this doc can be re-checked rather than re-argued:

- **Reposition instead of archive** becomes the better call if the maintainer wants to build
  capability A (§4) *and* is willing to rename — new PyPI name, new README, new CLI verbs, with
  `pypi-publisher` archived and pointing at it. Repositioning under the existing name is the
  option this doc rejects, not the capability.
- **Revive** becomes plausible only if PyPI ships a write API for yanking — watch
  [pypa/packaging-problems#633](https://github.com/pypa/packaging-problems/issues/633) and
  [pypi/warehouse#12708](https://github.com/pypi/warehouse/issues/12708). A working
  `release → verify → yank-on-failure` loop is a real tool; today its last step cannot be
  implemented.
- **The `.pypirc` shim niche (§4B) reopens** only if `uv` closes
  [astral-sh/uv#7676](https://github.com/astral-sh/uv/issues/7676) as *won't fix* **and**
  `uv-publish` goes unmaintained. Even then it is a small, shrinking niche.

## Sources

Checked 2026-07-27. Versions from the PyPI JSON API on the same date.

- [uv — Building and publishing a package](https://docs.astral.sh/uv/guides/package/) ·
  [uv — GitHub Actions integration](https://docs.astral.sh/uv/guides/integration/github/) ·
  [astral-sh/uv#7676 — `.pypirc` support](https://github.com/astral-sh/uv/issues/7676)
- [Hatch — Publishing](https://hatch.pypa.io/latest/publish/) ·
  [Hatch — Publisher authentication](https://hatch.pypa.io/latest/how-to/publish/auth/)
- [Flit — command line interface](https://flit.pypa.io/en/stable/cmdline.html)
- [Twine documentation](https://twine.readthedocs.io/en/stable/) ·
  [Twine changelog](https://twine.readthedocs.io/en/stable/changelog.html)
- [python-semantic-release](https://python-semantic-release.readthedocs.io/en/latest/)
- [PyPI — Trusted publishers](https://docs.pypi.org/trusted-publishers/) ·
  [PyPI — Yanking](https://docs.pypi.org/project-management/yanking/) ·
  [PyPI — APIs](https://docs.pypi.org/api/) · [PyPI — Help](https://pypi.org/help/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [PEP 740 — Index support for digital attestations](https://peps.python.org/pep-0740/) ·
  [PEP 592 — Adding "yank" support to the simple API](https://peps.python.org/pep-0592/)
- [Packaging guide — Using TestPyPI](https://packaging.python.org/en/latest/guides/using-testpypi/)
- [pypa/packaging-problems#633](https://github.com/pypa/packaging-problems/issues/633) ·
  [pypi/warehouse#12708](https://github.com/pypi/warehouse/issues/12708)
