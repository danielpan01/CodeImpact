# V6 candidate decisions

The default-branch listings were queried on November 28, 2026 with the
October 1, 2025 UTC cutoff in the protocol. Rows show the inspected prefix
in listing order. Each listing stopped at its second eligible change.
The four reserve repositories were unused.

## martinblech/xmltodict

Default branch `master`.

| Position | Commit | Subject | Decision |
| ---: | --- | --- | --- |
| 1 | [`d079849136b0`](https://github.com/martinblech/xmltodict/commit/d079849136b031c471ec96a168ad7859ed5994ff) | chore(master): release 1.0.2 | Exclude. Release bookkeeping and version metadata only. |
| 2 | [`25b61a41f580`](https://github.com/martinblech/xmltodict/commit/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f) | fix: allow DOCTYPE with disable_entities=True (default) | Select `xmltodict_doctype`. Permits a DOCTYPE without entities while retaining an entity declaration refusal. The tests pin both inputs and explicit disabled and enabled parsing. |
| 3 | [`a2a9ab7e0692`](https://github.com/martinblech/xmltodict/commit/a2a9ab7e0692a62f64d97ff12553d0d53368c854) | ci(publish): allow uploading release assets | Exclude. Publish workflow permission change only. |
| 4 | [`656e6af9543e`](https://github.com/martinblech/xmltodict/commit/656e6af9543e640fda7e96d6bdd6e693756687be) | chore(master): release 1.0.1 | Exclude. Release bookkeeping and version metadata only. |
| 5 | [`c986d2d37a93`](https://github.com/martinblech/xmltodict/commit/c986d2d37a93d45fcc059b09063d9d9c45a655ec) | fix: fail closed when entities disabled | Select `xmltodict_entity_policy`. Changes the default parser handler registrations from ignoring declarations to refusing them. The tests pin declaration inputs and a normal-comment control. |

## theskumar/python-dotenv

Default branch `main`.

| Position | Commit | Subject | Decision |
| ---: | --- | --- | --- |
| 1 | [`16f2bdad2ebb`](https://github.com/theskumar/python-dotenv/commit/16f2bdad2ebbaae72790514cce713d2d22ab0f7c) | Update spacing and docs | Exclude. Moves an unchanged helper and edits documentation and formatting. The flag behavior is already present in the parent. |
| 2 | [`c715d19fb88e`](https://github.com/theskumar/python-dotenv/commit/c715d19fb88e81f04cf3506a3c2c2812621d1b46) | feat:  add `PYTHON_DOTENV_DISABLED` flag to disable load_dotenv (fixes #510) (#569) | Select `dotenv_disable_loading`. Introduces the environment flag at the public load_dotenv entry. Tests exercise recognized and unrecognized values with explicit environment setup. |
| 3 | [`666984de9a73`](https://github.com/theskumar/python-dotenv/commit/666984de9a730a54438362b1adedd09bb1e9f5c7) | Use sys.exit() instead of exit() (#568) | Exclude. The relevant CLI tests reach the exit replacement through external Click dispatch or a launched command. |
| 4 | [`02b68577f37d`](https://github.com/theskumar/python-dotenv/commit/02b68577f37da2c4f4b9377d7a0ca2b58fdacf20) | style: upgrade to use ruff (#567) | Exclude. Ruff migration and formatting across the repository, with no focal behavior. |
| 5 | [`16e660d384b9`](https://github.com/theskumar/python-dotenv/commit/16e660d384b942b11879b44500afbbe021650448) | Bump version: 1.1.0 → 1.1.1 | Exclude. Package version and release metadata only. |
| 6 | [`667e82f18d6e`](https://github.com/theskumar/python-dotenv/commit/667e82f18d6e5306894c8746c46b1da2d031bd23) | update changelog | Exclude. Changelog only. |
| 7 | [`9d85edb3b865`](https://github.com/theskumar/python-dotenv/commit/9d85edb3b8652de4601f9ad8a7a49ad9909f898a) | fix(cli): issue with execvpe on Windows (#566) | Exclude. The Windows behavior needs an external Click and subprocess execution path. The captured tests do not isolate the Windows branch. |
| 8 | [`8411987b9301`](https://github.com/theskumar/python-dotenv/commit/8411987b9301f716245074872afa30646e9b9eb7) | fix: ensure find_dotenv work reliably on python 3.13 (#563) | Select `dotenv_interactive_detection`. Adds sys.ps1 and sys.ps2 checks inside find_dotenv. New tests model shell state using captured test setup. |

## asottile/tokenize-rt

Default branch `main`.

| Position | Commit | Subject | Decision |
| ---: | --- | --- | --- |
| 1 | [`2ea376551908`](https://github.com/asottile/tokenize-rt/commit/2ea37655190845d13ae7756b066685014e398628) | Merge pull request #209 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 2 | [`59343a43b4ba`](https://github.com/asottile/tokenize-rt/commit/59343a43b4ba869f7d2b711b776fe85182c5cf20) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 3 | [`77f75bdadee3`](https://github.com/asottile/tokenize-rt/commit/77f75bdadee3b2c57ccb3dcc6078cbd5d0331711) | Merge pull request #208 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 4 | [`23b33a0edf34`](https://github.com/asottile/tokenize-rt/commit/23b33a0edf3403ca42ea3db681e4a38342a7ae1d) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 5 | [`b2f4fb778686`](https://github.com/asottile/tokenize-rt/commit/b2f4fb77868698b9bcdf565c88e46a7efcfd919a) | Merge pull request #207 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 6 | [`3bef5e00c8a7`](https://github.com/asottile/tokenize-rt/commit/3bef5e00c8a732da10dd1549263102508a7d8029) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 7 | [`d3874b787677`](https://github.com/asottile/tokenize-rt/commit/d3874b787677593fc34aedf7174a2934e2caa94b) | Merge pull request #206 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 8 | [`200023563d5e`](https://github.com/asottile/tokenize-rt/commit/200023563d5e38de4334f859d422595a5a3387be) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 9 | [`bcc3c664874b`](https://github.com/asottile/tokenize-rt/commit/bcc3c664874b810b40398065cb8c7d5c75030aa7) | Merge pull request #205 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 10 | [`0b4e506ea21f`](https://github.com/asottile/tokenize-rt/commit/0b4e506ea21f46007e9e4420fcdb8bfbafadcaa6) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 11 | [`94ef0f9d66d6`](https://github.com/asottile/tokenize-rt/commit/94ef0f9d66d681c8cf75d60cb50f37484a6dc1bb) | Merge pull request #204 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 12 | [`d5e695e54d38`](https://github.com/asottile/tokenize-rt/commit/d5e695e54d38292cbcd63f7e56c89c9025f110a9) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 13 | [`ccae6e345530`](https://github.com/asottile/tokenize-rt/commit/ccae6e3455302c9b88c030591c1f3ac8ba352faf) | Merge pull request #203 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 14 | [`64e37114c350`](https://github.com/asottile/tokenize-rt/commit/64e37114c350aae8ba3e1b4b6dc2a203b8c0c6d5) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 15 | [`606dc2211b87`](https://github.com/asottile/tokenize-rt/commit/606dc2211b872f04ef49256ee560e57516e3a1b7) | Merge pull request #202 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 16 | [`4b03e57c5c62`](https://github.com/asottile/tokenize-rt/commit/4b03e57c5c6247d83ff75e60277ee729cbc3e5c0) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 17 | [`1582bcf0259d`](https://github.com/asottile/tokenize-rt/commit/1582bcf0259d183259da1761444c6fc73fa7ad9a) | v6.2.0 | Exclude. Configuration or release metadata only (setup.cfg). |
| 18 | [`07ad77b23e3e`](https://github.com/asottile/tokenize-rt/commit/07ad77b23e3e102f92ee1a97ad4d3e283d1c398e) | Merge pull request #201 from asottile/handle-tstring-tokens | Exclude. Merge with multiple parents. |
| 19 | [`2cb9c40dd1b7`](https://github.com/asottile/tokenize-rt/commit/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0) | handle tstring tokens | Select `tokenize_rt_tstrings`. Applies the existing brace handling to template-string middle tokens. The new test pins the 3.14 input and result, with independent token utilities in the same suite. |
| 20 | [`ed9a32cc33e4`](https://github.com/asottile/tokenize-rt/commit/ed9a32cc33e454dea90a7715663453b7070bb8cd) | Merge pull request #200 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 21 | [`09148b30c80e`](https://github.com/asottile/tokenize-rt/commit/09148b30c80e5e97599a141d7a0e23d01290596b) | [pre-commit.ci] auto fixes from pre-commit.com hooks | Exclude. Configuration or release metadata only (setup.cfg). |
| 22 | [`9dd86b710108`](https://github.com/asottile/tokenize-rt/commit/9dd86b710108e783094d6e63698814c008fd0250) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 23 | [`82fd4e13b3b4`](https://github.com/asottile/tokenize-rt/commit/82fd4e13b3b4ac8f4c344f51b1b77e7937aa61ba) | Merge pull request #199 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 24 | [`d3a79470d82e`](https://github.com/asottile/tokenize-rt/commit/d3a79470d82e77d938c9e250e85c1825ae064912) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 25 | [`2052c5939a8f`](https://github.com/asottile/tokenize-rt/commit/2052c5939a8f1ddb9ccdc945a732e29f250355ec) | Merge pull request #198 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 26 | [`7debf602d6b5`](https://github.com/asottile/tokenize-rt/commit/7debf602d6b5a5fcb4aa2ae902dbf1e6fd2af3ba) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 27 | [`fce6e6745094`](https://github.com/asottile/tokenize-rt/commit/fce6e674509468d22f884c6b361dbb4564d6b7d0) | Merge pull request #197 from asottile/all-repos_autofix_all-repos-sed | Exclude. Merge with multiple parents. |
| 28 | [`c0aa27b20f98`](https://github.com/asottile/tokenize-rt/commit/c0aa27b20f98753c74e86bb83e5dfef647bd649c) | upgrade asottile/workflows | Exclude. Configuration or release metadata only (.github/workflows/main.yml). |
| 29 | [`ff8337fa67e4`](https://github.com/asottile/tokenize-rt/commit/ff8337fa67e49c27cbaf755a8f3e45d6e7488bb3) | Merge pull request #196 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 30 | [`34e4619397df`](https://github.com/asottile/tokenize-rt/commit/34e4619397df919daed01d63aa6263e9f148d94b) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 31 | [`413692b7c1ad`](https://github.com/asottile/tokenize-rt/commit/413692b7c1ad8a873caec39dd4f427d55ee538ea) | Merge pull request #195 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 32 | [`123aaf54b539`](https://github.com/asottile/tokenize-rt/commit/123aaf54b5390d2e97810ef125c613c4e1c4cfd1) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 33 | [`956ea47ad95f`](https://github.com/asottile/tokenize-rt/commit/956ea47ad95ffb642ce6c4becb2101b74dd9e345) | Merge pull request #194 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 34 | [`dfa21941abc9`](https://github.com/asottile/tokenize-rt/commit/dfa21941abc9de43c763eb437d493baf995c8299) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 35 | [`a661ff9e465f`](https://github.com/asottile/tokenize-rt/commit/a661ff9e465ff05065b2380be2991668a0fb1d76) | Merge pull request #193 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 36 | [`23619a477011`](https://github.com/asottile/tokenize-rt/commit/23619a47701177efdcaf5d53728f5991ecef0f35) | [pre-commit.ci] pre-commit autoupdate | Exclude. Configuration or release metadata only (.pre-commit-config.yaml). |
| 37 | [`532687a2c2f5`](https://github.com/asottile/tokenize-rt/commit/532687a2c2f5f6583ba4e60e6b62650360833dd8) | Merge pull request #191 from asottile/pre-commit-ci-update-config | Exclude. Merge with multiple parents. |
| 38 | [`a3a7bed0a05d`](https://github.com/asottile/tokenize-rt/commit/a3a7bed0a05d82af907cbfa14437715f7bb91b5d) | v6.1.0 | Exclude. Configuration or release metadata only (setup.cfg). |
| 39 | [`3686bae7ade9`](https://github.com/asottile/tokenize-rt/commit/3686bae7ade95e9feb14bb9eb97a4f23e06fba8d) | Merge pull request #192 from asottile/named-escapes | Exclude. Merge with multiple parents. |
| 40 | [`32e62360acc5`](https://github.com/asottile/tokenize-rt/commit/32e62360acc5f0eb311ce0197ecfd57875f90066) | handle unicode named escapes in fstring components | Select `tokenize_rt_unicode_escapes`. Introduces a named-Unicode escape aware brace transformation and exercises it directly and through f-string tokenization. |

