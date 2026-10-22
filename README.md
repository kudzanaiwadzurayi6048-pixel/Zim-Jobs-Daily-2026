# Zim Jobs Daily — automatic job-feed update kit

This package adds a scheduled official-portal link discovery process to the static website.

## What updates automatically

- A GitHub Actions workflow runs once per day and can also be run manually.
- `scripts/refresh_jobs.py` checks the official PSC, ZINARA and City of Harare career pages.
- It keeps existing listings whose explicit deadline has not passed, removes listings whose explicit deadline is past, and discovers additional same-domain vacancy/career links.
- Newly discovered links are labelled **Auto-discovered · verify notice** and do not get invented deadlines, salaries or contact details.
- The website loads `jobs.json` when hosted over HTTP/HTTPS, merges the feed with its built-in fallback data, and keeps search/save/share working.

## Publish with GitHub Pages

1. Create a GitHub repository, for example `zim-jobs-daily`.
2. Upload **all** files from this folder, preserving the `.github/workflows/` and `scripts/` folders.
3. In the repository, open **Settings → Pages** and publish from the `main` branch and `/ (root)`.
4. After publishing, open the GitHub Pages site and check the job feed. `index.html` and `jobs.json` must be in the same published root.
5. Open **Actions** and run **Refresh official job links** once manually. If GitHub asks, enable Actions and allow workflow write permissions under **Settings → Actions → General → Workflow permissions**.
6. The workflow then runs daily. Changes to `jobs.json` are committed by the workflow bot.

## Important limitations

- This is link discovery, not a guaranteed source API. Employer websites may block automation, change page layouts, use JavaScript-only job boards, or expose only the careers landing page.
- New scraped links are candidates, not confirmed live vacancies. Review them periodically and remove irrelevant results.
- A link can remain on an official portal after a job closes. The original employer notice is authoritative.
- Some hosting providers block cross-origin requests. Host `index.html` and `jobs.json` in the same directory/domain.
- The first run requires you to publish the package to a GitHub repository and enable Actions; the files cannot schedule themselves while sitting on a phone or local computer.

## Files

- `index.html` — website with feed loading and fallback listings
- `jobs.json` — current job feed
- `scripts/refresh_jobs.py` — official-page link discovery and expiry cleanup
- `.github/workflows/refresh-jobs.yml` — daily scheduled workflow
