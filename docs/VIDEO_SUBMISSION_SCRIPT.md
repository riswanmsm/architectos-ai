# 5-Minute Solution Video Script (Deliverable 03)

Use this script and screen flow to record your 5-minute submission video for the **micro1 Agentic Workflows Hackathon**.

---

## ⏱️ Video Breakdown (Total Time: 4:45 - 5:00)

| Timestamp | Section | Visual Focus | Script & Talking Points |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:45** | **The Problem & Who Has It** | Slides / Title Screen | *"Building software without a rigorous blueprint leads to weeks of costly rework. Solopreneurs and early-stage engineering leads usually rely on single-prompt AI chats that hallucinate APIs without database entities, omit security boundaries, and produce unverified drafts. ArchitectOS solves this by automating a full engineering review committee."* |
| **0:45 – 1:30** | **The Baseline Comparison** | Terminal / Evaluation Table | *"We established a fair baseline: 1 direct prompt given the exact same idea and schema. While it outputs text quickly, our frozen 10-case evaluation shows the baseline fails on critical security boundaries and cross-artifact consistency, scoring low on Verified Blueprint Coverage (VBC)."* |
| **1:30 – 3:00** | **Live Execution & Agent Collaboration** | Browser UI (`localhost:5173`) | 1. Enter an idea: *"A multi-tenant subscription workspace with role-based access and billing webhooks."*<br/>2. Show the 8 disciplines activating: Requirements $\rightarrow$ Architecture $\rightarrow$ Data Engineering $\rightarrow$ API $\rightarrow$ Testing.<br/>3. Highlight how downstream agents consume upstream artifacts in real time. |
| **3:00 – 3:45** | **Deterministic Verification & Self-Correction Loop** | Browser UI / Reopening alert | 1. Show the Risk Engineering stage executing the deterministic verifier.<br/>2. Point out the audit alert: *"Notice how the verifier detected missing OAuth2 rate-limiting in the initial draft, deriving a real readiness score below threshold and reopening Architecture Review."*<br/>3. Show Architecture revising the design $\rightarrow$ Risk re-evaluating $\rightarrow$ Score promoted to 96%.<br/>4. Show Human Approval Gate. |
| **3:45 – 4:20** | **Improvement Changelog & Removed Experiment** | Slides / `IMPROVEMENT_CHANGELOG.md` | *"Our improvement changelog details how shared context and deterministic verifiers boosted our VBC score by over 40%. Importantly, our **Removed Experiment** tested unconstrained multi-turn agent debate—which exploded token costs by 3.8x without fixing schema errors. Replacing debate with deterministic verification gave us 100% reference integrity."* |
| **4:20 – 5:00** | **Hot Take & Conclusion** | GitHub Repo / Summary slide | *"Our key takeaway: More agents don't make better software. Strict domain specialization, deterministic rule checking, and targeted repair loops are the only reliable way to produce blueprints an engineer would actually sign their name to. Thank you!"* |

---

## 💡 Pro Recording Tips:
- **Audio:** Use a clean microphone with clear pacing.
- **Screen:** Zoom browser to 110%–125% for crisp readability of markdown specifications.
- **Tone:** Professional, empirical, and grounded in the evaluation data.
