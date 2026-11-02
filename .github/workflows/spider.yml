name: Generate spider

on:
  schedule:
    - cron: "0 4 * * *"   # 04:00 UTC = 06:00 in Johannesburg, every day
  workflow_dispatch:       # adds a "Run workflow" button in the Actions tab

permissions:
  contents: write          # lets the workflow commit the generated SVG

jobs:
  spider:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repo
        uses: actions/checkout@v4

      - name: Generate the spider SVG
        run: python3 generate_spider.py
        env:
          GH_USER: ${{ github.repository_owner }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Commit the SVG if it changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add dist/spider.svg
          git diff --staged --quiet || (git commit -m "Update spider animation" && git push)
