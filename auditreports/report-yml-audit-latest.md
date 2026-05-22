# Secure GitHub Token / YAML Audit Report

```text
Generated:             2026-05-22 15:30:57 UTC
Owner:                 felipealfonsog
Private repos scanned: no
Repos scanned:         30
Files scanned:         1221
Files skipped:         6
Findings:              49
High risk:             8
Secret redaction:      enabled
```

## Status

```text
STATUS: REVIEW REQUIRED
```

## High-Risk Findings

| Repo | Visibility | File | Line | Type | Redacted snippet |
|---|---|---|---:|---|---|
| `SpendWisePy` | `public` | `SQL/SpendWisePy-Arch.sql` | `10` | `small token column` | ``description` varchar(255) DEFAULT NULL,` |
| `SpendWisePy` | `public` | `SQL/SpendWisePy-Arch.sql` | `12` | `small token column` | ``name` varchar(255) NOT NULL,` |
| `SpendWisePy` | `public` | `SQL/SpendWisePy.sql` | `32` | `small token column` | ``description` varchar(255) DEFAULT NULL,` |
| `SpendWisePy` | `public` | `SQL/SpendWisePy.sql` | `34` | `small token column` | ``name` varchar(255) NOT NULL,` |
| `SpendWisePy` | `public` | `models/database.py` | `77` | `small token column` | `name VARCHAR(255) NOT NULL,` |
| `SpendWisePy` | `public` | `models/database.py` | `79` | `small token column` | `description VARCHAR(255),` |
| `rtl-88x2bu` | `public` | `hal/phydm/phydm_debug.c` | `5802` | `token length check` | `if (strlen(token) <= MAX_ARGV)` |
| `RescuePaw` | `public` | `www/www/js/jquery.mobile-1.4.0-rc.1.min.js` | `2` | `token substring` | `!function(a,b,c){"function"==typeof define&&define.amd?define(["jquery"],function(d){return c(d,a,b),d.mobile}):c(a.jQue` |

## All Findings

| Repo | Visibility | File | Line | Type | Redacted snippet |
|---|---|---|---:|---|---|
| `felipealfonsog` | `public` | `.github/workflows/deploy-wiki.yml` | `30` | `GITHUB_TOKEN usage` | `github_token: ${{ secrets.GITHUB_TOKEN }}` |
| `felipealfonsog` | `public` | `.github/workflows/langstats.yml` | `18` | `GITHUB_TOKEN usage` | `TOKEN: ${{ secrets.GITHUB_TOKEN }}` |
| `felipealfonsog` | `public` | `.github/workflows/report-yml-audit.yml` | `75` | `GITHUB_TOKEN usage` | `("GITHUB_TOKEN usage", re.compile(r"\bGITHUB_TOKEN\b")),` |
| `felipealfonsog` | `public` | `.github/workflows/report-yml-audit.yml` | `80` | `ghs token prefix assumption` | `("startswith ghs", re.compile(r"startswith\s*\(\s*['\"]ghs_", re.I)),` |
| `felipealfonsog` | `public` | `.github/workflows/report-yml-audit.yml` | `81` | `ghs token prefix assumption` | `("startsWith ghs", re.compile(r"startsWith\s*\(\s*['\"]ghs_", re.I)),` |
| `felipealfonsog` | `public` | `.github/workflows/report-yml-audit.yml` | `82` | `regex token logic` | `("regex token logic", re.compile(r"re\.match\|RegExp\|regexp\|regex", re.I)),` |
| `felipealfonsog` | `public` | `.github/workflows/report-yml-audit.yml` | `89` | `ghs token prefix assumption` | `re.compile(r"ghs_[A-Za-z0-9._-]{20,}"),` |
| `felipealfonsog` | `public` | `.github/workflows/report-yml-audit.yml` | `289` | `GITHUB_TOKEN usage` | `md.append("- `GITHUB_TOKEN` usage alone is not an error.")` |
| `felipealfonsog` | `public` | `.github/workflows/report-yml-audit.yml` | `290` | `regex token logic` | `md.append("- Risk appears when code assumes fixed token length, prefix, regex shape, truncation, or small storage.")` |
| `felipealfonsog` | `public` | `README.md` | `2323` | `regex token logic` | `<img src="https://skillicons.dev/icons?i=ableton,activitypub,actix,adonis,ae,aiscript,alpinejs,anaconda,androidstudio,an` |
| `felipealfonsog` | `public` | `_.github-bk/workflows/deploy-wiki.yml` | `30` | `GITHUB_TOKEN usage` | `github_token: ${{ secrets.GITHUB_TOKEN }}` |
| `felipealfonsog` | `public` | `_.github-bk/workflows/langstats.yml` | `18` | `GITHUB_TOKEN usage` | `TOKEN: ${{ secrets.GITHUB_TOKEN }}` |
| `felipealfonsog` | `public` | `backups/backup-manual-latest_ring1main_slot-main.md` | `2328` | `regex token logic` | `<img src="https://skillicons.dev/icons?i=ableton,activitypub,actix,adonis,ae,aiscript,alpinejs,anaconda,androidstudio,an` |
| `felipealfonsog` | `public` | `backups/backup-ring1d_slot0-2026-05-22_0040Z.md` | `2247` | `regex token logic` | `<img src="https://skillicons.dev/icons?i=ableton,activitypub,actix,adonis,ae,aiscript,alpinejs,anaconda,androidstudio,an` |
| `felipealfonsog` | `public` | `backups/backup-ring1d_slot1-2026-05-22_0714Z.md` | `2335` | `regex token logic` | `<img src="https://skillicons.dev/icons?i=ableton,activitypub,actix,adonis,ae,aiscript,alpinejs,anaconda,androidstudio,an` |
| `felipealfonsog` | `public` | `backups/backup-ring1d_slot2-2026-05-22_1249Z.md` | `2335` | `regex token logic` | `<img src="https://skillicons.dev/icons?i=ableton,activitypub,actix,adonis,ae,aiscript,alpinejs,anaconda,androidstudio,an` |
| `felipealfonsog` | `public` | `backups/backup-ring1d_slot3-2026-05-21_1838Z.md` | `2247` | `regex token logic` | `<img src="https://skillicons.dev/icons?i=ableton,activitypub,actix,adonis,ae,aiscript,alpinejs,anaconda,androidstudio,an` |
| `felipealfonsog` | `public` | `config/exclusions.json` | `18` | `regex token logic` | `"exclude_regex": [` |
| `felipealfonsog` | `public` | `generate-stats.js` | `116` | `regex token logic` | `new RegExp(`${start}[\\s\\S]*?${end}`),` |
| `felipealfonsog` | `public` | `scripts/update_projects.backup.v1.py` | `78` | `regex token logic` | `"exclude_regex": data.get("exclude_regex", []) or [],` |
| `felipealfonsog` | `public` | `scripts/update_projects.backup.v1.py` | `97` | `regex token logic` | `for rx in rules.get("exclude_regex", []):` |
| `felipealfonsog` | `public` | `scripts/update_projects.py` | `83` | `regex token logic` | `"exclude_regex": data.get("exclude_regex", []) or [],` |
| `felipealfonsog` | `public` | `scripts/update_projects.py` | `102` | `regex token logic` | `for rx in rules.get("exclude_regex", []):` |
| `AegisIntel` | `public` | `aegisintel/utils/validators.py` | `6` | `regex token logic` | `DOMAIN_REGEX = re.compile(` |
| `AegisIntel` | `public` | `aegisintel/utils/validators.py` | `10` | `regex token logic` | `HASH_REGEX = re.compile(r"^[A-Fa-f0-9]{32}$\|^[A-Fa-f0-9]{40}$\|^[A-Fa-f0-9]{64}$")` |
| `AegisIntel` | `public` | `aegisintel/utils/validators.py` | `22` | `regex token logic` | `return bool(DOMAIN_REGEX.fullmatch(value.strip()))` |
| `AegisIntel` | `public` | `aegisintel/utils/validators.py` | `26` | `regex token logic` | `return bool(HASH_REGEX.fullmatch(value.strip()))` |
| `camviewer` | `public` | `package-lock.json` | `130` | `regex token logic` | `"to-regex-range": "^5.0.1"` |
| `camviewer` | `public` | `package-lock.json` | `358` | `regex token logic` | `"node_modules/to-regex-range": {` |
| `camviewer` | `public` | `package-lock.json` | `360` | `regex token logic` | `"resolved": "https://registry.npmjs.org/to-regex-range/-/to-regex-range-5.0.1.tgz",` |
| `SpendWisePy` | `public` | `SQL/SpendWisePy-Arch.sql` | `10` | `small token column` | ``description` varchar(255) DEFAULT NULL,` |
| `SpendWisePy` | `public` | `SQL/SpendWisePy-Arch.sql` | `12` | `small token column` | ``name` varchar(255) NOT NULL,` |
| `SpendWisePy` | `public` | `SQL/SpendWisePy.sql` | `32` | `small token column` | ``description` varchar(255) DEFAULT NULL,` |
| `SpendWisePy` | `public` | `SQL/SpendWisePy.sql` | `34` | `small token column` | ``name` varchar(255) NOT NULL,` |
| `SpendWisePy` | `public` | `models/database.py` | `77` | `small token column` | `name VARCHAR(255) NOT NULL,` |
| `SpendWisePy` | `public` | `models/database.py` | `79` | `small token column` | `description VARCHAR(255),` |
| `rtl-88x2bu` | `public` | `hal/phydm/phydm_debug.c` | `5802` | `token length check` | `if (strlen(token) <= MAX_ARGV)` |
| `RescuePaw` | `public` | `www/www/js/jquery-2.0.3.min.js` | `4` | `regex token logic` | `(function(e,undefined){var t,n,r=typeof undefined,i=e.location,o=e.document,s=o.documentElement,a=e.jQuery,u=e.$,l={},c=` |
| `RescuePaw` | `public` | `www/www/js/jquery-2.0.3.min.js` | `5` | `regex token logic` | `};"inprogress"===i&&(i=n.shift(),r--),i&&("fx"===t&&n.unshift("inprogress"),delete o.stop,i.call(e,s,o)),!r&&o&&o.empty.` |
| `RescuePaw` | `public` | `www/www/js/jquery-2.0.3.min.js` | `6` | `regex token logic` | `},delegate:function(e,t,n,r){return this.on(t,e,n,r)},undelegate:function(e,t,n){return 1===arguments.length?this.off(e,` |
| `RescuePaw` | `public` | `www/www/js/jquery.mobile-1.3.2.min.js` | `3` | `regex token logic` | `}if(d.which&&1!==d.which)return!1;var j,k=d.target;d.originalEvent,c.bind("vmouseup",g).bind("vclick",i),f.bind("vmousec` |
| `RescuePaw` | `public` | `www/www/js/jquery.mobile-1.3.2.min.js` | `5` | `regex token logic` | `},_setDisabled:function(a){return this.element.attr("disabled",a),this.button.attr("aria-disabled",a),this._setOption("d` |
| `RescuePaw` | `public` | `www/www/js/jquery.mobile-1.4.0-rc.1.min.js` | `2` | `token substring` | `!function(a,b,c){"function"==typeof define&&define.amd?define(["jquery"],function(d){return c(d,a,b),d.mobile}):c(a.jQue` |
| `RescuePaw` | `public` | `www/www/js/jquery.mobile-1.4.0-rc.1.min.js` | `3` | `regex token logic` | `},popstate:function(b){var c,f;if(a.event.special.navigate.isPushStateEnabled())return this.preventHashAssignPopState?(t` |
| `RescuePaw` | `public` | `www/www/js/jquery.ui.map.full.min.js` | `2` | `regex token logic` | `eval(function(p,a,c,k,e,d){e=function(c){return(c<a?"":e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toStrin` |
| `RescuePaw` | `public` | `www/www/spec/lib/jasmine-1.2.0/jasmine.js` | `1245` | `regex token logic` | `* Matcher that compares the actual to the expected using a regular expression.  Constructs a RegExp, so takes` |
| `RescuePaw` | `public` | `www/www/spec/lib/jasmine-1.2.0/jasmine.js` | `1251` | `regex token logic` | `return new RegExp(expected).test(this.actual);` |
| `RescuePaw` | `public` | `www/www/spec/lib/jasmine-1.2.0/jasmine.js` | `1260` | `regex token logic` | `return !(new RegExp(expected).test(this.actual));` |
| `RescuePaw` | `public` | `www/www/spec/lib/jasmine-1.2.0/jasmine.js` | `1861` | `regex token logic` | `} else if (value instanceof RegExp) {` |

## Security Notes

- Report snippets are redacted before being written.
- `GITHUB_TOKEN` usage alone is not an error.
- Risk appears when code assumes fixed token length, prefix, regex shape, truncation, or small storage.
- GitHub tokens should be treated as opaque strings.
- For maximum safety, keep `AUDIT_INCLUDE_PRIVATE_REPOS` as `false` unless you explicitly want private repo names and paths in the report.
