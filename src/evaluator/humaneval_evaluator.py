import multiprocessing as mp
import traceback
import json
import os

from datasets import load_dataset


class HumanEvalEvaluator:

    def __init__(self, timeout_s: float = 10.0):
        self.timeout_s = timeout_s
        self.problems = self._load()

    def _load(self):
        ds = load_dataset("openai_humaneval", split="test")
        probs = {}
        for row in ds:
            probs[row["task_id"]] = row
        return probs

    @staticmethod
    def _worker(q, prompt, completion, test, entry_point):
        try:
            ns = {}
            exec(prompt + "\n" + completion + "\n", ns, ns)

            if entry_point not in ns or not callable(ns[entry_point]):
                q.put((False, f"Entry point '{entry_point}' missing or not callable"))
                return

            candidate = ns[entry_point]
            ns["candidate"] = candidate

            exec(test, ns, ns)

            if "check" in ns and callable(ns["check"]):
                ns["check"](candidate)

            q.put((True, ""))
        except Exception:
            q.put((False, traceback.format_exc()))

    def run_tests(self, problem, code):

        q = mp.Queue()
        p = mp.Process(
            target=self._worker,
            args=(
                q,
                problem["prompt"],
                code,
                problem["test"],
                problem["entry_point"],
            ),
        )
        p.start()
        p.join(self.timeout_s)

        if p.is_alive():
            p.terminate()
            return False, "Timeout"

        return q.get()

    def evaluate(self, agent, n_tasks=None, out_path="results/run_baseline.jsonl"):
        os.makedirs("results", exist_ok=True)

        task_ids_all = list(self.problems.keys())
        if n_tasks is None:
            task_ids = task_ids_all
        else:
            task_ids = task_ids_all[:n_tasks]

        passed = 0

        with open(out_path, "w", encoding="utf-8") as f:
            for idx, tid in enumerate(task_ids, start=1):
                print(f"[{idx}/{len(task_ids)}] {tid}")

                result = agent.solve_one(self.problems[tid], evaluator=self)

                row = {"task_id": tid, **result}
                passed += int(result.get("passed", False))

                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()

        if len(task_ids) == 0:
            return 0.0

        return passed / len(task_ids)
