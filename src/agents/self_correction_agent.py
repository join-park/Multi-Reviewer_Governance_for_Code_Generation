from __future__ import annotations

from src.agents.base_agent import BaseCodeAgent


class SelfCorrectionAgent(BaseCodeAgent):
    def __init__(self, cfg, max_retries: int = 3):
        super().__init__(cfg)
        self.max_retries = max_retries

    def solve_one(self, problem, evaluator):
        task_id = problem.get("task_id", "UNKNOWN_TASK")
        entry_point = problem.get("entry_point", "UNKNOWN_ENTRY")
        prompt = problem["prompt"]

        # 로그 가독성: 너무 길면 일부만
        prompt_preview = prompt[:400].rstrip() + ("..." if len(prompt) > 400 else "")

        print("=" * 80)
        print(f"[TASK] {task_id} | entry_point={entry_point}")
        print("[PROMPT PREVIEW]")
        print(prompt_preview)
        print("-" * 80)

        # 초기 생성
        raw = self.code_chain.invoke({"task": prompt})
        code = self.extract_code(raw)

        print("[INITIAL GENERATED CODE]")
        print(code)
        print("-" * 80)

        last_err = ""

        for i in range(self.max_retries + 1):
            print(f"[{task_id}] Attempt {i}/{self.max_retries}")

            ok, err = evaluator.run_tests(problem, code)

            if ok:
                print(f"[{task_id}] ✅ PASS (attempt={i})")
                print("=" * 80)
                return {
                    "passed": True,
                    "iters": i,
                    "code": code,
                    "last_error": ""
                }

            last_err = err
            err_preview = (err[:800].rstrip() + ("..." if len(err) > 800 else ""))
            print(f"[{task_id}] ❌ FAIL (attempt={i})")
            print("[TEST ERROR PREVIEW]")
            print(err_preview)
            print("-" * 80)

            if i == self.max_retries:
                break

            fix_prompt = (
                "The following Python code failed unit tests.\n\n"
                f"ERROR:\n{last_err}\n\n"
                f"CODE:\n{code}\n\n"
                "Fix the code and return ONLY the full fixed code."
            )

            raw = self.code_chain.invoke({"task": fix_prompt})
            code = self.extract_code(raw)

            print(f"[{task_id}] [REPAIRED CODE] (after attempt={i})")
            print(code)
            print("-" * 80)

        print(f"[{task_id}] ❌ FINAL FAIL after {self.max_retries} retries")
        print("=" * 80)
        return {
            "passed": False,
            "iters": self.max_retries,
            "code": code,
            "last_error": last_err
        }

    # def solve_one(self, problem, evaluator):
    #     print(f"=" * 50)
    #     print(f"문제:\n{problem}")
    #     prompt = problem["prompt"]
    #
    #     # 초기 생성
    #     raw = self.code_chain.invoke({"task": prompt})
    #     code = self.extract_code(raw)
    #     print(f"초기 생성 code: {code}")
    #     last_err = ""
    #
    #     for i in range(self.max_retries + 1):
    #         ok, err = evaluator.run_tests(problem, code)
    #
    #         if ok:
    #             return {
    #                 "passed": True,
    #                 "iters": i,
    #                 "code": code,
    #                 "last_error": ""
    #             }
    #
    #         last_err = err
    #
    #         if i == self.max_retries:
    #             break
    #
    #         fix_prompt = (
    #             "The following Python code failed unit tests.\n\n"
    #             f"ERROR:\n{last_err}\n\n"
    #             f"CODE:\n{code}\n\n"
    #             "Fix the code and return ONLY the full fixed code."
    #         )
    #
    #         raw = self.code_chain.invoke({"task": fix_prompt})
    #         code = self.extract_code(raw)
    #
    #     return {
    #         "passed": False,
    #         "iters": self.max_retries,
    #         "code": code,
    #         "last_error": last_err
    #     }
