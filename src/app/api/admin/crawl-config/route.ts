import { NextResponse } from "next/server";
import { isAdminAuthenticated } from "@/lib/adminAuth";
import {
  CRAWL_CONFIG_REPO_PATH,
  commitGithubFile,
  fetchGithubFile,
  isGithubConfigured,
  readLocalCrawlConfig,
} from "@/lib/githubContents";
import {
  formatCrawlConfigJson,
  validateCrawlConfig,
} from "@/lib/crawlConfigSchema";

async function requireAdmin() {
  if (!(await isAdminAuthenticated())) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return null;
}

export async function GET() {
  const denied = await requireAdmin();
  if (denied) return denied;

  try {
    const content = await readLocalCrawlConfig();
    return NextResponse.json({ content, source: "local" });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to read config";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  const denied = await requireAdmin();
  if (denied) return denied;

  if (!isGithubConfigured()) {
    return NextResponse.json(
      { error: "GITHUB_TOKEN and GITHUB_REPO must be set on the server (Vercel env)." },
      { status: 503 }
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const configText =
    typeof body === "object" && body !== null && "content" in body
      ? String((body as { content: string }).content)
      : null;

  if (!configText) {
    return NextResponse.json({ error: "Request body must include content (JSON string)" }, { status: 400 });
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(configText);
  } catch {
    return NextResponse.json({ error: "Invalid JSON syntax" }, { status: 400 });
  }

  const validated = validateCrawlConfig(parsed);
  if (!validated.ok) {
    return NextResponse.json({ error: "Validation failed", errors: validated.errors }, { status: 400 });
  }

  const formatted = formatCrawlConfigJson(validated.data);

  try {
    const existing = await fetchGithubFile(CRAWL_CONFIG_REPO_PATH);
    const result = await commitGithubFile(
      CRAWL_CONFIG_REPO_PATH,
      formatted,
      "chore: update crawl config from admin",
      existing?.sha
    );

    return NextResponse.json({
      ok: true,
      commitSha: result.commitSha,
      message: "Saved to GitHub. PC crawler will apply after git pull (next scheduled run).",
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "GitHub save failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
