import { readFile } from "node:fs/promises";
import path from "node:path";

const CONFIG_PATH = "data/crawl_config.json";

export function getGithubRepo(): string | undefined {
  return process.env.GITHUB_REPO?.trim();
}

export function getGithubToken(): string | undefined {
  return process.env.GITHUB_TOKEN?.trim();
}

export function isGithubConfigured(): boolean {
  return Boolean(getGithubRepo() && getGithubToken());
}

export async function readLocalCrawlConfig(): Promise<string> {
  const filePath = path.join(process.cwd(), CONFIG_PATH);
  return readFile(filePath, "utf-8");
}

type GithubContentResponse = {
  sha?: string;
  content?: string;
  message?: string;
};

function apiUrl(repoPath: string): string {
  const repo = getGithubRepo();
  if (!repo) throw new Error("GITHUB_REPO is not configured");
  return `https://api.github.com/repos/${repo}/contents/${repoPath}`;
}

export async function fetchGithubFile(repoPath: string): Promise<{ content: string; sha: string } | null> {
  const token = getGithubToken();
  if (!token) throw new Error("GITHUB_TOKEN is not configured");

  const res = await fetch(apiUrl(repoPath), {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    cache: "no-store",
  });

  if (res.status === 404) return null;
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`GitHub GET failed (${res.status}): ${body}`);
  }

  const data = (await res.json()) as GithubContentResponse;
  if (!data.content || !data.sha) {
    throw new Error("GitHub response missing content or sha");
  }

  const content = Buffer.from(data.content, "base64").toString("utf-8");
  return { content, sha: data.sha };
}

export async function commitGithubFile(
  repoPath: string,
  content: string,
  message: string,
  sha?: string
): Promise<{ commitSha: string }> {
  const token = getGithubToken();
  if (!token) throw new Error("GITHUB_TOKEN is not configured");

  const body: Record<string, string> = {
    message,
    content: Buffer.from(content, "utf-8").toString("base64"),
  };
  if (sha) body.sha = sha;

  const res = await fetch(apiUrl(repoPath), {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub PUT failed (${res.status}): ${text}`);
  }

  const data = (await res.json()) as { commit?: { sha?: string } };
  return { commitSha: data.commit?.sha || "unknown" };
}

export const CRAWL_CONFIG_REPO_PATH = CONFIG_PATH;
