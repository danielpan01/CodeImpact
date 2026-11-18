# Candidate decisions

GitHub commit-list order within each recorded window. Exact heads below come from the public listing.
Exclusions were made before the first analyzer run. See [the protocol](PROTOCOL.md).

## madzak/python-json-logger, cutoff 2020-01-01 UTC

| Position | Head | Subject | Source eligibility decision |
| ---: | --- | --- | --- |
| 1 | `6d43bde05ed8d6ce6b8740aa1d7ac9eaf4a6af18` | Remove python 2.7 support from setup files | Documentation, release, packaging or CI/maintenance metadata only. |
| 2 | `a335e61779984ae283f424b4e21483cc6e1800ab` | Removed python2.7 from tox builds | Documentation, release, packaging or CI/maintenance metadata only. |
| 3 | `c0b4ba1efee39b1acd0ff898aad93a1cf447192b` | Removed unused key from test object | Test-only change. |
| 4 | `bd9e54f5274be970300fdd13940cc1a6eac603f3` | Convert format string in new test to support more < Python 3.6 | Test-only change. |
| 5 | `6083af56e5b001d90896ca70dc841ce80576b068` | Fixed version links in changelog | Documentation, release, packaging or CI/maintenance metadata only. |
| 6 | `9d5bb1f2de4fbf40ffc8591b470d70bdc667a990` | Added .env to ignore | Documentation, release, packaging or CI/maintenance metadata only. |
| 7 | `83b847aef3c68bc98d1c72af6e3f3272b63e1727` | Added test for custom object serializer. Loggers are unique for each test | Test-only change. |
| 8 | `41a763dde0bd1967f3cb31df26c1071953b82039` | Added new changelog | Documentation, release, packaging or CI/maintenance metadata only. |
| 9 | `e756b9bb8d5edd1cbfa1f975f0b0e560cf5df30a` | Renamed README for shorter extenstion | Documentation, release, packaging or CI/maintenance metadata only. |
| 10 | `9876d0411377a9a8cbab72b4207d557f9dc42526` | Merge pull request #81 from Kobla/undebianize | Merge copy, excluded by protocol. |
| 11 | `d7fe3fec5f761a0223f2624bc951fa600fad2b6b` | Merge pull request #79 from jlewis91/patch-1 | Merge copy, excluded by protocol. |
| 12 | `4006b5cd12684bd3dc4e71054b09c173278a481a` | Remove debian directory | Documentation, release, packaging or CI/maintenance metadata only. |
| 13 | `cf6a8ff14e0214c031918d2e8390e2d74f04178a` | Update README.markdown | Documentation, release, packaging or CI/maintenance metadata only. |
| 14 | `687cc52260876fd2189cbb7c5856e3fbaff65279` | Update README.markdown | Documentation, release, packaging or CI/maintenance metadata only. |
| 15 | `46826c4921a2eff492e4f9fe9044fe4ec6c38187` | Only process stack_info if we are in python3+ | Production candidate in BSD-2-Clause repository, outside the allowlist. |
| 16 | `32aa5120b2b0c32dcf61e528bbba88a0f38d5f36` | Merge pull request #75 from FlyrInc/feature/support-py3.7 | Merge copy, excluded by protocol. |
| 17 | `3a9a9369265822f7db8845a7a9f1b1d0f3b29be1` | Merge pull request #72 from ghShu/feature/ghshu/stack_info | Merge copy, excluded by protocol. |
| 18 | `88838bd9627ee0eed1e8d9429b42890f7f484c06` | feat: add support for Python 3.7 | Production candidate in BSD-2-Clause repository, outside the allowlist. |
| 19 | `c15337a3d748e5b564f668ef728c61d6f919a74e` | Consistent control of caller stack frames output | Production candidate in BSD-2-Clause repository, outside the allowlist. |
| 20 | `12ab1c30c24846cadfba214fa9cd2c00d899ab2a` | Version 0.1.10 Bump | Documentation, release, packaging or CI/maintenance metadata only. |

## pydanny/cached-property, cutoff 2020-01-01 UTC

| Position | Head | Subject | Source eligibility decision |
| ---: | --- | --- | --- |
| 1 | `218147363a4085c0826a80a83984f3d20e718aa0` | Update AUTHORS.rst | Documentation, release, packaging or CI/maintenance metadata only. |
| 2 | `fe3aae9fd892e87ca24e33086b45bc2ff9f33108` | Merge pull request #171 from stikks/docstring_cached_property | Merge copy, excluded by protocol. |
| 3 | `c97cf414254e2aed83417785b3890a4f2602ba81` | resolve cached_property docstring not showing | Docstring-only production change. |
| 4 | `b4cc28f4f08e9c4bd06b35f92ab0f5a1aa2ae9b7` | Switch back to CC token | Documentation, release, packaging or CI/maintenance metadata only. |
| 5 | `51c2086859cd97f75e38e86c8e472cb7abdb4999` | Switch to encrypted token for code climate | Documentation, release, packaging or CI/maintenance metadata only. |
| 6 | `1ff7f45d298cd38263133cd8cc2f35516cf4cf0f` | Set cc to debug mode | Documentation, release, packaging or CI/maintenance metadata only. |
| 7 | `53dcadfedb92374eec890d58d824c7437c68f05c` | Switch to more targeted CC specification | Documentation, release, packaging or CI/maintenance metadata only. |
| 8 | `cb8d53fd100e14dbb564f22bff8ec94868371e1a` | Add code climate | Documentation, release, packaging or CI/maintenance metadata only. |
| 9 | `cdea716046a82de3bc971e0f32a41412f9d657e8` | Merge branch 'master' of github.com:pydanny/cached-property | Merge copy, excluded by protocol. |
| 10 | `537a5ca047aa5240476332a26f39f949c9a15458` | Include conftest.py in PyPI tarball | Documentation, release, packaging or CI/maintenance metadata only. |
| 11 | `93949e7cb4a3cc562d452d379acb86b253454cf7` | Blacking of project | Formatting across the project. |
| 12 | `945d81d40fae050efff30e14e6c09da8ddaa40c3` | Merge pull request #121 from pydanny/pyup-update-pytest-3.8.1-to-3.8.2 | Merge copy, excluded by protocol. |
| 13 | `20ad6d3e174193b1a4df1802ec64e0c2d6052841` | Update pytest from 3.8.1 to 3.8.2 | Documentation, release, packaging or CI/maintenance metadata only. |
| 14 | `863223bab17abf6ede84a34804554c01a95f9ba0` | Merge pull request #119 from pydanny/pyup-update-wheel-0.31.1-to-0.32.0 | Merge copy, excluded by protocol. |
| 15 | `55be8e79d2e1cc1eed6d1507feea7a17c4d1700e` | Merge branch 'master' into pyup-update-wheel-0.31.1-to-0.32.0 | Merge copy, excluded by protocol. |
| 16 | `3ee256b035cd1c9fe491da22f051213e466a2495` | Merge pull request #118 from pydanny/pyup-update-twine-1.11.0-to-1.12.1 | Merge copy, excluded by protocol. |
| 17 | `82ebde2a7aae75b6fa388225ee7d58222d232b0a` | Merge pull request #116 from pydanny/pyup-update-pytest-3.7.4-to-3.8.1 | Merge copy, excluded by protocol. |
| 18 | `99f1a6eac837e8b3850d70cf9f5e8faa522c6b3f` | Update wheel from 0.31.1 to 0.32.0 | Documentation, release, packaging or CI/maintenance metadata only. |
| 19 | `8b45f2cb39900600a10106b416e62f467389a98c` | Update twine from 1.11.0 to 1.12.1 | Documentation, release, packaging or CI/maintenance metadata only. |
| 20 | `cd13b5f0f3de0c8f80af2715bdced5a884b6e23d` | Update pytest from 3.7.4 to 3.8.1 | Documentation, release, packaging or CI/maintenance metadata only. |

## python-humanize/humanize, cutoff 2020-01-01 UTC

| Position | Head | Subject | Source eligibility decision |
| ---: | --- | --- | --- |
| 1 | `9fe089a2ae88dabd17d74e24e2af42725f5b91c4` | Use built-in mock from unittest when available (Python 3.4+) | Changes test-only mock imports and packaging. |
| 2 | `a43c266c30565e025a26abc77e747d88923dac6b` | Add mo for zh_CN | Translation data only, no production Python behavior change. |
| 3 | `05cc05da3f34d55dc3feb3decaaa9f4e98491a45` | add huge number translation in zh_CN | Translation data only, no production Python behavior change. |
| 4 | `b0afc5f214bbeccac3751dc8407642e9c9a8f613` | French people use long scale naming system | Translation data only, no production Python behavior change. |
| 5 | `526baa71a654ac939c246837bbe1bc75bfd662c0` | Add italian translation | Translation data only, no production Python behavior change. |
| 6 | `56459415de8ad3da0820c2de36823f0e86271620` | Mod: Change time | Translation data only, no production Python behavior change. |
| 7 | `429a7c5f63068b656ff03be42da9f30e5398387f` | ADD: Support Vietnamese | Translation data only, no production Python behavior change. |
| 8 | `54502fcb5635ce96ae5d6409bbc715fa0a207e50` | Add bahasa indonesia translation | Translation data only, no production Python behavior change. |
| 9 | `53a9a085df88e2c5d5ab5e9f0f5b6941d543b407` | Add Finnish translation | Translation data only, no production Python behavior change. |
| 10 | `9fed723dea69bf8b837bbd97fef6e0efd5c9f3a4` | Make examples Python 3 compatible | Example-only change. |
| 11 | `3299e2e5170475882a8b8e2421931a926df5c10f` | Spelling fix | Documentation, release, packaging or CI/maintenance metadata only. |
| 12 | `d4f7f998a48581843fbbb597565d225c4a37c446` | Python 3.6 invalid escape sequence deprecation fixes | Raw strings retain regex and replacement values, addressing invalid escape warnings. |
| 13 | `86e6f226fe04626f80e6b4727ca578c469ad4a60` | Merged turkish-translation into master | Merge copy, excluded by protocol. |
| 14 | `2783e8903885f7b7cdc6fa189ecb63ef160a63d0` | Turkish translation | Translation data only, no production Python behavior change. |
| 15 | `8e5580f2b56350129450a12dda9ea00e57b9be5e` | Fixing pt_BR typos | Translation data only, no production Python behavior change. |
| 16 | `bec33540362a04b01a13ae9a639bfeae002c9c96` | fixed 0th | Translation entry and test whitespace only. |
| 17 | `019fdcd961e5f4274279d2b3eea7ecc777db256a` | added fa_IR to locales | Translation data only, no production Python behavior change. |
| 18 | `32c469bc378de22e8eabd5f9565bd7cffe7c7ae0` | Merge pull request #32 from jose1711/master | Merge copy, excluded by protocol. |
| 19 | `fc4a2303cf8dd31052a51f5c2c4ba3348aa74ce7` | Merge pull request #40 from AZLisme/master | Merge copy, excluded by protocol. |
| 20 | `292a38ad3f2b2bfa61f1c8bef74af4a838be899e` | Merge pull request #37 from magnunleno/improvements/add_pt_br_translations | Merge copy, excluded by protocol. |

## wimglenn/oyaml, cutoff 2022-01-01 UTC

| Position | Head | Subject | Source eligibility decision |
| ---: | --- | --- | --- |
| 1 | `d0195070d26bd982f1e4e604bded5510dd035cd7` | Merge pull request #24 from wimglenn/pyyaml-6 | Merge copy, excluded by protocol. |
| 2 | `7381373cec378a464e1cf4ca8b03c6cb8493469b` | PyYAML 6 | CI, metadata, documentation and tests only. |
| 3 | `45bef7ee676e30a68a122fbac9801727e0064aab` | Merge pull request #21 from wimglenn/1.0 | Merge copy, excluded by protocol. |
| 4 | `5152325dcdb68b3684c7ba745a8710df6ea40b9a` | c loaders/dumpers | Selected as `oyaml_registrations`. Register ordered mappings on Python and optional C loaders and dumpers. |
| 5 | `6350d9de586f40014296b55427ccbc1d7f47269a` | preserve contextual error when patching the loader (#18) | Selected as `oyaml_error_context`. Preserve contextual errors when constructing mappings with unhashable keys. |

## gruns/icecream, cutoff 2022-01-01 UTC

| Position | Head | Subject | Source eligibility decision |
| ---: | --- | --- | --- |
| 1 | `7bf20d4c6cbc855d3c64d6369a4e0bae753599d8` | Merge pull request #106 from jtplaarj/patch-1 | Merge copy, excluded by protocol. |
| 2 | `987a00151870a0d99c484e63aff70af658dbf2d2` | Include Bash version of ic | Documentation, release, packaging or CI/maintenance metadata only. |
| 3 | `69f203c719d00af230a7bfea5a6ddd783c9ecf2d` | Merge pull request #102 from p3r7/master | Merge copy, excluded by protocol. |
| 4 | `d5bcaa250ef9e0f59eb70ffcefd892d0ad9de39b` | Add link to Clojure/ClojureScript port | Documentation, release, packaging or CI/maintenance metadata only. |
| 5 | `fb919b77069f52ef6597b0ac74ea0939873d8298` | icecream v2.1.1 | Release version and changelog only. |
| 6 | `b6a4421e1760ae1972659c404200967af827321e` | Merge pull request #86 from chunqian/master | Merge copy, excluded by protocol. |
| 7 | `ae9f728be4adcf14f07a0e77cf76af6d99507f48` | Add C99 port of IceCream. | Documentation, release, packaging or CI/maintenance metadata only. |
| 8 | `e952dc5b36af4671867b052225863299e396d30c` | Merge pull request #82 from DominikRafacz/master | Merge copy, excluded by protocol. |
| 9 | `a361a2a9ed97bbec292452f73d170663d217cb8a` | Merge branch 'master' into master | Merge copy, excluded by protocol. |
| 10 | `8f92940de9dcb6f2133ff03c004e1d9896847bcf` | update R port link | Documentation, release, packaging or CI/maintenance metadata only. |
| 11 | `db81565707137d177fa1fcdabe5d9b1cb22b2c4e` | add missing code block type | Documentation, release, packaging or CI/maintenance metadata only. |
| 12 | `2d0144ef5f4529564b5fe7f64fc1a86e0a682074` | tweak the no source available error message to be clearer | Selected as `icecream_source_error`. Change the public message raised when source is unavailable. |
| 13 | `daa30a0672e4588ca75a7072352114fe4232869a` | spacing | Documentation, release, packaging or CI/maintenance metadata only. |
| 14 | `9bd62f3c3ae4e0502b8dc7a4ccf25de45ef0bd19` | update changelog.txt to reflect py3.9 support in setup.py | Documentation, release, packaging or CI/maintenance metadata only. |
| 15 | `52d37e51e8a0808b1d23ada9f46511a76d88a0bd` | test icecream against py3.8 and py3.9. declare icecream compatible with py3.8 and py3.9 in setup.py | Documentation, release, packaging or CI/maintenance metadata only. |
| 16 | `ffefe1b9ceb04a476a4f5ab8dbe56d93d553c3fb` | remove travis testing params for py37 that are no longer necessary | Documentation, release, packaging or CI/maintenance metadata only. |
| 17 | `90e639ac1bdd26100f2672a05a9c338cd615ce23` | Merge pull request #75 from wlingze/master | Merge copy, excluded by protocol. |
| 18 | `b0a5a94993efe3eac93e18d36c8aea351bbd57e6` | Add Lua port of IceCream. | Documentation, release, packaging or CI/maintenance metadata only. |
| 19 | `792c59009219e8d8b1f4054acbcecf02ce884034` | Merge pull request #72 from DominikRafacz/master | Merge copy, excluded by protocol. |
| 20 | `0280d0df84e66f3016cb05c0f4b98c10cd9c0432` | add R port of icecream | Documentation, release, packaging or CI/maintenance metadata only. |
| 21 | `1925fc694bebff81bc37e29997ac3a0e5fcffd24` | tweak copy | Documentation, release, packaging or CI/maintenance metadata only. |
| 22 | `cb60412d2881e405c23fe693382345bd828f4471` | tweak copy | Documentation, release, packaging or CI/maintenance metadata only. |
| 23 | `792cfdec01fccbe069fe485bad0846940251efa6` | use timestamps in the local timezone instead of less helpful UTC timestamps | Selected as `icecream_local_time`. Format source-free call timestamps in local rather than UTC time. |

## python-humanize/humanize, cutoff 2021-01-01 UTC

| Position | Head | Subject | Source eligibility decision |
| ---: | --- | --- | --- |
| 1 | `a0f03c137ab33a9b4896789b94edb95ab635f9df` | README: Move API reference up | Documentation, release, packaging or CI/maintenance metadata only. |
| 2 | `97fc008f5b3af03d09e41cfd0afc8ddbeae8f195` | Merge pull request #183 from hugovk/i18n-intcomma | Merge copy, excluded by protocol. |
| 3 | `89b73e0099646ed6d3a7826e8c276a25f4e32d93` | Merge pull request #185 from jmoiron/revert-174-toxless-pypy3 | Merge copy, excluded by protocol. |
| 4 | `9b5fa9d1e38429f7a954605ed0c420c242cb5107` | Revert "GHA: Temporarily toxlessly test PyPy" | Documentation, release, packaging or CI/maintenance metadata only. |
| 5 | `6ca44f7d14a5bac0d8af2358e97eafe105174c09` | Fix tox.ini break by tox-ini-fmt | Documentation, release, packaging or CI/maintenance metadata only. |
| 6 | `5195e30c3bad6eb1992300c4920df5fdb5d150cd` | Update pre-commit and isort | Documentation, release, packaging or CI/maintenance metadata only. |
| 7 | `cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a` | Internationalise intcomma | Selected as `humanize_intcomma_locale`. Internationalize the thousands separator used by intcomma. |
| 8 | `0cbd1ababec2dcdd71e57856f9b0cce8c4d21b51` | Merge pull request #181 from mildblimp/fix_dutch_hours_translation | Merge copy, excluded by protocol. |
| 9 | `794a1eb43079bbd21c3898ae930813cb55b81fcc` | Fix grammar mistake in the Dutch translations | Documentation, release, packaging or CI/maintenance metadata only. |
| 10 | `36bc853e382460adb0d56c8237f9813f2c2d2750` | Merge pull request #178 from graingert/apply-setup-py-upgrade | Merge copy, excluded by protocol. |
| 11 | `55b5c18b003efd27a82e330619c3774adf306ebb` | apply pre-commit autoupdate | Documentation, release, packaging or CI/maintenance metadata only. |
| 12 | `3b8505d5bfd805462303afb53252f75a2d2069a0` | add and apply setup-cfg-fmt | Documentation, release, packaging or CI/maintenance metadata only. |
| 13 | `c24f3e3b304129fbb779f88cb8eaa64a8e802772` | Merge pull request #179 from hugovk/rm-travis | Merge copy, excluded by protocol. |
| 14 | `93119f292072ea44aa83f705b0c9bdc869cec2b7` | Test 3.10-dev on all OS on GHA | Documentation, release, packaging or CI/maintenance metadata only. |
| 15 | `6d1e98966a47978572c6ce6606f19414499784fe` | Remove Travis CI | Documentation, release, packaging or CI/maintenance metadata only. |
| 16 | `b2785e9671bbbe260a82bc7689a3db0308866592` | setuptools_scm no-longer required at setup time | Documentation, release, packaging or CI/maintenance metadata only. |
| 17 | `d97c61c00375f7c70654d5901cc39e2e22d63854` | move setuptools_scm config to pyproject.toml | Documentation, release, packaging or CI/maintenance metadata only. |
| 18 | `128717639723f035cca1acc8f9c1e1a427247c34` | apply setup-py-upgrade | Documentation, release, packaging or CI/maintenance metadata only. |
| 19 | `184269e4b8f9415927e19d841891c9021235f6ce` | Merge pull request #176 from jaimcamp/readd-travis-39 | Merge copy, excluded by protocol. |
| 20 | `2bf7f5bb481238c544a0557a3319659fda6d6fc3` | Revert "Revert support for 3.9 in travis.yml" | Documentation, release, packaging or CI/maintenance metadata only. |
| 21 | `aec9dc22412a70c26286f3a9a116164dc7163d2c` | Merge pull request #174 from hugovk/toxless-pypy3 | Merge copy, excluded by protocol. |
| 22 | `eaaa1e2ca6d00847973df09cba65ef4a79cf5ae0` | Temporarily toxlessly test PyPy | Documentation, release, packaging or CI/maintenance metadata only. |
| 23 | `2d4143e0aecb719a376dc757b439fc7e41b0d773` | Add version resolver to Release Drafter | Documentation, release, packaging or CI/maintenance metadata only. |
| 24 | `c3152b6d6fe6caa050ca448fa544ec757b7809ef` | Merge pull request #171 from jaimcamp/add-python-39 | Merge copy, excluded by protocol. |
| 25 | `518bae32535ad7f78b8788c9581d947fe67e69de` | Add hacktoberfest-accepted label | Documentation, release, packaging or CI/maintenance metadata only. |
| 26 | `b0fe8eb00d4d6f9699c4def5a2c57ee8d31a93a6` | Revert support for 3.9 in travis.yml | Documentation, release, packaging or CI/maintenance metadata only. |
| 27 | `b03cd63ccccf9d712cf710641e091fadd073e758` | Add initial support py3.9 | Documentation, release, packaging or CI/maintenance metadata only. |
| 28 | `809e66b7231b7f1ad4ba5db11b2728b95655d68c` | Merge pull request #170 from eldipa/Issue-159-Represent-as-Zero-a-Too-Small-Value | Merge copy, excluded by protocol. |
| 29 | `62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742` | Represent with a zero if the delta is too small | Selected as `humanize_small_delta`. Return a zero minimum unit for a too-small precise delta. |

## pydanny/cached-property, cutoff 2021-01-01 UTC

| Position | Head | Subject | Source eligibility decision |
| ---: | --- | --- | --- |
| 1 | `409f24286e16ea3086af463edea6b80cdd62deed` | Update README.md | Documentation, release, packaging or CI/maintenance metadata only. |
| 2 | `4adb33246294a6e7370c62212028b9fb152f6157` | Fix README indentation | Documentation, release, packaging or CI/maintenance metadata only. |
| 3 | `0be6adca6f173ee7d2d0d5ec31d6b01650bac97e` | Changeover to markdown | Documentation, release, packaging or CI/maintenance metadata only. |
| 4 | `f075b4f71741f84b687327948fc3a65e4d858b2c` | Merge pull request #234 from Secrus/migrate-to-md | Merge copy, excluded by protocol. |
| 5 | `ab48d01ec5b716b7078fa1da06cbf538da9e8ff7` | Merge branch 'master' into migrate-to-md | Merge copy, excluded by protocol. |
| 6 | `6b4e990aca401ef47f7517c914b6b6cda360f9e5` | Merge in work by @secrus | Merge copy, excluded by protocol. |
| 7 | `4056dca17cfc1bbe18f43819ece998cedb994a28` | Merge in work by @secrus | Documentation, release, packaging or CI/maintenance metadata only. |
| 8 | `426aa51d08d4c43cd318872c97e8d086abe013b8` | Delete HISTORY.rst | Documentation, release, packaging or CI/maintenance metadata only. |
| 9 | `a5ecd1df8edf1379581f4da37defa7ff1b1d1172` | Add HISTORY.md | Documentation, release, packaging or CI/maintenance metadata only. |
| 10 | `deb84ce9c9a53e2ca4969b8aa47dc80795fdf43a` | Delete README.rst | Documentation, release, packaging or CI/maintenance metadata only. |
| 11 | `bad6d273bdedb28e4dc237fa2f4b06b60da1f33a` | Fix some md lint errors | Documentation, release, packaging or CI/maintenance metadata only. |
| 12 | `d10a9661ae3ae59c60e9edbaa70a639b0dd76ce5` | Add README.md | Documentation, release, packaging or CI/maintenance metadata only. |
| 13 | `831c889ecf17ec2933513d45bbff6eeb1513a6dd` | Update README.rst | Documentation, release, packaging or CI/maintenance metadata only. |
| 14 | `46b84eb8ccf7f42598e04aab0b61eb21f0c4a290` | Merge branch 'master' of github.com:pydanny/cached-property | Merge copy, excluded by protocol. |
| 15 | `f7b6d211c6d1439253ee0ac01898731219bc27e6` | Remove support for Python 2.7 | CI, history and tox support metadata only. |
| 16 | `0990bfdb9694def81227c87879b180153ffb86ea` | Update AUTHORS.md | Documentation, release, packaging or CI/maintenance metadata only. |
| 17 | `63c1f67a492d6fc37ea3b72ae6f88e7b87d0bd8a` | Merge pull request #233 from Secrus/migrate-to-md | Merge copy, excluded by protocol. |
| 18 | `9a1b19a8247c3f8ea7adcdfc2e1404f9937a91e0` | Delete CONTRIBUTIONG.rst | Documentation, release, packaging or CI/maintenance metadata only. |
| 19 | `9cb55ecb394a7e82ebb97a9099b7e87766eadddf` | Cleanup of RST | Documentation, release, packaging or CI/maintenance metadata only. |
| 20 | `08a02298bdfd6e8203df7c8620a651be7d03a89f` | Add CONTRIBUTING.md | Documentation, release, packaging or CI/maintenance metadata only. |

