// Golden generator: runs the TS classifier over edge inputs. Not committed (no cross-app imports).
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const SRC = process.env.TS_SRC as string;
const c = require(`${SRC}/core/classification`);
const sha = execSync("git rev-parse HEAD", { cwd: SRC }).toString().trim();

const evidenceBodies = [
	"## Evidence\r\n\r\nWorks fine locally.\r\n## Risks\r\n\r\nhttps://x.y",
	"## Evidence\r\n\r\nTBC\r\n",
	"##\tEvidence:\nran it",
	"### Verification steps\n\n- [ ] one\n-[] two\n- [  ] three",
	"### Verification steps\n\n- [x] one",
	"#Evidence\nok then",
	"####### Evidence\nok then",
	"## Evidenced\nok then",
	"## EVIDENCE\n\nN/A.",
	"## Evidence_x\nok",
	"## Evidence\n\n ﻿TBC ",
	"## Evidence\n\n ﻿whatever　",
	"intro ## Evidence Works fine ## Next https://a.b",
	"intro\r## Testing\rsee the thing\r# Top\rmore",
	"##\nEvidence\ncontent here",
	"## Evidence\n### sub\nok\n## Next\nhttps://x",
	"## Evidence\n#hashtag\nok\n# Next\n10 tests",
	"## Evidence\n\n10\npassing",
	"## Evidence\n\n5passed",
	"## Evidence\n\n1 greenish",
	"## Evidence\n\n3 Tests",
	"## Evidence\n\nto follow",
	"## Evidence\n\nSee CI.",
	"## Evidence\n\ntbd!!",
	"## Evidence\n\nHTTP://upper",
	"## Evidence\n\n``` code",
	`## Evidence\n\n${"😀".repeat(100)}`,
	`## Evidence\n\n${"😀".repeat(101)}`,
	`## Evidence\n\n${"é".repeat(200)}`,
	`## Evidence\n\n${"é".repeat(201)}`,
	"## Evidence\n\nworks   here",
	"# Evidence\n\nfine\n## Sub\nstill fine\n# Next\nhttps://x",
	"text ## Evidence\nnot a heading",
	" ## Evidence\nindented",
	"## Evidence #\n\nfine",
	"## Evidence",
	"## Evidence   \n   \n",
	"## evidence\n\npending.",
	"## Evidence\n\n- [ ]\n- [ ] \n\n",
	"## Evidence\n\n-\t[\t]",
	"## Evidence\n\n- [ ]",
	"## Evidence\n\nOK\n\n##No space heading\nhttps://x",
	"## Evidence\n\nOK\n\n## \n",
	"## Evidence\n\nOK\n\n##   \n  more text",
	"## Evidence\n\nTesting done <b>&</b>",
];

const selfHold = [
	"PLEASE DON'T MERGE",
	"Please don’t merge",
	"x NOT READY TO MERGE y",
	"hold off merging",
	"Hold Off  merging",
	"",
];
const tickets = [
	["fuse-12a", null, null],
	["xFUSE-7 y", null, null],
	["FUSE-", "FuSe-0042", null],
	["", "", "body FUSE-9"],
	["nope", "FUSE-١٢", "fuse-3"],
];
const bots = ["Renovate-bot", "my[BOT]", "dependabot-preview[bot]", "renovate", "RENOVATE", "x-renovate", "bot", "[bot]x", "Dependabot"];
const days = [
	["2026-10-24T23:59:59Z", "2026-10-26T00:00:00Z"],
	["2026-10-25T00:00:00Z", "2026-10-26T00:00:00Z"],
	["2026-10-30T12:00:00Z", "2026-10-29T12:00:00Z"],
	["2026-12-24T09:00:00Z", "2027-01-04T09:00:00Z"],
	["2026-03-27T23:30:00+01:00", "2026-03-30T00:30:00+01:00"],
	["2025-02-27T09:00:00Z", "2025-03-03T09:00:00Z"],
];
const checks = [
	[
		{ id: 5, appId: null, name: "a", status: "completed", conclusion: "failure" },
		{ id: 3, appId: 1, name: "a", status: "completed", conclusion: "success" },
		{ id: 4, appId: null, name: "b", status: "completed", conclusion: "timed_out" },
		{ id: 6, appId: null, name: "a", status: "completed", conclusion: "success" },
		{ id: 7, appId: 2, name: "c", status: "queued", conclusion: null },
		{ id: 8, appId: 2, name: "b", status: "completed", conclusion: "action_required" },
		{ id: 2, appId: null, name: "b", status: "completed", conclusion: "success" },
	],
	[],
	[
		{ id: 1, appId: 1, name: "z", status: "completed", conclusion: "stale" },
		{ id: 2, appId: 1, name: "y", status: "completed", conclusion: "neutral" },
		{ id: 3, appId: 1, name: "x", status: "in_progress", conclusion: null },
		{ id: 1, appId: 1, name: "z", status: "completed", conclusion: "success" },
	],
];

const classifyCases = [];
const evidences = [
	{ sectionFound: false, verdict: "outstanding" },
	{ sectionFound: true, verdict: "outstanding" },
	{ sectionFound: true, verdict: "present" },
	{ sectionFound: true, verdict: "ambiguous", rawExcerpt: "x" },
];
const evNames = ["none", "pending", "present", "ambiguous"];
for (const isDraft of [false, true])
	for (const mergeableState of ["clean", "dirty", "unstable", "unknown", "has_hooks"])
		for (const [total, failing] of [[0, []], [2, []], [2, ["t", "l"]]] as const)
			for (const reviewDecision of [null, "APPROVED", "CHANGES_REQUESTED"])
				for (const [isDefaultBase, stacked] of [[true, null], [false, null], [false, { repo: "r", number: 9 }]] as const)
					for (const selfHold of [false, true])
						for (let ev = 0; ev < evidences.length; ev++) {
							const facts = {
								isDraft, mergeableState, checks: { total, success: 0, failing: [...failing] }, reviewDecision,
								isDefaultBase, stackedOnOpenPR: stacked, selfHoldPhraseDetected: selfHold, evidence: evidences[ev],
							};
							const w = c.classify(facts);
							classifyCases.push([[isDraft, mergeableState, total, failing.length, reviewDecision, isDefaultBase, stacked !== null, selfHold, evNames[ev]], [w.binary, w.holdReason, w.fiveState, w.fiveStateReason]]);
						}

const golden = {
	tsSha: sha,
	evidence: evidenceBodies.map((b) => ({ body: b, want: c.evaluateEvidence(b) })),
	selfHold: selfHold.map((b) => ({ body: b, want: c.detectSelfHold(b) })),
	tickets: tickets.map((s) => ({ sources: s.map((x) => x ?? ""), want: c.extractTicketKey(...s) })),
	bots: bots.map((l) => ({ login: l, want: c.isBotLogin(l) })),
	days: days.map(([a, b]) => ({ from: a, to: b, want: c.countWorkingDaysBetween(new Date(a), new Date(b)) })),
	checks: checks.map((runs) => ({ runs, want: c.summariseChecks(runs) })),
	classify: classifyCases,
};
const lines = Object.entries(golden).map(([k, v]) => `${JSON.stringify(k)}:${JSON.stringify(v)}`);
writeFileSync(process.argv[2], `{\n${lines.join(",\n")}\n}\n`);
console.log(`wrote ${classifyCases.length} classify cases, ts ${sha.slice(0, 7)}`);
