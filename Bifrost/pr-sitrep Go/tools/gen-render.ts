// Golden generator for the renderers. Not committed (no cross-app imports).
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const SRC = process.env.TS_SRC as string;
const c = require(`${SRC}/core/classification`);
const md = require(`${SRC}/core/render/markdown.renderer`);
const sl = require(`${SRC}/core/render/slack.renderer`);
const mk = require(`${SRC}/core/render/mrkdwn`);
const sha = execSync("git rev-parse HEAD", { cwd: SRC }).toString().trim();

let n = 100;
function row(o: Record<string, unknown>) {
	const number = (o.number as number) ?? ++n;
	const f = {
		owner: "gfs-bifrost", repo: "fapi", number, url: `https://github.com/gfs-bifrost/fapi/pull/${number}?a=1&b=<2>`,
		title: "t", author: "hjf", isDraft: false, isBot: false, baseRef: "main", headRef: "h", headSha: "s",
		isDefaultBase: true, stackedOnOpenPR: null, mergeableState: "clean",
		checks: { total: 3, success: 3, failing: [] }, reviewDecision: "APPROVED", selfHoldPhraseDetected: false,
		ticketKey: `FUSE-${number}`, createdAt: "2026-08-10T09:00:00Z", updatedAt: "2026-08-11T09:00:00Z",
		idleCalendarDays: 1, idleWorkingDays: 1, stale: false, evidence: { sectionFound: true, verdict: "present" },
		...o,
	};
	return { ...f, classification: c.classify(f) };
}
const authors = ["alice", "Bob", "ab-c", "abc", "x_gfsdev", "X-1", "9z", "oliver-denton_gfsdev", "Oliver", "émile", "emile", "hjf", "jo.smith", "jo-smith"];
const states = [
	{},
	{ mergeableState: "dirty" },
	{ mergeableState: "unstable", checks: { total: 4, success: 2, failing: ["test <unit>", "lint & fmt"] } },
	{ reviewDecision: null },
	{ reviewDecision: null, evidence: { sectionFound: false, verdict: "outstanding" } },
	{ reviewDecision: null, evidence: { sectionFound: true, verdict: "ambiguous", rawExcerpt: "works" } },
	{ reviewDecision: "CHANGES_REQUESTED" },
	{ isDraft: true },
	{ isDraft: true, checks: { total: 0, success: 0, failing: [] } },
	{ isDraft: true, checks: { total: 2, success: 1, failing: ["build"] } },
	{ mergeableState: "has_hooks" },
];
const prs = [];
let i = 0;
for (const author of authors) {
	for (let k = 0; k < 3; k++) {
		const s = states[i++ % states.length];
		prs.push(row({
			author, ...s, idleWorkingDays: (i * 7) % 5, stale: i % 4 === 0,
			createdAt: `2026-08-${String(10 + ((i * 3) % 17)).padStart(2, "0")}T09:00:00Z`,
			ticketKey: i % 6 === 0 ? null : `FUSE-${i}`,
		}));
	}
}
function payload(prs: unknown[], sprintName: string | null, merges: unknown[]) {
	return { generatedAt: "2026-10-29T08:00:04.123Z", author: "hjf", window: { sprintName, since: "2026-10-15" }, summary: c.summarise(prs), prs, merges };
}
const merges = [
	{ repo: "fapi", number: 1, merged: true, sha: "0123456789abcdef" },
	{ repo: "fapi", number: 2, merged: false, sha: null, error: "409 <conflict> & more" },
	{ repo: "fapi", number: 3, merged: false, sha: null, error: "" },
	{ repo: "fapi", number: 4, merged: false, sha: "" },
];
const mentions = new Map([["hjf", "U123ABC"], ["alice", "W0ALICE"], ["Bob", ""]]);
const cases = [
	{ payload: payload(prs, "Sprint 7 <b>", merges), me: "hjf" },
	{ payload: payload(prs, null, []), me: null },
	{ payload: payload(prs.filter((p) => p.isDraft), null, []), me: "hjf" },
	{ payload: payload([], "S", []), me: null },
].map(({ payload, me }) => {
	const opts = { me, jiraBaseUrl: "https://globalfreight.atlassian.net" };
	const plan = sl.renderSlackPlan(payload, { ...opts, mentions });
	return {
		payload, me,
		markdown: md.renderMarkdown(payload, opts),
		plan,
		planNoMentions: sl.renderSlackPlan(payload, { ...opts, mentions: new Map() }),
		mrkdwn: plan.messages.map((m: { text: string }) => mk.toMrkdwn(m.text)),
	};
});
const extraMrkdwn = [
	"**a** **b**", "***x***", "[a](b c)", "[a](b c)", "[a]](b)", "[[a](b)", "[a\nb](c)", "&lt;@U1&gt;", "<@u1>", "<@U1>x<@W2>",
	"**", "**unclosed", "[x](y)(z)", "[x]()", "a & b < c > d", "**[link](u)**", "[**b**](u)",
].map((s) => ({ in: s, want: mk.toMrkdwn(s) }));
const lines = [
	`"tsSha":${JSON.stringify(sha)}`,
	`"cases":${JSON.stringify(cases)}`,
	`"mentions":${JSON.stringify(Object.fromEntries(mentions))}`,
	`"mrkdwn":${JSON.stringify(extraMrkdwn)}`,
];
writeFileSync(process.argv[2], `{\n${lines.join(",\n")}\n}\n`);
console.log(`wrote ${prs.length} PRs x ${cases.length} cases, ts ${sha.slice(0, 7)}`);
