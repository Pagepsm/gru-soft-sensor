from __future__ import annotations

import csv
import json
import math
import re
import statistics
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-12


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def stats(values: list[float]) -> tuple[float, float, int]:
    return statistics.mean(values), statistics.stdev(values), len(values)


class ResultConsistencyTests(unittest.TestCase):
    def assert_close(self, actual: float, expected: str, label: str) -> None:
        self.assertTrue(
            math.isclose(actual, float(expected), rel_tol=TOLERANCE, abs_tol=TOLERANCE),
            f"{label}: actual={actual!r}, expected={expected!r}",
        )

    def test_v14_summary_matches_raw_results(self) -> None:
        folder = ROOT / "results" / "v14"
        raw = read_csv(folder / "raw_results.csv")
        summary = read_csv(folder / "summary.csv")
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in raw:
            grouped[row["model"]].append(row)

        columns = {
            "test_true_mae": "test_true_mae_diagnostic",
            "test_obs_mae": "test_obs_mae",
            "val_obs_mae": "val_obs_mae",
            "parameter_count": "parameter_count",
        }
        for row in summary:
            source_rows = grouped[row["model"]]
            with self.subTest(model=row["model"]):
                self.assertEqual(len(source_rows), int(row["seed_count"]))
                for prefix, raw_column in columns.items():
                    values = [float(item[raw_column]) for item in source_rows]
                    mean, std, _ = stats(values)
                    self.assert_close(mean, row[f"{prefix}_mean"], f"{prefix} mean")
                    std_column = f"{prefix}_std"
                    if std_column in row:
                        self.assert_close(std, row[std_column], f"{prefix} std")

    def test_v14_paired_comparisons_match_raw_results(self) -> None:
        folder = ROOT / "results" / "v14"
        raw = read_csv(folder / "raw_results.csv")
        paired = read_csv(folder / "paired_comparisons.csv")
        by_seed_model = {
            (int(row["process_seed"]), row["model"]): float(row["test_true_mae_diagnostic"])
            for row in raw
        }
        seeds = sorted({int(row["process_seed"]) for row in raw})

        for row in paired:
            deltas = [
                by_seed_model[(seed, row["left_model"])]
                - by_seed_model[(seed, row["right_model"])]
                for seed in seeds
            ]
            mean, std, count = stats(deltas)
            with self.subTest(comparison=row["comparison"]):
                self.assert_close(mean, row["mean_delta"], "mean delta")
                self.assert_close(std, row["std_delta"], "std delta")
                self.assertEqual(sum(delta < 0 for delta in deltas), int(row["left_wins"]))
                self.assertEqual(sum(delta == 0 for delta in deltas), int(row["ties"]))
                self.assertEqual(count, int(row["seed_count"]))

    def test_v13_label_summary_matches_raw_results(self) -> None:
        folder = ROOT / "results" / "v13" / "representation"
        raw = read_csv(folder / "05_labels.csv")
        summary = read_csv(folder / "05_labels_summary.csv")
        grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for row in raw:
            grouped[(row["label_count_requested"], row["model"])].append(row)

        for row in summary:
            source_rows = grouped[(row["label_count_requested"], row["model"])]
            with self.subTest(labels=row["label_count_requested"], model=row["model"]):
                for prefix, raw_column in (
                    ("test_true_mae", "test_true_mae"),
                    ("test_obs_mae", "test_obs_mae"),
                    ("n_train_labels", "n_train_labels"),
                ):
                    values = [float(item[raw_column]) for item in source_rows]
                    mean, std, count = stats(values)
                    self.assert_close(mean, row[f"{prefix}_mean"], f"{prefix} mean")
                    self.assert_close(std, row[f"{prefix}_std"], f"{prefix} std")
                    self.assertEqual(count, int(row[f"{prefix}_count"]))

    def test_resync_summary_matches_raw_results(self) -> None:
        folder = ROOT / "results" / "resync_v2" / "necessity"
        raw = read_csv(folder / "01_necessity_raw.csv")
        summary = read_csv(folder / "01_necessity_summary.csv")
        grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for row in raw:
            grouped[(row["disturbance_shape"], row["method"])].append(row)

        metric_columns = [
            name for name in raw[0] if name.startswith("future_") or name.startswith("dense_")
        ]
        for row in summary:
            source_rows = grouped[(row["disturbance_shape"], row["method"])]
            with self.subTest(shape=row["disturbance_shape"], method=row["method"]):
                self.assertEqual(len(source_rows), int(row["count"]))
                for column in metric_columns:
                    values = [float(item[column]) for item in source_rows if item[column] != ""]
                    if not values:
                        continue
                    mean, std, _ = stats(values)
                    self.assert_close(mean, row[f"{column}_mean"], f"{column} mean")
                    self.assert_close(std, row[f"{column}_std"], f"{column} std")

    def test_notebooks_are_valid_json(self) -> None:
        for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
            with self.subTest(path=path.name):
                with path.open(encoding="utf-8") as handle:
                    notebook = json.load(handle)
                self.assertEqual(notebook["nbformat"], 4)
                self.assertIsInstance(notebook["cells"], list)

    def test_notebook_code_cells_compile(self) -> None:
        for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
            notebook = json.loads(path.read_text(encoding="utf-8"))
            for index, cell in enumerate(notebook["cells"]):
                if cell["cell_type"] != "code":
                    continue
                source = "".join(cell["source"])
                with self.subTest(path=path.name, cell=index):
                    compile(source, f"{path.name}:cell-{index}", "exec")

    def test_notebook_defaults_are_smoke(self) -> None:
        soft_sensor = (ROOT / "notebooks" / "GRU_soft_sensor_simulation_v14.ipynb").read_text(
            encoding="utf-8"
        )
        resync = (ROOT / "notebooks" / "GRU_state_resync_simulation_v2.ipynb").read_text(
            encoding="utf-8"
        )
        self.assertIn(r'run_mode: str = \"smoke\"', soft_sensor)
        self.assertIn(r'run_stage: str = \"smoke\"', resync)
        self.assertIn("use_google_drive: bool = False", resync)

    def test_local_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
        for path in sorted(ROOT.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for target in link_pattern.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative_target = target.split("#", 1)[0]
                resolved = (path.parent / relative_target).resolve()
                with self.subTest(path=path.relative_to(ROOT), target=target):
                    self.assertTrue(resolved.exists(), f"missing link target: {target}")

    def test_no_local_paths_or_tokens(self) -> None:
        forbidden = (
            "github_" + "pat_",
        )
        local_path_pattern = re.compile(r"(?<![A-Za-z0-9])[A-Z]:[\\/][^\s\"']+")
        token_pattern = re.compile(r"(?:gh[pousr]_|sk-)[A-Za-z0-9_-]{20,}")
        suffixes = {".md", ".json", ".ipynb", ".py", ".txt", ".csv"}
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in suffixes:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if path.suffix.lower() == ".ipynb":
                notebook = json.loads(text)
                text = "\n".join(
                    "".join(cell.get("source", [])) for cell in notebook.get("cells", [])
                )
            with self.subTest(path=path.relative_to(ROOT)):
                for value in forbidden:
                    self.assertNotIn(value, text)
                self.assertIsNone(local_path_pattern.search(text))
                self.assertIsNone(token_pattern.search(text))


if __name__ == "__main__":
    unittest.main()
