# Detailed Blog Publishing Guide

## Recommended publishing plan

Publish the detailed article on **DEV Community first**, then use the shorter
LinkedIn post to distribute it. This gives the technical article a developer
audience and a stable public URL while keeping the LinkedIn launch concise.

| Platform | Best use | Important format details |
|---|---|---|
| **DEV Community — recommended** | Primary technical article and canonical URL | Markdown with Jekyll front matter; up to four tags; recommended cover size is 1000 × 420 |
| **Hashnode** | Secondary developer distribution or a personal engineering blog | Markdown/WYSIWYG editor, SEO title and description, canonical/original URL support; recommended cover is 1200 × 630 |
| **LinkedIn Article** | Long-form access for an existing professional network | Articles support up to 125,000 characters; use the short LinkedIn post for stronger feed distribution |

Official publishing references:

- [DEV Editor Guide](https://dev.to/p/editor_guide/)
- [Hashnode: Writing a Blog Post](https://docs.hashnode.com/blogs/editor/writing-a-blog-post)
- [LinkedIn posts vs. articles](https://www.linkedin.com/help/linkedin/answer/a522483)
- [Qwen Cloud Hackathon official rules](https://qwencloud-hackathon.devpost.com/rules)

## Publish on DEV Community

1. Sign in or create an account at [dev.to](https://dev.to/).
2. Open **Create Post** and switch to the Markdown editor if prompted.
3. Copy all of [`detailed_blog_post.md`](detailed_blog_post.md), including the
   front matter at the top.
4. Upload a clean product cover image. Use a 1000 × 420 image with the title
   “AI Agents Need Memory Governance” and a small “MemoPilot IQ” subtitle. Do
   not use cloud-console screenshots or any image containing credentials.
5. Keep the architecture diagram in the body. Its public GitHub URL is already
   embedded in the article.
6. Preview on desktop and mobile. Check that the diagram, JSON, scoring formula,
   lists, and repository link render correctly.
7. Add or confirm these four tags: `ai`, `agents`, `qwen`, `opensource`.
8. Leave `published: false` while reviewing. When everything is ready, change
   it to `published: true` or use DEV's Publish control.
9. Open the published URL in a signed-out/private window and save the URL.

## Distribute through LinkedIn

1. Publish the DEV article first so its final URL exists.
2. In [`blog_post.md`](blog_post.md), add this line immediately before the
   repository link:

   ```text
   Full build story: YOUR_DEV_ARTICLE_URL
   ```

   The current LinkedIn draft has enough space for a normal DEV article URL,
   but confirm the final text remains below LinkedIn's 3,000-character limit.
3. Attach media in this order:
   - Memory Trace screenshot showing a planned Next.js migration and the
     superseded frontend preference;
   - the architecture diagram;
   - timeline or graph view showing the supersession relationship.
4. Set visibility to **Anyone** and publish.
5. Check both links from a signed-out/private window.

Do not publish the same full article independently on several platforms at the
same time. Concentrate comments and traffic on the DEV article. If it is later
republished on Hashnode, set the DEV URL as the original/canonical URL.

## Submit the bonus entry on Devpost

The official rules require the blog or social post to be public, relevant to
the hackathon and project, and linked from an eligible Devpost submission.

1. Open the MemoPilot IQ submission on the Qwen Cloud hackathon Devpost page.
2. Find the optional **Blog or Social Post** URL field.
3. Add the public DEV article URL. If the form accepts only one URL, use the
   detailed DEV article; it is the strongest evidence for the “thoroughness and
   potential impact” judging criterion.
4. Include the LinkedIn post URL in the project description or other relevant
   links section if Devpost permits it.
5. Save the submission, reopen it, and verify both URLs.

## Final editorial and evidence check

Before publishing, confirm all of the following:

- The author name and profile are professional and recognizable.
- The cover and screenshots contain no API keys, account IDs, email addresses,
  private URLs, or cloud billing information.
- The GitHub repository is public and shows the latest `main` commit.
- The architecture image renders from its public GitHub URL.
- Local validation is described as local validation.
- Alibaba Cloud deployment and final model-backed results are not described as
  complete until public evidence exists.
- Any metrics added later link to a report produced by the exact submitted
  commit.
- The article and LinkedIn post are public and open while signed out.
- The DEV article URL is saved in the Devpost submission before the deadline.

## Suggested SEO and sharing copy

**SEO title**

> AI Agent Memory Governance with Qwen Cloud | MemoPilot IQ

**SEO description**

> How MemoPilot IQ structures, retrieves, supersedes, and explains persistent
> AI memory using Qwen Cloud, hybrid retrieval, and a strict context budget.

**Short share text**

> I built MemoPilot IQ to explore a hard agent problem: remembering is useful,
> but stale or ungoverned memory can make an AI confidently wrong. Here is the
> architecture, lifecycle design, and evaluation journey behind it: [URL]
