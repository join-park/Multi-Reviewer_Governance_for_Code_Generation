from src.agents.base_agent import AgentConfig
from src.agents.self_correction_agent import SelfCorrectionAgent
from src.agents.multi_review_agent import MultiReviewerAgent
from src.evaluator.humaneval_evaluator import HumanEvalEvaluator
import multiprocessing as mp


def main():
    cfg = AgentConfig()

    evaluator = HumanEvalEvaluator()

    # baseline = SelfCorrectionAgent(cfg, max_retries=6)
    proposed = MultiReviewerAgent(cfg, max_regen=1)

    # print("Baseline:", evaluator.evaluate(baseline, out_path="results/run_baseline.jsonl"))
    print("Proposed:", evaluator.evaluate(proposed, out_path="results/run_proposed_regen2_2.jsonl"))


if __name__ == "__main__":
    mp.freeze_support()
    main()
