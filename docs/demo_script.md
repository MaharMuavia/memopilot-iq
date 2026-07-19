# Demo Video Script (target: 2 minutes 40 seconds)

**Demo link:** [Watch on YouTube](https://youtu.be/UE2h4K_VaL8).

Record only the public Alibaba deployment at
[https://47-84-129-218.sslip.io/app](https://47-84-129-218.sslip.io/app). Use a fresh browser, zoom
to 90% if needed, hide bookmarks/notifications, and never show `.env` files,
cloud-console pages, API keys, or account identifiers.

Before recording:

1. Open the public URL and confirm the header says **Alibaba Cloud**, **Qwen
   Online**, and **Alibaba Store**.
2. Dry-run the four guided Chat steps in a separate private window. If any turn
   says **Qwen Fallback**, stop and retry later.
3. Close that window, then open a new private window for recording. This gives
   the signed anonymous demo a clean server-issued namespace. Keep the mouse
   near the next button and close unrelated browser tabs.

| Time | On screen | Narration |
|---|---|---|
| 0:00-0:15 | Header and Chat dashboard | "AI agents do not need unlimited memory. They need governed memory. MemoPilot IQ turns conversations into persistent, explainable decisions." |
| 0:15-0:30 | Point to the HTTPS URL and three status badges; briefly open **Settings** to show the build SHA | "This is the public Alibaba Cloud deployment. Qwen is online, Tablestore is the active memory store, the backend runs on ECS, and the exact revision is visible." |
| 0:30-0:50 | Return to Chat and click **Run step 1** | "This is a live Qwen request. I save my stack, response style, cloud choice, and the critical rule never to commit API keys." |
| 0:50-1:10 | Creation badges, then **Run step 2** | "Qwen extracts structured memories. In a new session, MemoPilot recalls the relevant FastAPI and Alibaba preferences to design the backend." |
| 1:10-1:30 | Qwen architecture answer and Memory Trace | "The trace exposes every injected memory, score, reason, and token cost. Unrelated candidates are rejected before they reach Qwen." |
| 1:30-1:50 | **Run step 3** | "I change the future frontend plan. MemoPilot creates the Next.js decision and supersedes the older preference without deleting its audit history." |
| 1:50-2:10 | **Run step 4** and final answer | "The final answer separates reality from intent: this submitted build is React 18 with Vite; Next.js is only the planned next iteration." |
| 2:10-2:25 | Open **Timeline** or **Graph** | "The lifecycle stays auditable through the timeline, graph, controls, analytics, and Memory Trace." |
| 2:25-2:40 | Open **Evaluation**; point to the committed report | "On 24 Qwen scenarios, governed memory reached 100 percent accuracy and context recall, with zero stale-memory errors and 21 percent fewer history tokens." |
| 2:40-2:50 | Return to header | "MemoPilot IQ is reusable memory-governance infrastructure for trustworthy long-running agents, built with Qwen Cloud and Alibaba Cloud." |

## Recording acceptance check

- Duration is below 3:00.
- The public URL is visible at least once.
- The Alibaba Cloud, Qwen Online, and Alibaba Store badges are readable.
- Memory creation, recall, supersession, and the final current-versus-planned
  answer are visible.
- No fallback warning, credential, private console, desktop notification, or
  copyrighted music appears.
- Upload to YouTube, Vimeo, or Facebook Video as **Public**, then test the link
  while signed out.
