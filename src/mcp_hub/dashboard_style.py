from __future__ import annotations

DASHBOARD_CSS = """
    :root {
      color-scheme: light;
      --ink: #111111;
      --paper: #fffdf2;
      --surface: #ffffff;
      --muted: #4b5563;
      --line: #111111;
      --yellow: #ffd400;
      --cyan: #00c2ff;
      --pink: #ff4f79;
      --green: #35d07f;
      --orange: #ff9f1c;
      --shadow: 7px 7px 0 #111111;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      background:
        linear-gradient(90deg, rgba(17, 17, 17, .06) 1px, transparent 1px),
        linear-gradient(rgba(17, 17, 17, .06) 1px, transparent 1px),
        var(--paper);
      background-size: 22px 22px;
      color: var(--ink);
      font-family: Segoe UI, Arial, sans-serif;
      font-size: 14px;
    }
    main {
      max-width: 1480px;
      margin: 0 auto;
      padding: 22px;
    }
    header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
      padding: 18px;
      background: var(--cyan);
      border: 4px solid var(--line);
      box-shadow: var(--shadow);
    }
    h1 {
      font-size: 30px;
      line-height: 1;
      margin: 0 0 8px;
      letter-spacing: 0;
    }
    h2 {
      display: inline-block;
      font-size: 17px;
      margin: 26px 0 12px;
      padding: 7px 10px;
      background: var(--yellow);
      border: 3px solid var(--line);
      box-shadow: 4px 4px 0 var(--line);
    }
    p {
      margin: 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--surface);
      border: 4px solid var(--line);
      box-shadow: var(--shadow);
    }
    th, td {
      border: 3px solid var(--line);
      padding: 10px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: var(--ink);
      color: var(--paper);
      font-size: 12px;
      text-transform: uppercase;
    }
    code, pre {
      background: #f7f7f7;
      border: 3px solid var(--line);
      border-radius: 0;
      font-family: Consolas, monospace;
    }
    code {
      padding: 1px 5px;
      box-decoration-break: clone;
    }
    pre {
      min-width: 260px;
      max-width: 430px;
      max-height: 230px;
      margin: 0;
      padding: 9px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      box-shadow: 4px 4px 0 var(--line);
    }
    button {
      min-width: 84px;
      min-height: 32px;
      border: 3px solid var(--line);
      border-radius: 0;
      background: var(--surface);
      color: var(--ink);
      cursor: pointer;
      font-weight: 700;
      box-shadow: 4px 4px 0 var(--line);
    }
    button:hover {
      transform: translate(2px, 2px);
      box-shadow: 2px 2px 0 var(--line);
    }
    button.primary {
      background: var(--pink);
      color: var(--ink);
    }
    form {
      display: inline-block;
      margin: 0 7px 7px 0;
    }
    .muted {
      color: var(--muted);
      font-weight: 600;
    }
    .status {
      display: inline-block;
      min-width: 82px;
      padding: 5px 7px;
      border: 3px solid var(--line);
      font-weight: 800;
      text-align: center;
      box-shadow: 3px 3px 0 var(--line);
    }
    .ready, .running {
      background: var(--green);
      color: var(--ink);
    }
    .invalid {
      background: var(--pink);
      color: var(--ink);
    }
    .stopped, .unknown {
      background: var(--orange);
      color: var(--ink);
    }
    .errors {
      color: var(--ink);
      margin: 0;
      padding-left: 18px;
    }
    .errors li {
      margin-bottom: 5px;
      background: var(--pink);
      border: 2px solid var(--line);
      padding: 4px;
    }
    .empty {
      color: var(--muted);
      font-weight: 700;
    }
    .service-name {
      font-size: 15px;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }
    .meta-block {
      background: var(--surface);
      border: 4px solid var(--line);
      box-shadow: var(--shadow);
      padding: 14px;
    }
    @media (max-width: 860px) {
      main {
        padding: 12px;
      }
      header {
        align-items: stretch;
        flex-direction: column;
      }
      table {
        display: block;
        overflow-x: auto;
      }
    }
"""
