# Validation record

## GitHub source package — October 20, 2026

This is the source-only publication copy. The portable application's runtime binaries, model weights, local tokens, logs, working database and Power BI caches are omitted. The committed seed recreates the research database, and its CSV exports are included. The Power BI DataFolder setting is a placeholder until the local launcher configures it.

All 17 tests passed against this source copy using the portable build's Python interpreter. JavaScript syntax validation passed. The source copy was checked for the original laptop's absolute filesystem paths. The historical validation below describes the original local application and its portable build; it does not mean GitHub hosts a running service.

## Recovery and portable package — October 19, 2026

- The dashboard and model were stopped. Restarted the services and verified the dashboard health endpoint, research data and model readiness.
- Added a project-relative Windows launcher and bundled Python runtime. Startup failures are visible; the dashboard remains usable when optional AI startup fails.
- All 17 application tests passed with the bundled Python runtime. The test temporary directory was placed inside the writable workspace because this session restricts the Windows sandbox temporary folder.
- JavaScript syntax validation passed.
- Copied the application and bundled Python to a different folder containing spaces. Started that copy on a separate local port and verified the page, JavaScript, styles, research data, CSV export and a cited analytical answer. The copied Windows launcher also ran successfully.
- Verified that the launcher updates only the Power BI data-folder parameter for a moved project. The Power BI report was not rendered again during this repair.
- Browser visual/interaction testing was not performed during this repair. HTTP checks confirm that the server and application resources respond.

The complete ZIP includes the code, a consistent SQLite backup, research seed, Power BI definitions and exports, local model, llama.cpp binaries, Python runtime and licenses. It omits ephemeral logs, process IDs, generated local access tokens and Power BI caches. Extraction requires an ordinary writable Windows x64 folder. This repair does not refresh the research facts.

## Original project validation

Validated on this laptop on September 11, 2026.

- **17 automated tests passed:** database initialization, relational integrity, variant separation, missing-value handling, boundary conditions, portfolio candidates, retrieval, abstention, historical pricing, deterministic analytical routing, research audit, rollback, immutable sources, source-linked pricing, export restrictions, numeric constraints and Windows CSV line endings.
- **JavaScript syntax check passed.** No browser interaction or visual testing of the web dashboard was performed.
- **HTTP smoke checks passed:** research data, CSV download and rejection of write requests from an unapproved origin.
- **Source checks exercised live:** Apple's launch source produced a first-fetch baseline and then an unchanged result. Other manufacturers' retrieval availability has not been exhaustively tested.
- **Local model exercised live:** Qwen2.5-1.5B produced a structured memory-specification answer with valid source IDs. Analytical questions route to deterministic rules because a trial model answer confused evidence gaps with product gaps.
- **Power BI validated:** Microsoft's report-authoring CLI returned zero errors and zero warnings. All four pages were rendered in the installed Power BI Desktop and inspected. Cards showed 7 families, 9 variants, 5 brands, and 78% average field coverage. Portfolio candidates and unresolved entries matched the application rules. Tables support scrolling for long evidence text.
- Power BI uses PBIR definition version 2.0.0 and a TMSL semantic model at compatibility level 1606, matching the installed engine. The semantic model was not converted to TMDL. The generated report was repaired after an earlier version-1 definition loaded without pages; the final version was rendered successfully.

The seed has no current retail quotes and no reviewed post-baseline product changes. Empty change tables are intentional. This is a curated, expandable project, not a complete live market database. Citation validation checks source IDs, not automatic factual entailment.

The runtime is local and has no paid API dependency. Its binary and model checksums were verified against published digests. Runtime downloads and their licenses are kept in the project runtime folder.
