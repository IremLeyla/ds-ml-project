# Prompt for the teammate's Claude Code session

Copy everything inside the box into a new Claude Code session that is open in this repository (`ds-ml-project`, branch `feature/neural-network`).

```text
You are continuing a team project: a neural-network (NN) challenger for our finished STEG fraud-detection project. A teammate and their Claude session did the planning; I (the teammate taking over) will run the compute-heavy part with you.

First read these files completely, in this order, before doing anything:
1. NN_HANDOFF.md (status, what is left, rules, setup)
2. model-comparison-plan.md (the FROZEN comparison plan, do not change its rules)
3. protocol.md (all team decisions, newest at the bottom; the rows dated 2026-11-05 matter most)
4. CLAUDE.md (project rules, including how decisions are logged)
5. model_results.md and 00_overview.md (what the historical LightGBM did)

Then:
- Run `git status` and `git log --oneline -5`, tell me which branch I am on, and run `git pull` if the branch is behind origin. The notebook 16_neural-network.ipynb may not exist yet or may only have sections 1 to 4.
- Check the setup in NN_HANDOFF.md ("Setup on a new machine") step by step with me: data in data/, the v3 tables rebuilt with build_feature_tables.py (compare the SHA-256 values with the plan), the main environment and the NN environment .venv-nn. Do not continue until the hashes match. Do not install anything or change my machine without asking me first.
- Then continue at section 5 of 16_neural-network.ipynb (random search) and work through sections 5 to 9 as described in NN_HANDOFF.md. Write comprehensive markdown and well-commented code in English. Save the result files named in NN_HANDOFF.md under results/.
- Work step by step: show me the plan for each section and wait for my confirmation before you start long computations. Run long jobs in the background and tell me how long they will probably take.

Hard rules (from the frozen plan):
- The test set is X_valid_v3.csv / y_valid.csv (27,099 clients). Never use it for early stopping, tuning, architecture choice, threshold choice or preprocessing. It is scored exactly once, in section 7, after the final configuration is saved and committed.
- Fit all preprocessing on training clients only. Use the same 39 features as LightGBM.
- Do not re-score LightGBM (only time it). Do not add subgroups, calibration, extra models or a no-ML rule.
- If a rule of the plan has to change, do not change it silently: ask me, then log it with the decision-notetaker agent (see CLAUDE.md) and mention it in the report.
- Report all numbers unrounded and include results that look bad for the NN.
- Do not commit or push unless I ask you to. Keep NN model files out of git.

When all of section 9 is finished, summarize the results in a short table and tell me what to send back to my teammate.
```
