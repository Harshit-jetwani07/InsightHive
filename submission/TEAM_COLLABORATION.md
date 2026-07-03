# Team and Collaboration Guide

## Confirmed team

- **Harshit Jetwani — Team Leader & Co-Creator**
- **Jiya Aalwani — Team Member & Co-Creator**

InsightHive is a joint project. Harshit Jetwani is the designated Kaggle Team Leader
and final submission owner. Both creators must appear on the final Kaggle team
and receive visible credit in the writeup and video description.

InsightHive is intended to be submitted as one collaborative Kaggle project.
The competition allows a maximum team size of five and one hackathon submission
per team. Confirm the live competition page before the final deadline in case
Kaggle updates an operational detail.

## Before inviting collaborators

Agree on:

- the Kaggle team owner;
- final Kaggle display names and profile URLs;
- GitHub usernames;
- contribution ownership;
- who controls Cloud Run, YouTube, and the final Kaggle submission;
- a private channel for credentials and deployment coordination.

Never send API keys or passwords through Git commits, issues, pull requests, or
Kaggle comments.

## Recommended roles

One person may own multiple roles.

| Role | Responsibility |
| --- | --- |
| Harshit Jetwani — Team Leader | Creates/confirms the Kaggle team and performs final Submit |
| Jiya Aalwani — Team Member & Co-Creator | Shared implementation, evidence, and submission support |
| Agent engineering | ADK orchestration, specialist instructions, routing evidence |
| Data and evaluation | Demo dataset, test cases, metrics, evidence JSON |
| Product and UX | Mission Control, result clarity, accessibility, screenshots |
| Documentation and demo | README, writeup, video, media gallery, link verification |

## Kaggle collaboration procedure

1. The submission owner creates the project/writeup.
2. Open the competition Team or project collaboration controls.
3. Invite every eligible collaborator using the exact Kaggle account identity.
4. Each teammate accepts before the team-lock or submission deadline.
5. Confirm every contributor appears on the final team.
6. Select **Agents for Business**.
7. Only the agreed owner clicks final **Submit**.
8. Re-open the project and verify it is submitted, not a draft.
9. Do not create duplicate individual submissions after joining the team.

## GitHub collaboration procedure

1. Push the clean repository to a public GitHub repository.
2. Add collaborators under repository **Settings → Collaborators**.
3. Protect `main` when possible:
   - require pull requests;
   - require the Capstone CI check;
   - require one approval;
   - block force pushes.
4. Use issues for tasks and branches for changes.
5. Credit material contributions in the final writeup and video description.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the branch, review, test, and
documentation workflow.

## Final credits block

Before Kaggle submission, add the confirmed team roster to the writeup using:

```markdown
## Team

- **Full name** — Kaggle profile · GitHub handle · Specific contribution
- **Full name** — Kaggle profile · GitHub handle · Specific contribution
```

Do not publish private email addresses. Every listed contribution must be
accurate and agreed by the team.
