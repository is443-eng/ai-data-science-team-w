# Process diagrams (Mermaid)

## File to use for your report

| File | Use |
|------|-----|
| **[`architecture.mmd`](architecture.mmd)** | **Primary** — full data layer, risk model, Streamlit UI, and **five-agent** orchestration with parallel phases. |

## How to export to PNG / SVG

1. **Mermaid Live (quickest)**  
   - Open [https://mermaid.live](https://mermaid.live).  
   - Paste **one** diagram only: from `flowchart TB` through the last line (`A5 --> Ov`). If you paste the block twice, or lose newlines, you may see a parse error like `Oflowchart` (two diagrams glued together).  
   - Leading `%%` lines are comments; you can delete them if the editor complains.  
   - Use **Actions → Export** for PNG or SVG.

2. **Mermaid CLI** (from repo root or `Tool V3/docs/diagrams/`):

   ```bash
   cd "Tool V3/docs/diagrams"
   npx --yes @mermaid-js/mermaid-cli -i architecture.mmd -o architecture.png
   ```

   SVG: add `-o architecture.svg`.

3. **VS Code / Cursor**  
   Install a Mermaid preview extension and export from the preview if supported.

## Same diagram in the docs

The **same graph** is embedded in **[`../ARCHITECTURE.md`](../ARCHITECTURE.md)** as a fenced `mermaid` code block (GitHub and many Markdown renderers draw it automatically).
