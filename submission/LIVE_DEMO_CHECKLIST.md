# Live Demo Deployment Checklist

## Recommended deployment

Use Google Cloud Run because it runs the same Docker image verified locally and
supports the Full ADK + MCP runtime.

For the public judging deployment:

- enable `ALLOW_GUEST_DEMO=true`;
- keep `APP_ENV=production`;
- store `GOOGLE_API_KEY` and bootstrap admin credentials in Secret Manager;
- do not place any secret in GitHub or Cloud Build YAML;
- expose the **Explore Sample Workspace** path without login;
- use only the public Northstar Retail sample in the judge flow.

## Pre-publication checks

1. Open the Cloud Run URL in an incognito browser.
2. Confirm the logo, InsightHive browser title, and guest entry.
3. Load Northstar Retail.
4. Confirm Runtime displays **Full ADK**.
5. Run one mission and confirm tools/trace populate.
6. Verify MCP and memory proof.
7. Confirm no admin credential is displayed.
8. Test desktop and 1366×768 layouts.
9. Record the exact deployment command and region.
10. Add the URL to README, writeup, YouTube description, and Kaggle project.

## Demo resilience

- Run the mission once before recording to warm the container.
- Use a fresh Gemini project/quota window.
- Keep the final evaluation JSON and screenshots ready as backup.
- Do not rebuild Docker during the video.
- If Gemini quota is exhausted, wait for reset or replace the private key and
  recreate the container; never expose the key.

