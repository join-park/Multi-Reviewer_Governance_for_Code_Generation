from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

from src.agents.base_agent import BaseCodeAgent


class MultiReviewerAgent(BaseCodeAgent):
    def __init__(self,
                 cfg,
                 max_regen=1,):
        super().__init__(cfg)
        self.max_regen = max_regen

        self.reviewer_llm = ChatOllama(
            model=getattr(cfg, "review_llm_name", cfg.code_llm_name),
            temperature=getattr(cfg, "review_temperature", 0.5),
            base_url=cfg.base_url
        )

        # ✅ Reviewer 역할(다양성 확보)
        self.reviewer_roles = [
            "Correctness-focused reviewer. Approve if the solution is likely correct for the prompt.",
            "Edge-case reviewer. Focus on boundary/tricky cases. Approve if still correct.",
            "Quality reviewer. Mention performance/style in COMMENT, but DO NOT reject solely for them if correct."
        ]

        self.reviewer_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert code reviewer and debugger.\n"
             "Goal: help maximize unit-test passing rate.\n"
             "Use the TEST RESULT (traceback) to pinpoint issues.\n\n"
             "Return exactly this format:\n"
             "STATUS: LGTM or NEEDS_CHANGES\n"
             "CHANGES: <a short bullet list of concrete fixes; or NONE>\n"
             "No extra text."
             ),
            ("user", "{task}")
        ])

        self.reviewer_chain = (
            self.reviewer_prompt
            | self.reviewer_llm
            | StrOutputParser()
        )

    def solve_one(self, problem, evaluator):
        task_id = problem.get("task_id", "UNKNOWN_TASK")
        prompt = problem["prompt"]

        print("=" * 80)
        print(f"[TASK] {task_id}")
        print("-" * 80)

        last_err = ""
        last_code = ""

        roles = [
            "Correctness/logic reviewer (focus on algorithmic correctness).",
            "Edge-case reviewer (try to find counterexamples from the prompt).",
            "Debugger reviewer (use traceback to propose minimal fixes).",
        ]

        for regen_i in range(self.max_regen + 1):
            print(f"[{task_id}] === ROUND {regen_i}/{self.max_regen} ===")

            # 1) generate
            raw = self.code_chain.invoke({"task": prompt})
            code = self.extract_code(raw)
            last_code = code

            # 2) test
            ok, err = evaluator.run_tests(problem, code)
            if ok:
                print(f"[{task_id}] PASS on initial generation")
                return {"passed": True, "iters": regen_i, "code": code, "last_error": ""}

            last_err = err
            err_preview = err[:800].rstrip() + ("..." if len(err) > 800 else "")
            print(f"[{task_id}] FAIL → collecting reviewer fixes")
            print("[TRACEBACK PREVIEW]")
            print(err_preview)
            print("-" * 80)

            # 3) reviewers produce fixes (test result included)
            review_text = (
                f"PROMPT:\n{prompt}\n\n"
                f"CODE:\n{code}\n\n"
                f"TEST RESULT (traceback):\n{err_preview}\n"
            )

            changes_list = []
            raw_reviews = []
            for i in range(3):
                role = roles[i]
                reviewer_raw = self.reviewer_chain.invoke({"task": f"ROLE: {role}\n\n{review_text}"})
                reviewer_raw_str = (reviewer_raw or "").strip()
                raw_reviews.append({"role": role, "raw": reviewer_raw_str})

                print(f"[{task_id}] Reviewer {i+1}/3 role={role}")
                print(reviewer_raw_str)

                # CHANGES 라인만 뽑기(없으면 전체를 changes로 넣는 fallback)
                ch = ""
                for line in reviewer_raw_str.splitlines():
                    if line.strip().upper().startswith("CHANGES:"):
                        ch = line.split(":", 1)[1].strip()
                        break
                if not ch:
                    ch = reviewer_raw_str
                changes_list.append(f"[Reviewer {i+1} | {role}] {ch}")

                print("-" * 80)

            combined_changes = "\n".join(changes_list)

            # 4) revise using combined fixes
            fix_prompt = (
                "You are an expert Python programmer.\n"
                "Fix the code to pass the unit tests.\n"
                "Apply the reviewer suggestions below, prioritizing correctness.\n"
                "Return ONLY the full fixed code in a python code block.\n\n"
                f"PROMPT:\n{prompt}\n\n"
                f"CURRENT CODE:\n{code}\n\n"
                f"REVIEWER FIXES:\n{combined_changes}\n"
            )

            raw2 = self.code_chain.invoke({"task": fix_prompt})
            revised = self.extract_code(raw2)

            print(f"[{task_id}] [REVISED CODE]")
            print(revised)
            print("-" * 80)

            # 5) test revised
            ok2, err2 = evaluator.run_tests(problem, revised)
            if ok2:
                print(f"[{task_id}] PASS after revision")
                return {
                    "passed": True,
                    "iters": regen_i,
                    "code": revised,
                    "last_error": "",
                    "review_raw": raw_reviews,
                }

            last_err = err2
            print(f"[{task_id}] Still FAIL after revision")
            err2_preview = err2[:800].rstrip() + ("..." if len(err2) > 800 else "")
            print("[TRACEBACK PREVIEW]")
            print(err2_preview)
            print("-" * 80)

        return {
            "passed": False,
            "iters": self.max_regen,
            "code": last_code,
            "last_error": last_err or "Failed after max_regen",
        }
