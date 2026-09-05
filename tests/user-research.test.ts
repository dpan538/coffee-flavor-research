import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";

const root = new URL("../db/data/user-research-round1/", import.meta.url);
const text = (name: string) => readFileSync(new URL(name, root), "utf8");
const rows = (name: string) => {
  const [header, ...lines] = text(name).trimEnd().split("\n");
  return lines.map((line) =>
    Object.fromEntries(
      header!.split("\t").map((key, i) => [key, line.split("\t")[i] ?? ""]),
    ),
  );
};

describe("restricted-source public survey receipt", () => {
  it("keeps single-digit note artifacts out of qualitative interpretation", () => {
    const result = execFileSync(
      "python3",
      [
        "-c",
        "import importlib.util,json; s=importlib.util.spec_from_file_location('intake','db/scripts/ingest-user-research-round1.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(json.dumps([m.is_format_artifact_candidate(v) for v in ('3',' 4 ',5,'B','8-10','')]))",
      ],
      { encoding: "utf8" },
    );
    expect(JSON.parse(result)).toEqual([true, true, true, false, false, false]);
  });
  it("reconciles 11 source events, 10 payloads and all 220 question records", () => {
    const files = rows("USER_TEST_FILE_AUDIT.tsv");
    const answers = rows("USER_TEST_RESPONSE_LEDGER.tsv");
    expect(files).toHaveLength(11);
    expect(new Set(files.map((r) => r.file_sha256)).size).toBe(10);
    expect(files.filter((r) => r.primary_included === "true")).toHaveLength(10);
    expect(answers).toHaveLength(220);
    expect(answers.filter((r) => r.primary_included === "true")).toHaveLength(
      200,
    );
    expect(files.filter((r) => r.duplicate_cluster_id === "D001")).toHaveLength(
      2,
    );
    const numbers = files.find((r) => r.file_format === "numbers")!;
    expect(numbers.primary_included).toBe("true");
    expect(answers.filter((r) => r.file_id === numbers.file_id)).toHaveLength(
      20,
    );
    for (let q = 1; q <= 20; q++) {
      const summary = rows("USER_TEST_QUESTION_SUMMARY.tsv").filter(
        (r) => r.question_id === `Q${q}`,
      );
      expect(summary.reduce((sum, r) => sum + Number(r.count), 0)).toBe(10);
    }
  });

  it("preserves open and supplementary answers without silently recoding them", () => {
    const answers = rows("USER_TEST_RESPONSE_LEDGER.tsv");
    const open = answers.filter((r) => r.coded_answer === "OPEN");
    expect(open).toHaveLength(1);
    expect(open[0]).toMatchObject({ file_id: "F001", question_id: "Q13" });
    expect(answers.filter((r) => r.supplementary_code)).toHaveLength(2);
    const manifest = JSON.parse(text("USER_TEST_MANIFEST.json"));
    expect(manifest.single_digit_note_artifact_candidate_count).toBe(0);
    expect(manifest.numbers_file_included).toBe(true);
    expect(manifest.review_aid_option_count_matches).toBe(80);
    expect(manifest.ml_training_role).toBe(false);
    expect(manifest.professional_sensory_label_role).toBe(false);
  });

  it("checksums every public file and excludes raw response files and paths", () => {
    const sums = text("SHA256SUMS").trim().split("\n");
    const covered = sums.map((line) => line.slice(66));
    expect(covered.sort()).toEqual(
      readdirSync(root)
        .filter((n) => n !== "SHA256SUMS")
        .sort(),
    );
    for (const line of sums) {
      expect(
        createHash("sha256")
          .update(readFileSync(new URL(line.slice(66), root)))
          .digest("hex"),
      ).toBe(line.slice(0, 64));
    }
    for (const name of covered) {
      expect(name).not.toMatch(/\.(xlsx|numbers)$/);
      expect(text(name)).not.toMatch(
        /\/Users\/|\/Downloads\/|source_name|workbook_author/,
      );
    }
  });
});
