# PROVENANCE: frozen analysis for "Can rat cortical cultures predict what comes next, unpredictable or learned?"

This repository holds the code and saved outputs of the pre-registered re-analysis of DANDI 001611, taken from the analysis repository at tag `cp4` (one line-ending normalization noted below). This file records what was frozen before the held-out run, and how each file here can be checked against that freeze without access to the analysis repository.

## 1. The freeze

| Item | Value |
|---|---|
| Tag | `prereg-v1` (annotated) |
| Tag object | `5133487411696830dd6ad5940848a7e2903005d5` |
| Tagged commit | `71e50189bd366943028b2b88b6892a7c3af26b85` |
| Tree of that commit | `993efd486d1f4d80e63f37cf703519bcdb841971` |
| Tag time | 2026-10-28 16:19:20 −07:00 (PDT), as recorded by the local machine's clock; tagger and commit time are identical |
| OSF registration | osf.io/nxsph (project osf.io/fk9dn), Open-Ended Registration, created 2026-10-28 19:51 PDT, embargoed; the registration summary records the SHA-256 and git blob ID of the three registered files (section 3) |
| Held-out run | started 2026-10-28 19:06:44 PDT at commit `fe7a9d47b40c2fe51188c687b2f0425b64e6c049`; the run guard recorded `changed_since_tag = []` and `uncommitted_in_frozen = []`, i.e. every frozen file equalled its `prereg-v1` version at run time (`results/D/heldout_primary/summary.json`, `provenance`) |
| Snapshot taken | analysis repository tag `cp4`, 2026-10-29 (held-out run of 2026-10-28); public repository created 2026-11-04 |

## 2. How to check

- **Against the run:** `python check_hashes.py` (in this folder; standard library only) recomputes the SHA-256 of every file in section 3 and compares it with the values the confirmatory run wrote into `summary.json`. Expected last line: `all frozen files match`.
- **Against the tag:** the git blob ID of a file is `git hash-object <file>` (no repository needed). Section 3 lists the blob ID each file has in the `prereg-v1` tree; a match means the bytes are identical to the frozen version.
- **Against OSF:** the three registered files carry the same SHA-256 and blob ID in the OSF registration summary (column "OSF").
- **Registered inputs:** `docs/preregistration_values.json` fixes `SPLIT_SHA256` and `LOCK_SHA256`; `data/manifests/split.csv` and `environment.lock.yml` here hash to those values (rows below).

## 3. Files frozen at the tag

SHA-256 as recorded by the run (`summary.json` → `provenance.file_sha256`, `split_sha256`, `gates_sha256`); blob ID from `git ls-tree -r prereg-v1`; "identical" means `git hash-object` of the file in this repository equals that blob ID; "OSF" marks the three files whose hashes are in the OSF registration.

| Path | SHA-256 (recorded by the run) | Blob ID at `prereg-v1` | Identical to tag | OSF |
|---|---|---|---|---|
| `src/organoid_anticipation/__init__.py` | `a8eda9f8088f3da157b85ed63d841edd0c2f6656d585171493824ace234d3591` | `507054838f88af895e7406d060d329a7d5a5f950` | yes |  |
| `src/organoid_anticipation/audit/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/decode/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/decode/blocked_cv.py` | `f321ec22d1732ba9ae049ef2820ff46e492b3c4b805b6e585f39accf6258f503` | `d713eeaec46fb60b3e045e6dac9797aade1d9f11` | yes |  |
| `src/organoid_anticipation/events/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/events/volleys.py` | `9cf310dc2abcfe2ac194baa3a031ef985b53112d765d7ea9eb38b99133420783` | `6d8f0e36c7143a541e1dd7ffb52171ffa16137ab` | yes |  |
| `src/organoid_anticipation/io/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/io/d001611.py` | `e0202a29606b6d97e7013056f4a8077c57546e8c0e19956d04158e9a9b948831` | `5f1ccb491607ffa18734778c79b2e6b20a725ddb` | yes |  |
| `src/organoid_anticipation/io/d001611_index.py` | `4ce9ad952567a8e1b44137b2943a1c509997290c12ad6e4ac49e62eb5448364f` | `a3429348d978bcffdc00464ae33e077ad07eb56b` | yes |  |
| `src/organoid_anticipation/io/isomura.py` | `746850be3742eef2fce516a5243a388590693deb89514db4fbceeb27319662f7` | `3cf81be809a499b17133a7c13639192c34031284` | yes |  |
| `src/organoid_anticipation/models/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/models/pool.R` | `2743ce33d8b733a034fbdc2a5cb5c987e3edf14bedb0e06ad67e759381d3480f` | `cca2411c4bedb30442583d1799aaa3e37178132d` | yes |  |
| `src/organoid_anticipation/models/pooling.py` | `0386e4c9aa9d345e6346c6d462759eea90d36233ac17a80effe1c2568737f48b` | `e4f2823eb28a0ff6ee4064223bdd5ffcee5f7dd6` | yes |  |
| `src/organoid_anticipation/nulls/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/nulls/labels.py` | `eaf0a434559d72f9643464981143d4dfc5aee7ec050a70aa93b0ec3d7fa264de` | `f8a29bdd1001d722abb295f2853db08e3080935d` | yes |  |
| `src/organoid_anticipation/pipeline/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/pipeline/analysis.py` | `7ce788dbdb711155deec4babc88e754637c80be0166fd2fd1a9b3d767cf51ba5` | `dac3818bb42807a725243dee2ec6bc7eeeae95ae` | yes |  |
| `src/organoid_anticipation/pipeline/experiment.py` | `ca2ae49450c55eadeac994d0df39e3c729e9dd5d9cbf990fd6e59287ff80ea1f` | `5da29927675beeb9cf4eb6d130cf84cb32477cf6` | yes |  |
| `src/organoid_anticipation/plotting/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/spont/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/synth/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `src/organoid_anticipation/synth/inject.py` | `a5a3a789bdbb938f0fe81561751525e0b59c555febbe25c9db13001bafd7a7e2` | `04dd7781d6bdbdd1dfd0d363d3613f4681ef5313` | yes |  |
| `src/organoid_anticipation/tests_paper/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | yes |  |
| `scripts/D_confirmatory.py` | `3862e03316995850f9a37d510d668307b7f3c1369912b1ac1761f84a443da0e7` | `bbfd17e04c2b1495e91778f61410ecb5757231ec` | yes |  |
| `scripts/B1_build_experiments.py` | `bd7ed26a67de8df4c9d9a0a9a07959621a493ee5441fc973a801cc6bc9ab68bd` | `c29e95147a6977fc3a8b56faea67a97a198be8d4` | yes |  |
| `docs/preregistration.md` | `becf768214619cdd0daad52b0b2df9f2cc382f44bc34f0c038b234ab5fc33f25` | `091b00122ee347b294493c2d7379e2529afd4a0c` | yes | yes |
| `docs/preregistration_values.json` | `711c54da2a2e0a18632a01d70e3de84a54267a39ada24a566c8ec962bf74313a` | `0a7d8b385ceb50e69bdb1ab7667272159c2ffeac` | yes | yes |
| `docs/analysis_spec.md` | `737ba4d3ed7602efe2bf511d37038536c7196dc04ce593e2e95e6fcf2611564d` | `fd200ea88f725da615d81a12bb89843de165f2dc` | yes | yes |
| `environment.lock.yml` | `c8364adf47b6bfa0de8980b30288f2a85e51909ecb2f1ac54f4c149c2483d3a2` | `d79abd2a4e6c2f6c81298c10c0ea5fe2e36ef397` | yes |  |
| `data/manifests/split.csv` | `2d792f9ebc1fdf3a82f83c709a0c40ef6417c357dc5799fe40100715b9e65ef9` | — | not in the tag tree (`data/` is untracked); SHA-256 matches the run record: yes; matches `SPLIT_SHA256` in preregistration_values.json: yes |  |
| `results/B/B7/gates.json` | `33764aa12537242e3ffbd17bce605b1a4c0664337c1b9d749e8c26860f0b6a27` | `9b507a5875e67c4108fe570624986915eea76a1a` | yes |  |

31 of 31 frozen files are byte-identical to their recorded hashes (checked when this file was last updated, 2026-11-09).

## 4. Every other file in this repository

Not part of the frozen set. "identical" means the file is byte-identical to its `prereg-v1` version; "post-freeze" means the file was produced or edited after the tag (held-out outputs, brief, manifests, snapshot READMEs).

| Path | Status | Blob ID (this folder) |
|---|---|---|
| `.gitattributes` | added at the public release (not in the tag tree); disables line-ending conversion so the frozen files stay byte-identical | `fa1385d99a319b43c06f5309d1aae9fdd3adea46` |
| `.gitignore` | post-freeze edit (differs from the tag version) | `01a24d58d920384b39f1776a009b460bfb3488cd` |
| `CITATION.cff` | added at the public release (not in the tag tree) | `da30636414b37d6ce53c544dedb2c12e9c2f6b25` |
| `LICENSE` | added at the public release (not in the tag tree) | `f288702d2fa16d3cdf0035b15a9fcbc552cd88e7` |
| `README.md` | post-freeze edit (differs from the tag version) | `dc313e01039c794d031da47c0692461f6a911e0c` |
| `VERIFICATION.md` | post-freeze (not in the tag tree) | `08d3d8f33ee3fc82bbe7356a1c07b709c9f366e8` |
| `brief/a_timeline.csv` | post-freeze (not in the tag tree) | `79fff036930bd11a555b4ce8cba52ea57d424d36` |
| `brief/a_timeline.png` | post-freeze (not in the tag tree) | `180e68a15b896f77119391b6d7dd6d7c40a8722f` |
| `brief/at_a_glance.pdf` | post-freeze (not in the tag tree) | `3350e00849801b09a83a945b6dfb63aca85731d4` |
| `brief/b_q1_forest.csv` | post-freeze (not in the tag tree) | `f13ef945a47db64ff53a31df369bc3c9af1dfc81` |
| `brief/b_q1_forest.png` | post-freeze (not in the tag tree) | `03728cb43e031cd43194dc91a473dfe112b8d693` |
| `brief/c_q2_forest.csv` | post-freeze (not in the tag tree) | `0228d8b975f23b9d56e27c98451457405364004b` |
| `brief/c_q2_forest.png` | post-freeze (not in the tag tree) | `8ef9cf471b6567c54b2d176ce7d07af973a7384b` |
| `brief/d_detection_vs_effect.csv` | post-freeze (not in the tag tree) | `7714ee5e5cf92e5b96f1372f6a62c0771f4a8d26` |
| `brief/d_detection_vs_effect.png` | post-freeze (not in the tag tree) | `fe35c948531769d08f96198e5d74c7598b3c94e7` |
| `brief/paragraphs.txt` | post-freeze (not in the tag tree) | `c9844ecbfc6fdeab40bd7994e99b687911e522a5` |
| `brief/pdf_text.txt` | post-freeze (not in the tag tree) | `8f7e4bcd7264d29d2c6130c101faba488363b05b` |
| `brief/results.json` | post-freeze (not in the tag tree) | `ddacff24fae031910ff3ee3f969139a812592fe2` |
| `check_hashes.py` | post-freeze (not in the tag tree) | `63d25f2472ebf1071f1bd46603551320367385a1` |
| `data/manifests/d001611.assets.tsv` | post-freeze (not in the tag tree); CRLF line endings converted to LF for this repository (content otherwise as at tag `cp4`; not in the hash-checked set) | `7c9d79217087dc76d76e47788742cfa774caaa2f` |
| `data/manifests/d001611_index.csv` | post-freeze (not in the tag tree) | `2715979acb66ff0b00cd95e511f8c922e02d0cf4` |
| `data/manifests/provenance/d001611_bulk.csv` | post-freeze (not in the tag tree) | `7e60bf632431dba809b0374ff0bde6e5d3ad1ef4` |
| `data/manifests/provenance.csv` | post-freeze (not in the tag tree) | `3b797c797b4ca082fa31dd7dd25acf13b7cd6db8` |
| `environment.yml` | identical to the tag | `c302d96e92a3762932c002bb9f8c062847c49df8` |
| `posthoc/README.md` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `ce327ee9402807537e74311de5c288254b0a9774` |
| `posthoc/output/depression_by_experiment.csv` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `84fa1d499e1657200e8fa671fabac0fde6883f83` |
| `posthoc/output/pretask_by_culture.csv` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `0733d0df135ee0ed137fafce323be36bceb86511` |
| `posthoc/output/recovery_by_culture.csv` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `ae99663c098032650510afa00331f47fd3db24f3` |
| `posthoc/output/summary.json` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `e3ab052433dd396a4bdf616f27b23c965fdf9f93` |
| `posthoc/pretask_cadence_audit.py` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `11a5fd880d2e2ba668603b41225bc6b215dfca5d` |
| `posthoc/response_recovery_depression.py` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `6c1ad4dacc69aa04af9e542adf02ff747eec5a93` |
| `posthoc/summarize_controls.py` | post-freeze (not in the tag tree); post-hoc descriptive control, not part of the registered pipeline | `f4060430d429a5f903a660d2b6a982454471780f` |
| `pyproject.toml` | identical to the tag | `7613e43108f62d0390076088b7ecd067bb742fac` |
| `results/B/B1/div_check.csv` | identical to the tag | `bfd23a721fbee96502c4a52ec60bfeb298d27500` |
| `results/B/B1/units.csv` | identical to the tag | `9c5b83bd7ade55e5a79a16c998e434118578e037` |
| `results/B/B2/README.md` | identical to the tag | `7c5a7d38c135684098cbcd8e53bd7ec3ba0227f4` |
| `results/B/B2/q1_homog_mde80.csv` | identical to the tag | `f2d2c404c62e6d7b7959f725765c4a1b74ddc24b` |
| `results/B/B2/q1_homog_power.csv` | identical to the tag | `f9622f432f55b9a54b3497e6f4e5b89124c4d35d` |
| `results/B/B2/q1_mde80.csv` | identical to the tag | `224f7139798d1e11363e3e3b1bb4d9b1e4238acd` |
| `results/B/B2/q1_power.csv` | identical to the tag | `65a48ee560483a7414ec3398408d0786d0cf9be5` |
| `results/B/B2/q1_unit_sensitivity.csv` | identical to the tag | `eabb60196d7a08f6841b84a38fee656cb7daa21e` |
| `results/B/B2/q2_homog_mde80.csv` | identical to the tag | `fe2ecb2588cae2814ef6c7a52651b4b2d098c8b9` |
| `results/B/B2/q2_homog_power.csv` | identical to the tag | `a2f35b5bd1c18afbd57a9da1b34e2bf987d02de8` |
| `results/B/B2/q2_mde80.csv` | identical to the tag | `6d6972af4e63c16fb1b06d54fca9025c81952154` |
| `results/B/B2/q2_power.csv` | identical to the tag | `368fd1e454689e12806f7e2c8f263c3e9a0b773a` |
| `results/B/B2/q2_unit_sensitivity.csv` | identical to the tag | `45ead2ac990185b02446e4a9f508f3c9b82951fb` |
| `results/B/B7/README.md` | identical to the tag | `f1aa417b8437ef462e84dcb0693ac64edd2990f5` |
| `results/B/B7/gate_a_pooled.csv` | identical to the tag | `e57d6caa556cf760dfae6fad45f1726d26c69d9a` |
| `results/B/B7/gate_a_units.csv` | identical to the tag | `51ddfe4803262ee336604948922e8ee73d509cff` |
| `results/B/B7/gate_b_global.csv` | identical to the tag | `8d4a331ad04cf59be6fdf93658f44f0e206fd74d` |
| `results/B/B7/gate_b_tests.csv` | identical to the tag | `fee15673b1b293c214c317f2b23407bc79d0ec80` |
| `results/D/README.md` | post-freeze edit (differs from the tag version) | `030dee5d042c7137727bf8af3bf06bf7a93abcad` |
| `results/D/dev_permuted_primary/forest_q1.csv` | identical to the tag | `53b1997a2e0c8bcb6384f38b8d0e11962663d2af` |
| `results/D/dev_permuted_primary/forest_q1.png` | identical to the tag | `3a9d87c38a2374d6c81e7cd6ccfc474c42d12eb0` |
| `results/D/dev_permuted_primary/forest_q2.csv` | identical to the tag | `610e273a9e86087d4b0d1893cfd1dcb12094e603` |
| `results/D/dev_permuted_primary/forest_q2.png` | identical to the tag | `a153b7bab4b7390d0404eba1568c94931caaed38` |
| `results/D/dev_permuted_primary/nulls.npz` | identical to the tag | `c769172318f352aaf9df9e8013bc6509fae24c1b` |
| `results/D/dev_permuted_primary/summary.json` | identical to the tag | `d21d6ce51b397d7a762636843020e5ae49f37c75` |
| `results/D/dev_permuted_primary/units.csv` | identical to the tag | `a3c80776382b809b29cffdf9b65feb4704649762` |
| `results/D/heldout_L360/forest_q1.csv` | post-freeze (not in the tag tree) | `e16c7e255f25b399c8826125a2df8ab4998e7ba6` |
| `results/D/heldout_L360/forest_q1.png` | post-freeze (not in the tag tree) | `555d2a9cfc2254af8558490a3acf9603f048150f` |
| `results/D/heldout_L360/forest_q2.csv` | post-freeze (not in the tag tree) | `e9fffcaad55b111bee3ccfbbfb01ddd4e55c330c` |
| `results/D/heldout_L360/forest_q2.png` | post-freeze (not in the tag tree) | `19a56e3b3dfa29479d4b3a10457018022b1bd963` |
| `results/D/heldout_L360/nulls.npz` | post-freeze (not in the tag tree) | `11d1aabcd9eda2a948907295590d38286f6aa96f` |
| `results/D/heldout_L360/run.log` | post-freeze (not in the tag tree) | `47c88bab7ac21215e7d2f502382b3ab321a3bb93` |
| `results/D/heldout_L360/summary.json` | post-freeze (not in the tag tree) | `7da83d8bd29ce762fb9da5f339d7520099b576da` |
| `results/D/heldout_L360/units.csv` | post-freeze (not in the tag tree) | `07071ee4853863553db1b31a512ef47cbf3f95a6` |
| `results/D/heldout_primary/forest_q1.csv` | post-freeze (not in the tag tree) | `3ab0863d64abe794be03677f4d36dcec4ba5a41a` |
| `results/D/heldout_primary/forest_q1.png` | post-freeze (not in the tag tree) | `70dd8137a47105c9e5086505dd5bd83ef5378959` |
| `results/D/heldout_primary/forest_q2.csv` | post-freeze (not in the tag tree) | `b1ae2283c2568b1ac276031c9a5ec276331e5139` |
| `results/D/heldout_primary/forest_q2.png` | post-freeze (not in the tag tree) | `d0937ff104046e26ca1de51b855528c2b401ee5c` |
| `results/D/heldout_primary/nulls.npz` | post-freeze (not in the tag tree) | `8ea1ea7c1930fe33734f3f277e3b7ce13d9025e1` |
| `results/D/heldout_primary/run.log` | post-freeze (not in the tag tree) | `c43a2ba1ccd2d6a6f31178fff1480d0d3eb46c7a` |
| `results/D/heldout_primary/summary.json` | post-freeze (not in the tag tree) | `4b920d881ee88c76ab4db2bf37e740d6627c3b50` |
| `results/D/heldout_primary/units.csv` | post-freeze (not in the tag tree) | `b407996928149921d08b7c1091a526c996448452` |
| `results.json` | post-freeze (not in the tag tree) | `ddacff24fae031910ff3ee3f969139a812592fe2` |
| `scripts/A2_split.py` | identical to the tag | `fbd2b044ecaa5d073d353f21a6c3f716349e57c5` |
| `scripts/B0_download_001611.py` | identical to the tag | `90a32aebdae8cfcca4fab56151b90c6062bde751` |
| `tests/test_cv_nulls.py` | identical to the tag | `c8cb02906907040f5946cb8555dc7e7871065d36` |
| `tests/test_d001611_reader.py` | identical to the tag | `f8a1864a5081545ce80dfa3d31b572acd4760b9a` |
| `tests/test_pipeline.py` | identical to the tag | `03a68aab4ec5b2940504958496f536787da13a74` |
| `tests/test_seed.py` | identical to the tag | `e97251001505dea920336271467bdd016a998800` |
| `tools/make_brief.py` | post-freeze (not in the tag tree) | `f2c3600a80754f7ba1498b5f68f8e39ee2504b91` |
| `tools/verify_earlier_findings.py` | post-freeze (not in the tag tree) | `20f6c30251d463cee1a859c5d0ae93b6a03d11b9` |
| `tools/verify_earlier_findings_expected.txt` | post-freeze (not in the tag tree) | `dc1c990c11136b5c0f6966ebe4c1235c20a9c3b1` |
| `tools/verify_earlier_findings_expected_values.json` | post-freeze (not in the tag tree) | `a5cdf1b808374e1ec11fd524a81c79b642117c93` |

## 5. Note

The full git history behind this tag is kept private because it contains third-party correspondence drafts; the tag, commit and files can be shown to an editor on request.
