/**
 * Room Thermostat — the page.
 *
 * One file, one shadow root, no build step, in the slab language NSPanel
 * Companion is drawn in: the two integrations are one system and should look
 * like it. The stylesheet below is ported from that page, minus the screens
 * this one does not have.
 *
 * Two rules of that stylesheet, copied here because breaking either wrecks
 * the look and neither is obvious:
 *
 *   1. A border is ALWAYS var(--line), never var(--accent). Accent means
 *      "this is the thing you selected", and is permitted on exactly four
 *      things: a primary button fill, the inset bar of the ONE selected row,
 *      the underline of the ONE active tab, and a focus ring.
 *   2. Accent as text is var(--accent-ink), never var(--accent).
 */

const FONT_FACES = `/* Barlow and Roboto Mono are what the design and the page are drawn in.
   They are served from this integration rather than from Google Fonts:
   plenty of Home Assistant installs cannot reach the internet, and the one
   that can should not be telling a third party who is looking at its admin
   page. Without these the page fell back to system-ui, which is why it did
   not look like the design. */
@font-face { font-family:Barlow; font-style:normal; font-weight:400; font-display:swap;
  src:url('/room_thermostat/frontend/fonts/barlow-400.woff2') format('woff2'); }
@font-face { font-family:Barlow; font-style:normal; font-weight:500; font-display:swap;
  src:url('/room_thermostat/frontend/fonts/barlow-500.woff2') format('woff2'); }
@font-face { font-family:Barlow; font-style:normal; font-weight:600; font-display:swap;
  src:url('/room_thermostat/frontend/fonts/barlow-600.woff2') format('woff2'); }
@font-face { font-family:Barlow; font-style:normal; font-weight:700; font-display:swap;
  src:url('/room_thermostat/frontend/fonts/barlow-700.woff2') format('woff2'); }
/* One variable file covers the two weights the mono role uses. Latin only:
   it sets identifiers, which are ASCII. */
@font-face { font-family:'Roboto Mono'; font-style:normal; font-weight:400 500; font-display:swap;
  src:url('/room_thermostat/frontend/fonts/roboto-mono-latin.woff2') format('woff2');
  unicode-range:U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC,
    U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }`;

const installFonts = () => {
  const id = "room-thermostat-fonts";
  if (document.getElementById(id)) return;
  const style = document.createElement("style");
  style.id = id;
  style.textContent = FONT_FACES;
  document.head.appendChild(style);
};


const STYLES = `
/* ============================================================
   SLAB ADMIN — complete stylesheet for the NSPanel Companion
   Home Assistant add-on UI.

   One file. Paste the whole thing into the STYLES template
   literal in frontend/nspanel-companion-panel.js (shadow DOM),
   or ship it as a stylesheet and adopt it:

     const sheet = new CSSStyleSheet();
     sheet.replaceSync(SLAB_ADMIN_CSS);
     this.shadowRoot.adoptedStyleSheets = [sheet];

   Contents
     1  Tokens — colour, geometry, type
     2  Reset and base
     3  Typography roles
     4  Controls — buttons, fields, toggles, checks
     5  Bands, rows, lists
     6  Status pills and notices
     7  Chrome — app bar, breadcrumb, tabs, save bar
     8  Home — status strip, panel grid, empty state
     9  Integrations route
    10  Workspace — general, doorbell, diagnostics
    11  Page editor — rail, board, inspector
    12  Pickers — entity, icon, add component
    13  Dialogs
    14  Utilities and responsive

   Rules this encodes: separation is a 1px rule, not a gap;
   state is a fill, never an outline colour; identifiers are
   monospace; destructive is red and on the right; every
   interactive element has a visible focus ring.

   TWO RULES THAT ARE EASY TO BREAK AND WRECK THE UI

   1. A border is ALWAYS var(--line). Never var(--accent).
      Accent means "this is the thing you selected" and nothing
      else. An accent rule on a list divider or an Add button
      makes the least important element the loudest on screen.
      Accent is permitted on exactly four things: a primary
      button fill, the 3px inset bar of the ONE selected row,
      the 2px underline of the ONE active tab, and a focus ring.

   2. Accent as text is var(--accent-ink), never var(--accent).
   ============================================================ */


/* 1 ── TOKENS ─────────────────────────────────────────────── */

:host {
  /* surface — four steps, each visibly apart at arm's length.
     The panel could collapse these because one screen showed one
     thing at a time; a three-column app cannot. */
  --canvas:#0E1012;
  --surface:#171B1F;
  --surface-raised:#242B33;
  --accent-wash:#33200F;

  /* ink */
  --ink:#F2F5F7;
  --muted:#949CA3;
  --disabled:#4A5158;
  --line:#2F373E;

  /* accent and status */
  --accent:#F36D21;
  --accent-ink:#FF9455;   /* accent as TEXT. --accent is for FILLS only:
                             #F36D21 on --accent-wash is 2.6:1, unreadable. */
  --on-accent:#0E1012;
  --danger:#D24A3F;
  --ok:#34C759;
  --pending:#FF9500;
  --ok-wash:#12301E;
  --danger-wash:#2E1512;

  /* geometry */
  --radius:2px;
  --row:40px;
  --row-tall:56px;
  --control:36px;
  --control-sm:28px;
  --app-bar:56px;
  --tab-bar:44px;
  --pane-inset:20px;
  --page-inset:32px;
  --rail:232px;
  --inspector:340px;
  --content-max:1180px;
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:20px; --s6:32px;

  /* type */
  --font:Barlow,system-ui,-apple-system,sans-serif;
  --mono:'Roboto Mono',ui-monospace,SFMono-Regular,monospace;

  display:block;
  min-height:100%;
  background:var(--canvas);
  color:var(--ink);
  font-family:var(--font);
  font-size:14px;
  font-variant-numeric:tabular-nums;
}

:host(.light) {
  --canvas:#EFF1EE;
  --surface:#FFFFFF;
  --surface-raised:#E4E7E2;
  --accent-wash:#FFE4D4;
  --ink:#14171A;
  --muted:#636A65;
  --disabled:#A8ADA6;
  --line:#C7CCC6;
  --accent-ink:#C9560F;
  --on-accent:#FFFFFF;
  --danger:#C0392B;
  --ok-wash:#DFF7EB;
  --ok:#147A4D;
  --danger-wash:#FDE7E4;
}


/* 2 ── RESET AND BASE ─────────────────────────────────────── */

*, *::before, *::after { box-sizing:border-box; }
h1,h2,h3,h4,p,dl,dd,figure { margin:0; }
a { color:var(--accent-ink); text-decoration:none; }
a:hover { text-decoration:underline; }
code, .mono, .id { font:500 12px/1.4 var(--mono); }
hr { border:0; border-top:1px solid var(--line); margin:0; }
::-webkit-scrollbar { width:10px; height:10px; }
::-webkit-scrollbar-thumb { background:var(--surface-raised); }
::-webkit-scrollbar-track { background:transparent; }

main { max-width:none; margin:0; padding:0; }
main.wide { max-width:none; }


/* 3 ── TYPOGRAPHY ROLES ───────────────────────────────────── */

.t-page   { font:700 30px/1.1 var(--font); }
.t-title  { font:700 22px/1.2 var(--font); }
.t-sub    { font:600 17px/1.3 var(--font); }
.t-read   { font:700 20px/1.2 var(--font); }
.t-body   { font:400 14px/1.5 var(--font); }
.t-small  { font:400 13px/1.5 var(--font); color:var(--muted); }
.t-control{ font:600 14px/1 var(--font); }
.t-label  { font:600 11px/1 var(--font); letter-spacing:.12em; text-transform:uppercase; color:var(--muted); }
.t-micro  { font:400 11px/1.4 var(--font); color:var(--muted); }
.t-mono   { font:500 12px/1.4 var(--mono); }

.t-label.accent { color:var(--accent-ink); }
.t-label.danger { color:var(--danger); }
.section-label { font:600 11px/1 var(--font); letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin-bottom:10px; display:block; }
.section-label + .band { margin-top:0; }
.stack { display:flex; flex-direction:column; gap:26px; }


/* 4 ── CONTROLS ───────────────────────────────────────────── */

button {
  height:var(--control); padding:0 var(--s4);
  display:inline-flex; align-items:center; justify-content:center; gap:var(--s2);
  border:1px solid var(--line); border-radius:var(--radius);
  background:var(--surface-raised); color:var(--ink);
  font:600 14px/1 var(--font); cursor:pointer;
  white-space:nowrap;
}
button:hover { background:var(--line); }
button:active { transform:translateY(1px); }
button.primary { background:var(--accent); border-color:var(--accent); color:var(--on-accent); }
button.primary:hover { filter:brightness(1.08); background:var(--accent); }
button.danger { background:var(--danger); border-color:var(--danger); color:var(--on-accent); font-weight:700; }
button.danger.quiet { background:transparent; border-color:var(--line); color:var(--danger); font-weight:600; }
button.quiet { background:transparent; border-color:transparent; color:var(--muted); }
button.quiet:hover { background:var(--surface-raised); color:var(--ink); }
button.small { height:var(--control-sm); padding:0 var(--s3); font-size:13px; }
button.icon { width:var(--control); padding:0; font-size:16px; }
button:disabled, button[disabled] {
  background:var(--surface); color:var(--disabled); border-color:var(--line);
  cursor:default; transform:none; filter:none;
}

input, select, textarea {
  height:var(--control); width:100%; padding:0 var(--s3);
  border:1px solid var(--line); border-radius:var(--radius);
  background:var(--canvas); color:var(--ink);
  font:400 14px/1 var(--font);
}
textarea { height:auto; padding:10px var(--s3); line-height:1.5; resize:vertical; }
input::placeholder { color:var(--disabled); }
input[readonly] { color:var(--muted); }
input.mono, select.mono, .pair-code { font:500 13px/1 var(--mono); }
.pair-code.entry { height:64px; font-size:30px; letter-spacing:.3em; text-indent:.3em; text-align:center; }
select { appearance:none; padding-right:30px; background-image:linear-gradient(transparent,transparent); }
.select-wrap { position:relative; }
.select-wrap::after { content:'▾'; position:absolute; right:12px; top:50%; transform:translateY(-50%); color:var(--muted); pointer-events:none; }

:is(button,input,select,textarea,a,[tabindex],.slot,.row):focus-visible {
  outline:2px solid var(--accent); outline-offset:1px;
}

/* toggle */
.toggle { flex:none; width:36px; height:20px; border:0; padding:0; border-radius:999px; background:var(--line); position:relative; cursor:pointer; }
.toggle::after { content:''; position:absolute; left:2px; top:2px; width:16px; height:16px; border-radius:50%; background:var(--muted); transition:left .12s, background .12s; }
.toggle[aria-checked="true"] { background:var(--accent); }
.toggle[aria-checked="true"]::after { left:18px; background:var(--on-accent); }
.toggle:hover { background:var(--disabled); }
.toggle[aria-checked="true"]:hover { background:var(--accent); filter:brightness(1.08); }

/* check and radio */
.check { display:flex; align-items:center; gap:10px; font:400 14px/1 var(--font); cursor:pointer; }
.check input[type=checkbox], .check input[type=radio] { appearance:none; flex:none; width:16px; height:16px; margin:0; border:1px solid var(--disabled); border-radius:var(--radius); background:transparent; cursor:pointer; }
.check input[type=radio] { border-radius:50%; }
.check input[type=checkbox]:checked { background:var(--accent); border-color:var(--accent); }
.check input[type=checkbox]:checked::after { content:'✓'; display:block; color:var(--on-accent); font:700 12px/14px var(--font); text-align:center; }
.check input[type=radio]:checked { border:4px solid var(--accent); }

/* field group: label above control, hint below */
.field { display:flex; flex-direction:column; gap:6px; }
.field > .label { font:600 12px/1 var(--font); color:var(--muted); }
.field > .hint { font:400 12px/1.5 var(--font); color:var(--muted); }
.field .optional { font-weight:400; color:var(--disabled); }
.preset-row { display:flex; gap:var(--s2); }
.preset-row input { text-align:center; font:500 13px/1 var(--mono); }


/* 5 ── BANDS, ROWS, LISTS ─────────────────────────────────── */

.band { border:1px solid var(--line); background:transparent; }
.band > * + * { border-top:1px solid var(--line); }
.band.flush { border-left:0; border-right:0; }

.row { min-height:var(--row); display:flex; align-items:center; gap:var(--s3); padding:0 var(--s4); }
.row.tall { min-height:var(--row-tall); }
.row.stacked { flex-direction:column; align-items:stretch; justify-content:center; gap:2px; padding-top:10px; padding-bottom:10px; }
.row > .grow { flex:1; min-width:0; }
.row .sub { font:400 13px/1.4 var(--font); color:var(--muted); margin-top:2px; }
.row.interactive { cursor:pointer; }
.row.interactive:hover { background:var(--surface-raised); }
.row.selected { background:var(--accent-wash); box-shadow:inset 3px 0 0 var(--accent); }
.row.selected .index { color:var(--accent-ink); }
.row .index { font:500 12px/1 var(--mono); color:var(--muted); flex:none; }
.row .drag { color:var(--disabled); cursor:grab; font-size:14px; }
.row .drag:active { cursor:grabbing; }
.row.dragging { opacity:.45; }
.row.drop-target { box-shadow:inset 0 -2px 0 var(--accent); }
.row .chev { color:var(--muted); }

/* key/value table */
.kv { border:1px solid var(--line); }
.kv > div { min-height:var(--row); display:flex; align-items:center; gap:var(--s4); padding:0 var(--s4); font-size:14px; }
.kv > div + div { border-top:1px solid var(--line); }
.kv dt, .kv .k { flex:1; color:var(--muted); }
.kv dd, .kv .v { margin:0; text-align:right; overflow-wrap:anywhere; }


/* 6 ── STATUS AND NOTICES ─────────────────────────────────── */

.status { flex:none; padding:5px 10px; border-radius:999px; font:600 11px/1 var(--font); letter-spacing:.12em; text-transform:uppercase; }
.status.online   { background:var(--ok-wash); color:var(--ok); }
.status.waiting  { background:var(--accent-wash); color:var(--pending); }
.status.offline  { background:var(--surface-raised); color:var(--muted); }
.status.error    { background:var(--danger-wash); color:var(--danger); }
/* Something published that this house is not running. Accent, because it is
   worth noticing and is not a fault. */
.status.update   { background:var(--accent-wash); color:var(--accent-ink); }
.release-notice .sub { font:400 13px/1.5 var(--font); color:var(--muted); margin-top:2px; }
.release-notice a { color:var(--accent-ink); text-decoration:none; white-space:nowrap; }

.dot { flex:none; width:8px; height:8px; border-radius:50%; background:var(--disabled); }
.dot.on { background:var(--ok); }
.dot.warn { background:var(--pending); }
.dot.off { background:var(--disabled); }

.notice { padding:12px var(--s4); border:1px solid var(--line); background:var(--accent-wash); font:400 13px/1.5 var(--font); }
.notice.error { background:var(--danger-wash); border-color:var(--danger); color:var(--ink); }
.notice.plain { background:var(--surface); }

.empty { border:1px solid var(--line); padding:56px var(--page-inset); display:flex; flex-direction:column; align-items:center; gap:10px; text-align:center; }
.empty .glyph { width:40px; height:40px; display:grid; place-items:center; border-radius:var(--radius); background:var(--accent-wash); color:var(--accent-ink); font-size:20px; }
.empty p { max-width:340px; font:400 14px/1.5 var(--font); color:var(--muted); }

.device-icon { flex:none; width:40px; height:40px; display:grid; place-items:center; border-radius:var(--radius); background:var(--surface-raised); color:var(--muted); font-size:20px; }
.device-icon.active { background:var(--accent-wash); color:var(--accent-ink); }
.device-icon.small { width:32px; height:32px; font-size:16px; }


/* 7 ── CHROME ─────────────────────────────────────────────── */

/* The phone's status bar is drawn over the top of the page in the Home
   Assistant app, so the bar begins below it rather than under it. The inset
   is zero everywhere else, which leaves this exactly as it was. */
.app-bar { min-height:var(--app-bar); display:flex; align-items:center; gap:var(--s3);
  padding:env(safe-area-inset-top, 0px) var(--page-inset) 0; border-bottom:1px solid var(--line); }
.app-bar .mark { width:8px; height:8px; background:var(--accent); flex:none; }
.app-bar .spacer, .save-bar .spacer { flex:1; }

.crumbs { display:flex; align-items:center; gap:var(--s2); font:400 13px/1 var(--font); color:var(--muted); }
.crumbs .sep { color:var(--disabled); }
.crumbs .here { font:700 15px/1 var(--font); color:var(--ink); }
.crumbs .back { height:28px; padding:0 var(--s3); }

.tabs { height:var(--tab-bar); display:flex; padding:0 var(--page-inset); border-bottom:1px solid var(--line); overflow-x:auto; }
.tabs button { height:100%; border:0; border-radius:0; background:transparent; color:var(--muted); padding:0 var(--s4); }
.tabs button:hover { background:transparent; color:var(--ink); }
.tabs button.active { color:var(--ink); box-shadow:inset 0 -2px 0 var(--accent); }
/* The bar scrolls horizontally, and a scroller clips in both directions: the
   global ring sits 1px outside its button, so a focused tab lost its top and
   bottom edge. This one is drawn inside the tab instead. */
.tabs button:focus-visible { outline-offset:-2px; }

/* the only thing that writes */
.save-state { font:400 13px/1 var(--font); color:var(--muted); }
.save-state.dirty { color:var(--accent-ink); }


/* ============================================================
   8 ── THE THERMOSTAT MODULE
   Drawn to Thermostat Module.dc.html. The design's own values are
   kept, expressed through the tokens above where they agree.
   ============================================================ */

.page { padding:32px; max-width:1180px; margin:0 auto; }
/* The history page is a column of blocks 26px apart, not a stack of elements
   carrying their own margins. */
.page.stack { display:flex; flex-direction:column; gap:26px; }
/* Inside a column the gap already separates the heading from the first
   group; its own margin would add to it. */
.page.stack .page-head, .column .page-head { margin-bottom:0; }
.page-head h1 { font:700 30px/1.1 var(--font); margin:0; }
.page-head p { font:400 14px/1.5 var(--font); color:var(--muted); margin-top:4px; max-width:720px; }
.page-head { display:flex; align-items:flex-end; gap:20px; margin-bottom:20px; }
.page-head .grow { flex:1; }

/* Two columns: the settings, and what is true right now. */
.split { display:grid; grid-template-columns:minmax(0,1fr) 340px; gap:32px; align-items:start; }
.column { display:flex; flex-direction:column; gap:26px; min-width:0; }

/* A group of settings under a label, separated by rules rather than gaps. */
.group > .label { font:600 11px/1 var(--font); letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); margin-bottom:10px; }
.group .rows { border:1px solid var(--line); }
.row-setting { min-height:56px; display:flex; align-items:center; gap:16px; padding:12px 16px; }
.row-setting + .row-setting { border-top:1px solid var(--line); }
.row-setting .what { flex:1; min-width:0; }
.row-setting .name { font:400 14px/1.4 var(--font); }
.row-setting .name .optional { color:var(--disabled); }
.row-setting .entity { font:500 12px/1.45 var(--mono); color:var(--muted); margin-top:2px;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.row-setting .entity.none { font:400 13px/1.4 var(--font); color:var(--disabled); }
.row-setting .why { font:400 13px/1.5 var(--font); color:var(--muted); margin-top:6px; max-width:560px; }
.row-setting .control { flex:none; display:flex; align-items:center; gap:8px; }
.row-setting input[type=text], .row-setting input[type=number] { height:36px; width:96px;
  padding:0 12px; font:500 13px/1 var(--mono); text-align:center; }
.row-setting input.wide { width:220px; text-align:left; font:400 14px/1 var(--font); }
/* One width for every unit, so the inputs above and below each other line
   up. The design sizes each to its own word — "hours" is twice "K" — which
   leaves the column ragged. */
.row-setting .unit { font:400 13px/1 var(--font); color:var(--muted);
  width:44px; flex:none; }
.row-setting .select-wrap { flex:0 0 260px; }

/* Rooms */
.room-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(min(100%,360px),1fr));
  border:1px solid var(--line); }
/* Shared rules rather than gaps: the grid is one object, not nine cards. */
.room-cell { border-left:1px solid var(--line); border-top:1px solid var(--line);
  margin:-1px 0 0 -1px; padding:20px; display:flex; flex-direction:column; gap:16px;
  min-height:236px; min-width:0; }
.room-cell .head { display:flex; align-items:flex-start; gap:14px; }
.room-icon { flex:none; width:40px; height:40px; display:grid; place-items:center;
  border-radius:var(--radius); }
.room-cell .naming { flex:1; min-width:0; }
.room-cell .naming b { font:600 17px/1.3 var(--font); display:block; }
.room-cell .naming small { font:500 12px/1.45 var(--mono); color:var(--muted); margin-top:3px;
  display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pill { flex:none; padding:5px 10px; border-radius:999px; font:600 11px/1 var(--font);
  letter-spacing:.12em; text-transform:uppercase; }
.reading { display:flex; align-items:baseline; gap:7px; }
.reading b { font:700 30px/1 var(--font); letter-spacing:-.01em; }
.reading .unit { font:600 15px/1; color:var(--muted); }
.reading .hum { font:400 13px/1; color:var(--muted); margin-left:8px; }
.room-cell .controls { border:1px solid var(--line); }
.control-row { min-height:40px; display:flex; align-items:center; gap:12px; padding:0 16px; }
.control-row + .control-row { border-top:1px solid var(--line); }
.control-row .what { flex:1; min-width:0; font:400 14px/1.4 var(--font); color:var(--muted); }
.control-row .select-wrap { flex:0 0 132px; }
.control-row select { height:28px; font:400 13px/1 var(--font); }
.control-row input { height:28px; width:72px; font:500 13px/1 var(--mono); text-align:center; }
.control-row .doing { flex:1; min-width:0; font:400 13px/1.4 var(--font); color:var(--muted); }
.dot { flex:none; width:8px; height:8px; border-radius:50%; }
.room-cell .actions { display:flex; gap:8px; margin-top:auto; }
.add-cell { border-left:1px solid var(--line); border-top:1px solid var(--line);
  margin:-1px 0 0 -1px; padding:20px; display:grid; place-items:center; }
/* A cell that has stretched across a row does not need a room's height. */
.add-cell.spanning button { min-height:120px; }
.add-cell button { width:100%; height:100%; min-height:196px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:8px; border:1px dashed var(--disabled);
  background:transparent; color:var(--muted); }
.add-cell button:hover { background:var(--surface); color:var(--ink); }
.add-cell .plus { font:400 20px/1 var(--font); }
.add-cell .what { font:600 14px/1 var(--font); }
.add-cell .why { font:400 12px/1.4 var(--font); color:var(--disabled); }

/* What is true right now, beside whatever is being edited. */
.inspector { border:1px solid var(--line); }
.inspector .cap { height:44px; display:flex; align-items:center; padding:0 16px;
  border-bottom:1px solid var(--line); font:600 11px/1 var(--font); letter-spacing:.12em;
  text-transform:uppercase; color:var(--muted); }
.inspector .now { padding:16px; display:flex; flex-direction:column; gap:14px; }
.inspector .facts > div { min-height:40px; display:flex; align-items:center; gap:16px;
  padding:0 16px; font-size:14px; border-top:1px solid var(--line); }
.inspector .facts .what { flex:1; color:var(--muted); }
.note { padding:14px 16px; border:1px solid var(--line); background:var(--accent-wash);
  font:400 13px/1.55 var(--font); }
.inspector .note { border:0; border-top:1px solid var(--line); }
.aside-note { font:400 13px/1.5 var(--font); color:var(--muted); }
.danger-group > .label { color:var(--danger); }
.explainer .prose { padding:16px; }
.explainer .prose p { font:400 14px/1.65 var(--font); color:var(--muted); max-width:70ch; }
.explainer .prose p + p { margin-top:14px; }
.explainer .prose b { color:var(--ink); font-weight:600; }
.danger-group { padding-top:26px; border-top:1px solid var(--line); }

/* History */
.ranges { display:flex; gap:8px; }
.ranges button { height:28px; padding:0 14px; font:600 13px/1 var(--font); }
.summary { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); border:1px solid var(--line); }
.summary > div { padding:14px 16px; }
.summary > div + div { border-left:1px solid var(--line); }
.summary .cap { font:600 11px/1 var(--font); letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); }
.summary .big { display:flex; align-items:baseline; gap:6px; margin-top:6px;
  font:700 20px/1 var(--font); }
.summary .big span { font:400 13px/1; color:var(--muted); }
.summary .under { font:400 12px/1.4 var(--font); color:var(--muted); margin-top:4px; }

.lanes { border:1px solid var(--line); }
.lane-cap { min-height:40px; display:flex; align-items:center; gap:12px; padding:0 16px;
  border-bottom:1px solid var(--line); font:600 11px/1 var(--font); letter-spacing:.12em;
  text-transform:uppercase; color:var(--muted); }
.lane-cap + .lane-cap, .lanes > .lane-cap:not(:first-child) { border-top:1px solid var(--line); }
.lane-cap .aside { margin-left:auto; font:400 12px/1 var(--font); text-transform:none;
  letter-spacing:0; }
.lane { display:flex; gap:20px; padding:16px 20px 12px; }
.lane .gutter { flex:none; width:152px; position:relative; font:400 12px/1 var(--font);
  color:var(--muted); }
.lane .gutter span { position:absolute; right:0; }
.lane .plot { flex:1; min-width:0; }
.lane svg, .strip svg, .signature-plot svg { display:block; width:100%; }
.lane-key { display:flex; flex-wrap:wrap; gap:16px; padding:0 20px 14px 192px;
  font:400 12px/1.4 var(--font); color:var(--muted); }
.lane-key span { display:flex; align-items:center; gap:7px; }
.lane-key i { display:block; }
.strip { min-height:36px; display:flex; align-items:center; gap:20px; padding:0 20px;
  border-bottom:1px solid var(--line); }
.strip .naming { flex:0 0 152px; display:flex; align-items:baseline; gap:10px; min-width:0; }
.strip .naming b { flex:1; min-width:0; font:400 13px/1.4 var(--font); color:var(--muted);
  font-weight:400; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.strip .naming small { flex:none; font:500 12px/1 var(--mono); color:var(--muted); }
.strip .plot { flex:1; min-width:0; }
.axis-row { display:flex; justify-content:space-between; padding:10px 20px 14px 192px;
  font:400 12px/1 var(--font); color:var(--muted); }
.legend-row { display:flex; flex-wrap:wrap; gap:8px; padding:14px 20px;
  border-top:1px solid var(--line); }
.legend-row button { display:flex; align-items:center; gap:8px; height:28px; padding:0 12px;
  font:400 13px/1 var(--font); }
.legend-row i { width:14px; height:2px; display:block; }

.section h2 { font:700 22px/1.2 var(--font); margin:0; }
.section > p { font:400 14px/1.5 var(--font); color:var(--muted); margin-top:6px; max-width:680px; }
.section .after { font:400 11px/1.4 var(--font); color:var(--muted); margin-top:8px; }
.grid-table { display:grid; border:1px solid var(--line); margin-top:16px; }
.grid-table .th { padding:10px 16px; border-bottom:1px solid var(--line); font:600 11px/1 var(--font);
  letter-spacing:.12em; text-transform:uppercase; color:var(--muted); }
.grid-table .td { padding:12px 16px; border-top:1px solid var(--line); font:400 14px/1.4 var(--font); }
.grid-table .num { text-align:right; font-variant-numeric:tabular-nums; }
.grid-table .mono { font:500 13px/1.4 var(--mono); }
.grid-table .quiet { font:400 13px/1.4 var(--font); color:var(--muted); }
.what-if { grid-template-columns:minmax(0,1fr) repeat(3,minmax(0,1fr)) minmax(0,1.4fr); }
.rooms-table { grid-template-columns:minmax(0,2fr) repeat(4,minmax(0,1fr)) minmax(0,1.5fr); }

.signature-split { display:grid; grid-template-columns:minmax(0,1fr) 300px; gap:20px;
  margin-top:16px; align-items:start; }
.signature-plot { border:1px solid var(--line); padding:20px; }
.signature-plot .holder { position:relative; }
.signature-plot .ytick { position:absolute; right:94.4%; transform:translateY(-50%);
  font:400 11px/1 var(--font); color:var(--muted); }
.signature-plot .xrow { display:flex; justify-content:space-between; gap:12px;
  padding:6px 1.9% 0 6.9%; font:400 11px/1 var(--font); color:var(--muted); }
.signature-plot .after { font:400 11px/1.4 var(--font); color:var(--muted); margin-top:10px; }

.save-bar { display:flex; align-items:center; gap:8px; }
.save-bar .save-state { margin-right:4px; }
.save-bar button[disabled] { color:var(--disabled); cursor:default; }
.save-bar button.primary[disabled] { background:var(--surface); border-color:var(--line);
  color:var(--disabled); }
button.quiet { background:transparent; border-color:transparent; color:var(--muted); }
button.quiet:hover { background:var(--surface-raised); color:var(--ink); }
button.quiet.tiny { height:auto; padding:0 4px; font-size:11px; }
button.danger { background:transparent; border-color:var(--line); color:var(--danger); }
button.danger:hover { background:#2E1512; }
.row-setting .problem { color:var(--danger); }
.entity-picker { position:relative; width:280px; }
.entity-results { position:absolute; right:0; top:calc(100% + 4px); width:320px; z-index:5;
  border:1px solid var(--line); max-height:280px; overflow:auto; overflow-x:hidden;
  background:var(--canvas); }
.entity-results button { display:flex; flex-direction:column; align-items:flex-start;
  justify-content:center; gap:2px; width:100%; height:52px; border:0; border-radius:0;
  background:transparent; padding:0 var(--s3); text-align:left; }
.entity-results button + button { border-top:1px solid var(--line); }
.entity-results button:hover { background:var(--surface-raised); }
.entity-results b, .entity-results small { max-width:100%; overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap; }
.entity-results b { font:400 14px/1.2 var(--font); }
.entity-results small { font:500 12px/1.3 var(--mono); color:var(--muted); }
.entity-results .none { padding:var(--s3); color:var(--muted); font:400 13px/1.4 var(--font); }
.tabs[hidden] { display:none; }

.lane .plot { position:relative; }
.lane svg[data-lane] { touch-action:none; }
line.crosshair { stroke:var(--ink); stroke-width:1; opacity:.55; }
.readout { position:absolute; top:8px; z-index:4; pointer-events:none;
  background:var(--surface-raised); border:1px solid var(--line); padding:var(--s3);
  min-width:190px; }
.readout[data-side=right] { margin-left:var(--s3); }
.readout[data-side=left] { margin-right:var(--s3); }
.readout p { display:flex; align-items:center; gap:var(--s2); font:400 13px/1.6 var(--font);
  white-space:nowrap; }
.readout p strong { margin-left:auto; font-variant-numeric:tabular-nums; }
.readout .when { font:500 12px/1.4 var(--mono); color:var(--muted); padding-bottom:var(--s2);
  margin-bottom:var(--s2); border-bottom:1px solid var(--line); }
.readout .swatch { display:inline-block; width:10px; height:10px; flex:none; }

@media (max-width:1100px) {
  .split, .signature-split { grid-template-columns:minmax(0,1fr); }
  .summary { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .summary > div:nth-child(3) { border-left:0; }
  .summary > div:nth-child(n+3) { border-top:1px solid var(--line); }
}
@media (max-width:600px) {
  .page { padding:20px 12px 32px; }
  /* The design is drawn for a desk. On a phone the state text is the part of
     the save bar worth losing: the buttons say the same thing. */
  .save-bar .save-state { display:none; }
  .save-bar button { padding:0 10px; }
  .app-bar { padding-left:12px; padding-right:12px; gap:8px; }
  .tabs { padding:0 12px; }
  .crumbs .here { font-size:14px; }
  .page-head { flex-direction:column; align-items:stretch; gap:12px; }
  .page-head h1 { font-size:22px; }
  .row-setting { flex-direction:column; align-items:stretch; }
  .row-setting .control { justify-content:flex-start; }
  .row-setting .select-wrap, .row-setting input.wide { flex:1; width:auto; }
  .summary { grid-template-columns:minmax(0,1fr); }
  .summary > div + div { border-left:0; border-top:1px solid var(--line); }
  .lane .gutter { display:none; }
  .lane-key, .axis-row { padding-left:20px; }
  .strip .naming { flex:0 0 96px; }
  .what-if, .rooms-table { grid-template-columns:minmax(0,1fr); }
  .grid-table .th { display:none; }
  .grid-table .td { border-top:0; }
  .grid-table .td:first-child { border-top:1px solid var(--line); }
  input, select { font-size:16px; }
}

/* 14 ── UTILITIES AND RESPONSIVE ──────────────────────────── */

.grow { flex:1; min-width:0; }
.right { margin-left:auto; }
.muted { color:var(--muted); }
.accent { color:var(--accent-ink); }
.danger-text { color:var(--danger); }
.ok-text { color:var(--ok); }
.nowrap { white-space:nowrap; }
.truncate { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.hstack { display:flex; align-items:center; gap:var(--s2); }
.vstack { display:flex; flex-direction:column; gap:var(--s2); }
[hidden] { display:none !important; }
`;


const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>'"]/g, (char) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);

/** What the server's refusal keys mean, in words that name the way out. */
const PROBLEMS = {
  required: "This is needed.",
  own_entity:
    "That is one of this integration's own entities — a room set to drive it would drive itself.",
  no_devices:
    "A room that can neither heat nor cool is a thermometer. Give it an air conditioner, a heater, or both.",
};

const TABS = [["rooms", "Rooms"], ["house", "House"], ["history", "History"]];

/** Home Assistant's mode names, in the design's words. */
const MODES = {
  off: "Off", heat: "Heat", cool: "Cool", heat_cool: "Heat / cool",
  dry: "Dry", fan_only: "Fan only",
};

/** The design's colours, where they are not already tokens. */
const TONE = {
  off:     { pillBg: "#242B33", pillInk: "#949CA3", dot: "#4A5158", iconBg: "#242B33", iconInk: "#C2C9CF" },
  idle:    { pillBg: "#33200F", pillInk: "#FF9500", dot: "#FF9500", iconBg: "#242B33", iconInk: "#FF9500" },
  running: { pillBg: "#33200F", pillInk: "#FF9455", dot: "#F36D21", iconBg: "#33200F", iconInk: "#FF9455" },
};
const ROOM_COLOURS = ["#5FA8E8", "#6FCF7F", "#D08CB8", "#E8C15F", "#9A8CE8"];
const LANE = { season: "#1C1408", band: "#242B33", deficit: "#3B1A16", ran: "#3A2510" };

/** The design's four mode icons. */
const ICONS = {
  heat: `<svg width="24" height="24" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="10" cy="10" r="3.6"></circle><line x1="10" y1="1.6" x2="10" y2="4"></line><line x1="10" y1="16" x2="10" y2="18.4"></line><line x1="1.6" y1="10" x2="4" y2="10"></line><line x1="16" y1="10" x2="18.4" y2="10"></line><line x1="4.1" y1="4.1" x2="5.8" y2="5.8"></line><line x1="14.2" y1="14.2" x2="15.9" y2="15.9"></line><line x1="15.9" y1="4.1" x2="14.2" y2="5.8"></line><line x1="5.8" y1="14.2" x2="4.1" y2="15.9"></line></svg>`,
  cool: `<svg width="24" height="24" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><line x1="10" y1="1.8" x2="10" y2="18.2"></line><line x1="2.9" y1="5.9" x2="17.1" y2="14.1"></line><line x1="2.9" y1="14.1" x2="17.1" y2="5.9"></line><line x1="7.4" y1="4.4" x2="10" y2="6.4"></line><line x1="12.6" y1="4.4" x2="10" y2="6.4"></line><line x1="7.4" y1="15.6" x2="10" y2="13.6"></line><line x1="12.6" y1="15.6" x2="10" y2="13.6"></line></svg>`,
  off: `<svg width="24" height="24" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="10" cy="11.2" r="6.6"></circle><line x1="10" y1="2.2" x2="10" y2="8.4"></line></svg>`,
  other: `<svg width="24" height="24" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="7.4" y="2" width="5.2" height="11" rx="2.6"></rect><circle cx="10" cy="14.9" r="3.3"></circle></svg>`,
};

const number = (value, digits = 1) =>
  value === null || value === undefined || Number.isNaN(Number(value))
    ? "—" : Number(value).toFixed(digits);

/** A moment in full, for a readout. */
const momentLabel = (timestamp) => {
  const at = new Date(timestamp * 1000);
  return `${at.toLocaleDateString([], { day: "numeric", month: "short" })} ${at.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

const when = (timestamp, span) => {
  const at = new Date(timestamp * 1000);
  return span === "24h"
    ? at.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : at.toLocaleDateString([], { day: "numeric", month: "short" });
};

class RoomThermostatPage extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.rooms = [];
    this.house = {};
    this.loaded = false;
    this.busy = false;
    this.error = "";
    this.tab = "rooms";
    this.editing = null;
    this.draft = null;
    this.draftHouse = null;
    this.problems = {};
    this.history = null;
    this.span = "7d";
    // Not `hidden`: that is a reflected DOM attribute, and a custom element
    // may not gain an attribute in its constructor. Assigning one throws
    // NotSupportedError, which marks the definition failed and turns every
    // instance into an HTMLUnknownElement — a page that silently never
    // renders.
    this.hiddenSeries = new Set();
    this.routeHandler = () => this.restoreRoute();
  }

  set hass(value) {
    const first = !this._hass;
    this._hass = value;
    if (first && this.isConnected) this.load();
    // Live values are written into the nodes that hold them. Re-rendering
    // here is what made every state change in the house redraw the whole
    // page — dozens of times a minute, closing pickers and scrolling to the
    // top, which looked like the page reloading on every navigation.
    else if (this.loaded) this.refreshLive();
  }

  set narrow(value) { this.toggleAttribute("narrow", Boolean(value)); }
  set panel(value) { this._panel = value; }

  connectedCallback() {
    installFonts();
    window.addEventListener("hashchange", this.routeHandler);
    this.readRoute();
    this.renderShell();
    if (this._hass && !this.loaded) this.load();
  }

  disconnectedCallback() {
    window.removeEventListener("hashchange", this.routeHandler);
  }

  readRoute() {
    const [tab, id] = (window.location.hash || "#rooms").slice(1).split("/");
    this.tab = TABS.some(([key]) => key === tab) ? tab : "rooms";
    this.editing = id || null;
    this.problems = {};
    this.draftDirty = id === "new";
    this.draft = id
      ? id === "new"
        ? { name: "", cooling_strategy: "gated", frost_temperature: 5 }
        : { ...this.rooms.find((room) => room.id === id) }
      : null;
  }

  restoreRoute() {
    this.readRoute();
    this.renderBody();
    if (this.tab === "history" && !this.history) this.loadHistory();
  }

  go(hash) { window.location.hash = hash; }

  async call(message) {
    if (!this._hass) throw new Error("Home Assistant is not ready");
    return this._hass.connection.sendMessagePromise(message);
  }

  async load() {
    try {
      const record = await this.call({ type: "room_thermostat/rooms/list" });
      this.rooms = record.rooms;
      this.house = record.house;
      this.loaded = true;
      this.error = "";
    } catch (err) {
      this.error = err?.message || "Could not read the record";
    }
    this.restoreRoute();
    this.renderChrome();
  }

  /*
   * The chrome is drawn once and stays. Only the body is replaced when the
   * route changes, and nothing at all is replaced when a reading changes.
   *
   * Replacing the whole page — bar, tabs and all — with "Reading the record…"
   * is what made every navigation flash.
   */
  renderShell() {
    this.shadowRoot.innerHTML = `<style>${STYLES}</style>
      <header class="app-bar" data-chrome></header>
      <nav class="tabs" data-tabs></nav>
      <main data-body></main>`;
    this.renderChrome();
    this.renderBody();
  }

  /** Whether what is on screen has anything to save. */
  dirty() {
    if (this.editing) return this.draftDirty === true;
    if (this.tab === "house") return this.draftHouse !== null;
    return false;
  }

  renderChrome() {
    const bar = this.shadowRoot.querySelector("[data-chrome]");
    const tabs = this.shadowRoot.querySelector("[data-tabs]");
    if (!bar || !tabs) return;
    // The save bar belongs to a room and to the house; everywhere else that
    // corner says what the season is doing.
    const showSave = Boolean(this.editing) || this.tab === "house";
    const dirty = this.dirty();
    bar.innerHTML = `<span class="mark"></span>
      <nav class="crumbs">
        ${this.editing
          ? `<a class="link" data-go="#rooms">Rooms</a>
             <span class="sep">/</span>
             <span class="here">${escapeHtml(this.draft?.name || "New room")}</span>`
          : `<span class="here">Room Thermostat</span>`}
      </nav>
      <span class="spacer"></span>
      ${this.error ? `<span class="save-state dirty">${escapeHtml(this.error)}</span>` : ""}
      ${showSave ? `<div class="save-bar">
          <span class="save-state ${dirty ? "dirty" : ""}">${dirty ? "Unsaved changes" : "No unsaved changes"}</span>
          <button data-revert ${dirty ? "" : "disabled"}>Revert</button>
          <button class="primary" data-save ${dirty && !this.busy ? "" : "disabled"}>${
            this.editing ? (this.draft?.id ? "Save room" : "Add room") : "Save the house"}</button>
        </div>`
        : `<span class="save-state">${escapeHtml(this.seasonWord())}</span>`}`;
    tabs.hidden = Boolean(this.editing);
    tabs.innerHTML = this.editing ? "" : TABS.map(([key, label]) =>
      `<button data-go="#${key}" class="${key === this.tab ? "active" : ""}">${label}</button>`).join("");
    this.bindChrome(bar);
    this.bindChrome(tabs);
  }

  bindChrome(root) {
    root.querySelectorAll("[data-save]").forEach((node) =>
      node.addEventListener("click", () => {
        if (this.editing) this.saveRoom();
        else this.saveHouse();
      }));
    root.querySelectorAll("[data-revert]").forEach((node) =>
      node.addEventListener("click", () => {
        if (this.editing) {
          this.draft = { ...this.rooms.find((room) => room.id === this.editing) };
          this.draftDirty = false;
        } else {
          this.draftHouse = null;
        }
        this.renderBody();
      }));
    root.querySelectorAll("[data-go]").forEach((node) => {
      node.addEventListener("click", (event) => {
        event.preventDefault();
        this.go(node.dataset.go);
      });
    });
  }

  renderBody() {
    const body = this.shadowRoot.querySelector("[data-body]");
    if (!body) return;
    if (!this.loaded) {
      // Only ever seen once, before the first answer arrives.
      body.innerHTML = `<div class="page"><p class="muted">Reading the record…</p></div>`;
      return;
    }
    if (this.watchGrid) this.watchGrid.disconnect();
    body.innerHTML = this.editing
      ? this.roomEditor()
      : this.tab === "house"
        ? this.houseTab()
        : this.tab === "history"
          ? this.historyTab()
          : this.roomsTab();
    this.bind(body);
    this.renderChrome();
    const grid = body.querySelector(".room-grid");
    if (grid) {
      this.fitAddCell();
      // The column count changes with the window, and so does what is left
      // of the last row.
      this.watchGrid = new ResizeObserver(() => this.fitAddCell());
      this.watchGrid.observe(grid);
    }
  }

  // --- what a room is doing ----------------------------------------------

  climateOf(room) {
    return Object.values(this._hass?.states || {}).find(
      (state) =>
        state.entity_id?.startsWith("climate.") &&
        state.attributes?.room_id === room.id,
    ) || null;
  }

  liveOf(room) {
    const state = this.climateOf(room);
    const attributes = state?.attributes || {};
    const mode = state?.state || "off";
    const action = attributes.hvac_action || "idle";
    const target = attributes.temperature;
    const frost = number(room.frost_temperature ?? 5);

    // The design's own sentences. "Idle" alone is what made the season
    // lockout look like a fault rather than a decision.
    let doing;
    if (!state) doing = "No reading — this room's thermostat has not started";
    else if (mode === "off") doing = `Off — frost protection still holds at ${frost} °C`;
    else if (mode === "heat" && attributes.heating_season === false)
      doing = "Idle — heating is out of season";
    else if (mode === "cool" && attributes.cooling_season === false)
      doing = "Idle — cooling is out of season";
    else if (action === "heating") doing = `Heating to ${number(target)} °C`;
    else if (action === "cooling") doing = `Cooling to ${number(target)} °C`;
    else if (action === "drying") doing = "Drying — no setpoint in this mode";
    else if (action === "fan") doing = "Running — fan only";
    else doing = "At target, idle";

    const tone = !state || mode === "off"
      ? TONE.off
      : action === "heating" || action === "cooling"
        ? TONE.running
        : TONE.idle;
    const word = !state ? "Unknown"
      : mode === "off" ? "Off"
      : action === "heating" ? "Heating"
      : action === "cooling" ? "Cooling"
      : "Idle";
    const icon = mode === "heat" ? "heat" : mode === "cool" ? "cool"
      : mode === "off" ? "off" : "other";

    return {
      entityId: state?.entity_id || null,
      mode,
      modes: attributes.hvac_modes || [],
      temperature: attributes.current_temperature,
      humidity: attributes.current_humidity,
      target,
      doing, tone, word, icon,
    };
  }

  roomCell(room) {
    const live = this.liveOf(room);
    return `<div class="room-cell" data-room="${room.id}">
      <div class="head">
        <span class="room-icon" data-icon
              style="background:${live.tone.iconBg};color:${live.tone.iconInk}">${ICONS[live.icon]}</span>
        <span class="naming">
          <b>${escapeHtml(room.name)}</b>
          <small title="${escapeHtml(room.temperature_sensor || "")}">${escapeHtml(room.temperature_sensor || "no sensor")}</small>
        </span>
        <span class="pill" data-pill
              style="background:${live.tone.pillBg};color:${live.tone.pillInk}">${live.word}</span>
      </div>
      <p class="reading">
        <b data-temp>${number(live.temperature)}</b><span class="unit">°C</span>
        <span class="hum" data-hum>${live.humidity === undefined || live.humidity === null ? "" : `${Math.round(live.humidity)}&thinsp;% RH`}</span>
      </p>
      <div class="controls">
        <div class="control-row">
          <span class="what">Mode</span>
          <div class="select-wrap">
            <select data-mode="${room.id}" aria-label="Mode">
              ${live.modes.map((mode) =>
                `<option value="${mode}" ${mode === live.mode ? "selected" : ""}>${MODES[mode] || mode}</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="control-row">
          <span class="what">Target</span>
          <input type="number" step="0.5" data-target="${room.id}" aria-label="Target"
                 value="${live.target ?? ""}" ${live.target === undefined || live.target === null ? "disabled" : ""}>
          <span class="unit">°C</span>
        </div>
        <div class="control-row">
          <span class="dot" data-dot style="background:${live.tone.dot}"></span>
          <span class="doing" data-doing>${escapeHtml(live.doing)}</span>
        </div>
      </div>
      <div class="actions">
        <button data-go="#rooms/${room.id}">Settings</button>
        <button class="quiet" data-history="${room.id}">History</button>
      </div>
    </div>`;
  }

  roomsTab() {
    if (!this.rooms.length) {
      return `<div class="page">
        <div class="page-head"><div class="grow"><h1>Rooms</h1>
          <p>A room is a temperature sensor and whatever heats or cools it.</p></div></div>
        <div class="room-grid"><div class="add-cell">
          <button data-add-room><span class="plus">+</span><span class="what">Add a room</span>
            <span class="why">A sensor and whatever heats or cools it</span></button>
        </div></div>
      </div>`;
    }
    return `<div class="page">
      <div class="page-head">
        <div class="grow"><h1>Rooms</h1>
          <p>What each room reads, what it is set to, and what it is doing.</p></div>
        <button class="primary" data-add-room>Add a room</button>
      </div>
      <div class="room-grid">
        ${this.rooms.map((room) => this.roomCell(room)).join("")}
        <div class="add-cell">
          <button data-add-room><span class="plus">+</span><span class="what">Add a room</span>
            <span class="why">A sensor and whatever heats or cools it</span></button>
        </div>
      </div>
    </div>`;
  }

  /*
   * Write the readings into the nodes that hold them.
   *
   * A state arrives every few seconds. Redrawing the page for each one is
   * what closed pickers mid-search and threw away the scroll position; this
   * touches only the text that changed.
   */
  /*
   * Let the add cell finish the row it lands on.
   *
   * Three rooms in three columns put it alone on a second row and left two
   * thirds of that row as an empty bordered box. How many columns there are
   * is only known once the grid has been laid out, so it is measured rather
   * than guessed.
   */
  fitAddCell() {
    const grid = this.shadowRoot.querySelector(".room-grid");
    const cell = grid?.querySelector(".add-cell");
    if (!grid || !cell) return;
    const columns = window.getComputedStyle(grid)
      .gridTemplateColumns.split(" ").filter(Boolean).length;
    if (!columns) return;
    const used = this.rooms.length % columns;
    const span = used === 0 ? columns : columns - used;
    cell.style.gridColumn = span > 1 ? `span ${span}` : "";
    cell.classList.toggle("spanning", span > 1);
  }

  refreshLive() {
    const root = this.shadowRoot;
    if (!root || this.editing) return;
    root.querySelectorAll("[data-room]").forEach((cell) => {
      const room = this.rooms.find((item) => item.id === cell.dataset.room);
      if (!room) return;
      const live = this.liveOf(room);
      const set = (selector, value) => {
        const node = cell.querySelector(selector);
        if (node && node.textContent !== value) node.textContent = value;
      };
      set("[data-temp]", number(live.temperature));
      set("[data-doing]", live.doing);
      const humidity = cell.querySelector("[data-hum]");
      const shown = live.humidity === undefined || live.humidity === null
        ? "" : `${Math.round(live.humidity)} % RH`;
      if (humidity && humidity.textContent !== shown) humidity.textContent = shown;
      const pill = cell.querySelector("[data-pill]");
      if (pill && pill.textContent !== live.word) {
        pill.textContent = live.word;
        pill.style.background = live.tone.pillBg;
        pill.style.color = live.tone.pillInk;
      }
      const dot = cell.querySelector("[data-dot]");
      if (dot) dot.style.background = live.tone.dot;
      const icon = cell.querySelector("[data-icon]");
      if (icon) {
        icon.style.background = live.tone.iconBg;
        icon.style.color = live.tone.iconInk;
        if (icon.dataset.shows !== live.icon) {
          icon.dataset.shows = live.icon;
          icon.innerHTML = ICONS[live.icon];
        }
      }
      // A field somebody is typing in is left alone.
      const mode = cell.querySelector("[data-mode]");
      if (mode && mode !== root.activeElement && mode.value !== live.mode) mode.value = live.mode;
      const target = cell.querySelector("[data-target]");
      if (target && target !== root.activeElement && live.target !== undefined
          && Number(target.value) !== Number(live.target)) {
        target.value = live.target;
      }
    });
    if (this.tab === "house" || this.editing) this.refreshInspector();
  }

  async setMode(roomId, mode) {
    const live = this.liveOf(this.rooms.find((room) => room.id === roomId) || {});
    if (!live.entityId) return;
    await this._hass.callService("climate", "set_hvac_mode", {
      entity_id: live.entityId, hvac_mode: mode,
    });
  }

  async setTarget(roomId, value) {
    const live = this.liveOf(this.rooms.find((room) => room.id === roomId) || {});
    if (!live.entityId || value === "" || Number.isNaN(Number(value))) return;
    await this._hass.callService("climate", "set_temperature", {
      entity_id: live.entityId, temperature: Number(value),
    });
  }

  // --- rows of settings ---------------------------------------------------

  /** A row: what it is and why on the left, the control on the right. */
  settingRow(name, why, control, { entity = null, problem = null } = {}) {
    const message = problem ? PROBLEMS[problem] || problem : null;
    return `<div class="row-setting">
      <div class="what">
        <div class="name">${name}</div>
        ${entity === null ? "" : entity
          ? `<div class="entity" title="${escapeHtml(entity)}">${escapeHtml(this.entityName(entity))}</div>`
          : `<div class="entity none">Not set</div>`}
        ${why ? `<div class="why">${why}</div>` : ""}
        ${message ? `<div class="why problem">${escapeHtml(message)}</div>` : ""}
      </div>
      <div class="control">${control}</div>
    </div>`;
  }

  entityName(entityId) {
    const state = this._hass?.states?.[entityId];
    return state ? `${state.attributes?.friendly_name || entityId} · ${entityId}` : entityId;
  }

  numberBox(name, value, unit) {
    return `<input type="number" step="0.5" name="${name}" value="${escapeHtml(value ?? "")}">
      <span class="unit">${unit}</span>`;
  }

  /** A picker behind a Change button, as the design draws it. */
  chooser(name, domains, deviceClass = null, label = "Change", clearable = false) {
    const open = this.picking === name;
    if (!open) {
      return `<button type="button" data-pick="${name}">${label}</button>
        ${clearable ? `<button type="button" class="quiet" data-clear="${name}" title="Clear">✕</button>` : ""}`;
    }
    const states = Object.values(this._hass?.states || {})
      .filter((state) => domains.includes(state.entity_id.split(".")[0]))
      .filter((state) => !deviceClass || state.attributes?.device_class === deviceClass
        || !state.entity_id.startsWith("sensor."))
      .sort((first, second) => this.entityName(first.entity_id)
        .localeCompare(this.entityName(second.entity_id)));
    return `<div class="entity-picker" data-picker="${name}">
      <input class="entity-search" data-entity-search type="search" autocomplete="off"
             placeholder="Search entities…" aria-label="Search entities">
      <div class="entity-results">
        ${states.length ? states.map((state) => {
          const option = this.entityName(state.entity_id);
          return `<button type="button" data-entity-option="${escapeHtml(state.entity_id)}"
                    data-entity-terms="${escapeHtml(option.toLowerCase())}">
                    <b>${escapeHtml(state.attributes?.friendly_name || state.entity_id)}</b>
                    <small>${escapeHtml(state.entity_id)}</small>
                  </button>`;
        }).join("") : `<p class="none">Nothing of that kind in this house.</p>`}
      </div>
    </div>`;
  }

  // --- the room editor ----------------------------------------------------

  roomEditor() {
    const draft = this.draft || {};
    const isNew = !draft.id;
    const live = isNew ? null : this.liveOf(draft);
    const heaters = draft.heaters || [];
    return `<div class="page split">
      <div class="column">
        <div class="page-head"><div class="grow">
          <h1>${escapeHtml(draft.name || "New room")}</h1>
          <p>A room is a temperature sensor and whatever heats or cools it.</p>
        </div></div>

        <div class="group"><div class="label">Identity</div><div class="rows">
          ${this.settingRow("Name", "What this room is called, here and in Home Assistant.",
            `<input type="text" class="wide" name="name" value="${escapeHtml(draft.name || "")}">`,
            { problem: this.problems.name })}
        </div></div>

        <div class="group"><div class="label">Sensors</div><div class="rows">
          ${this.settingRow("Temperature sensor",
            "The reason this integration exists: the room is controlled against this, never against the air conditioner's own sensor.",
            this.chooser("temperature_sensor", ["sensor", "input_number", "number"], "temperature"),
            { entity: draft.temperature_sensor, problem: this.problems.temperature_sensor })}
          ${this.settingRow(`Humidity sensor <span class="optional">optional</span>`, "",
            this.chooser("humidity_sensor", ["sensor", "input_number", "number"], "humidity", "Change", true),
            { entity: draft.humidity_sensor })}
        </div></div>

        <div class="group"><div class="label">Equipment</div><div class="rows">
          ${this.settingRow("Air conditioner",
            "Any climate entity. Its fan, swing and preset lists are mirrored rather than replaced.",
            this.chooser("cooler", ["climate"], null, "Change", true),
            { entity: draft.cooler, problem: this.problems.cooler })}
          <div class="row-setting">
            <div class="what">
              <div class="name">Heaters</div>
              ${heaters.length
                ? heaters.map((entity) =>
                    `<div class="entity" title="${escapeHtml(entity)}">${escapeHtml(this.entityName(entity))}
                      <button type="button" class="quiet tiny" data-drop-heater="${escapeHtml(entity)}" title="Remove">✕</button>
                    </div>`).join("")
                : `<div class="entity none">None — this room cools only</div>`}
              <div class="why">A radiator valve is a valve entity, not a switch. A room may have several, and they open together.</div>
              ${this.problems.base ? `<div class="why problem">${escapeHtml(PROBLEMS[this.problems.base])}</div>` : ""}
            </div>
            <div class="control">${this.chooser("heaters", ["valve", "switch", "input_boolean"], null, "Add heater")}</div>
          </div>
          ${this.settingRow("Cooling strategy",
            "Gated is for a unit whose sensor reads its own recirculated air and stops while the room is still warm.",
            `<div class="select-wrap"><select name="cooling_strategy">
              <option value="gated" ${draft.cooling_strategy === "gated" ? "selected" : ""}>Park the unit and gate it on the room's sensor</option>
              <option value="passthrough" ${draft.cooling_strategy !== "gated" ? "selected" : ""}>Let the unit run its own thermostat</option>
            </select></div>`)}
        </div></div>

        <div class="group"><div class="label">Safety</div><div class="rows">
          ${this.settingRow("Frost protection",
            "Heats whatever the mode, whatever the season. A thermostat switched off must not be able to freeze a pipe.",
            this.numberBox("frost_temperature", draft.frost_temperature ?? 5, "°C"))}
        </div></div>

        ${isNew ? "" : `<div class="group danger-group"><div class="label">Danger zone</div><div class="rows">
          ${this.settingRow("Delete this room",
            "", `<button class="danger" data-delete>Delete room</button>`)}
          <div class="row-setting"><div class="what"><div class="why">The sensor and the air conditioner stay; only the room and its history go.</div></div></div>
        </div></div>`}
      </div>

      ${isNew ? "<div></div>" : `<div class="column" data-inspector>
        ${this.roomInspector(draft, live)}
        <div class="aside-note">Seasons are decided once for the whole house. This room has no
          seasonal settings of its own — they live on <a class="link" data-go="#house">House</a>.</div>
      </div>`}
    </div>`;
  }

  roomInspector(room, live) {
    if (!live) return "";
    return `<div class="inspector">
      <div class="cap">Right now</div>
      <div class="now">
        <p class="reading"><b data-temp>${number(live.temperature)}</b><span class="unit">°C</span>
          <span class="hum" data-hum>${live.humidity === undefined || live.humidity === null ? "" : `${Math.round(live.humidity)}&thinsp;% RH`}</span></p>
        <div class="control-row" style="padding:0">
          <span class="dot" data-dot style="background:${live.tone.dot}"></span>
          <span class="doing" data-doing>${escapeHtml(live.doing)}</span>
        </div>
      </div>
      <div class="facts">
        <div><span class="what">Mode</span><span>${MODES[live.mode] || live.mode}</span></div>
        <div><span class="what">Target</span><span>${live.target === undefined || live.target === null ? "—" : `${number(live.target)} °C`}</span></div>
        <div><span class="what">Season</span><span>${this.seasonWord()}</span></div>
        <div><span class="what">Frost protection</span><span>${number(room.frost_temperature ?? 5)} °C</span></div>
      </div>
    </div>`;
  }

  refreshInspector() {
    const root = this.shadowRoot.querySelector("[data-inspector]");
    if (!root || !this.draft) return;
    const live = this.liveOf(this.draft);
    const set = (selector, value) => {
      const node = root.querySelector(selector);
      if (node && node.textContent !== value) node.textContent = value;
    };
    set("[data-temp]", number(live.temperature));
    set("[data-doing]", live.doing);
    const dot = root.querySelector("[data-dot]");
    if (dot) dot.style.background = live.tone.dot;
  }

  // --- the house ----------------------------------------------------------

  seasonSensor() {
    return Object.values(this._hass?.states || {}).find(
      (state) =>
        state.entity_id?.startsWith("binary_sensor.") &&
        state.attributes?.damped !== undefined,
    ) || null;
  }

  dampedNow() {
    const value = this.seasonSensor()?.attributes?.damped;
    return typeof value === "number" ? value : null;
  }

  seasonWord() {
    const house = this.draftHouse || this.house;
    if (!house.outdoor_sensor) return "Not decided";
    const sensor = this.seasonSensor();
    if (!sensor) return "Waiting for a reading";
    return sensor.state === "on" ? "Heating season" : "Out of season";
  }

  seasonExplainer() {
    const house = this.draftHouse || this.house;
    if (!house.outdoor_sensor) {
      return `No outdoor temperature is set, so nothing is held back: every room
        heats and cools exactly as it would have before.`;
    }
    const damped = this.dampedNow();
    if (damped === null) {
      return `Waiting for a first reading from
        <b>${escapeHtml(house.outdoor_sensor)}</b>. Until one arrives nothing is held back.`;
    }
    const limit = Number(house.heat_limit);
    const hysteresis = Number(house.heat_limit_hysteresis);
    const inSeason = this.seasonSensor()?.state === "on";
    return `The outdoor average is <b>${number(damped)} °C</b> against a limit of
      ${number(limit)}. Heating is <b>${inSeason ? "in season" : "out of season"}</b>,
      ${inSeason
        ? `so a room below its setpoint heats. It leaves once the average passes
           ${number(limit + hysteresis)} °C.`
        : `so a room below its setpoint stays idle. It comes back once the average
           falls below ${number(limit)} °C.`}
      A change has to last ${house.season_dwell_hours} hours — the dwell — before it
      counts, because a mild autumn dips below the limit for a few hours every night.`;
  }

  houseTab() {
    const house = this.draftHouse || this.house;
    const limit = Number(house.heat_limit);
    const damped = this.dampedNow();
    return `<div class="page split">
      <div class="column">
        <div class="page-head"><div class="grow"><h1>House</h1>
          <p>Decided once for the whole house, from an outdoor temperature. Rooms obey
          this; they have no seasonal settings of their own.</p></div></div>

        <div class="group"><div class="label">Outdoor</div><div class="rows">
          ${this.settingRow("Outdoor temperature",
            "A sensor or a weather entity. Put a sensor in shade: one in afternoon sun reads far too warm and would hold the heating off on a cold day. Leave it empty and nothing is held back at all.",
            this.chooser("outdoor_sensor", ["sensor", "weather", "input_number", "number"], null, "Change", true),
            { entity: house.outdoor_sensor })}
        </div></div>

        <div class="group"><div class="label">Heating season</div><div class="rows">
          ${this.settingRow("Heating stops above",
            "The outdoor average above which the house heats itself — sun, cooking, bodies. Around 16 for an insulated house, higher for an old one.",
            this.numberBox("heat_limit", house.heat_limit, "°C"))}
          ${this.settingRow("Heating restarts this far below", "",
            this.numberBox("heat_limit_hysteresis", house.heat_limit_hysteresis, "K"))}
          ${this.settingRow("Averaging time",
            "The heating decision follows an average rather than the reading, so one warm afternoon does not end the season. Longer suits a heavy masonry house.",
            this.numberBox("damping_hours", house.damping_hours, "hours"))}
          ${this.settingRow("A change must last",
            "A mild autumn dips below the limit for a few hours every night. Nothing changes until it has lasted this long.",
            this.numberBox("season_dwell_hours", house.season_dwell_hours, "hours"))}
        </div></div>

        <div class="group"><div class="label">Cooling season</div><div class="rows">
          ${this.settingRow("Cooling stops below",
            "Judged on the live reading rather than the average: a sunny afternoon in an otherwise cold week still overheats a room that afternoon.",
            this.numberBox("cool_limit", house.cool_limit, "°C"))}
          ${this.settingRow("Cooling restarts this far above", "",
            this.numberBox("cool_limit_hysteresis", house.cool_limit_hysteresis, "K"))}
        </div></div>

        ${this.howItWorks()}

        <div class="group"><div class="label">When the weather is wrong</div><div class="rows">
          ${this.settingRow("Heat anyway this far below setpoint",
            "The weather is a guess and the room's own thermometer is not. Keep this well below your setpoint, or it will heat on the very evenings the limit exists to prevent.",
            this.numberBox("heat_override", house.heat_override, "K"))}
          ${this.settingRow("Cool anyway this far above setpoint", "",
            this.numberBox("cool_override", house.cool_override, "K"))}
        </div></div>

      </div>

      <div class="column" data-inspector>
        <div class="inspector">
          <div class="cap">The decision right now</div>
          <div class="now">
            <p class="reading"><b>${number(damped)}</b><span class="unit">°C</span>
              <span class="hum">outdoor average</span></p>
            <div class="control-row" style="padding:0">
              <span class="dot" style="background:${this.seasonSensor()?.state === "on" ? TONE.running.dot : TONE.idle.dot}"></span>
              <span style="font:600 14px/1.3 var(--font)">${this.seasonWord()}</span>
            </div>
          </div>
          <div class="facts">
            <div><span class="what">Heating limit</span><span>${number(limit)} °C</span></div>
            <div><span class="what">Leaves above</span><span>${number(limit + Number(house.heat_limit_hysteresis))} °C</span></div>
            <div><span class="what">Dwell</span><span>${house.season_dwell_hours} hours</span></div>
            <div><span class="what">Rooms obeying</span><span>${this.rooms.length}</span></div>
          </div>
          <div class="note">${this.seasonExplainer()}</div>
        </div>
        <div class="aside-note">Frost protection is per room and ignores all of this.
          See <a class="link" data-go="#rooms">Rooms</a>.</div>
      </div>
    </div>`;
  }

  /**
   * The whole of it, in order, in words.
   *
   * Every number on this page is one clause of a single sentence, and the
   * sentence is never written down anywhere. Somebody coming back in six
   * months — or arriving for the first time — should be able to read what
   * their house is actually doing without reconstructing it from eight
   * fields.
   */
  howItWorks() {
    const house = this.draftHouse || this.house;
    const limit = number(house.heat_limit);
    const back = number(Number(house.heat_limit) + Number(house.heat_limit_hysteresis));
    const cool = number(house.cool_limit);
    const coolBack = number(Number(house.cool_limit) - Number(house.cool_limit_hysteresis));
    return `<div class="group explainer">
      <div class="label">How the thermostat decides</div>
      <div class="rows">
        <div class="prose">
          <p><b>A room asks first.</b> Every room compares its own sensor with its
          setpoint. Below it, the room wants heat; above it, it wants cooling. That
          is the whole of what a room knows, and on its own it would run the heating
          in September because 20 °C is still below 22 °C.</p>

          <p><b>The house answers second.</b> A setpoint of 22 means "heat to 22" in
          January and "do nothing" in September, and the difference is the weather.
          So the house watches the outdoor temperature and decides once, for
          everybody, whether heating is in season at all. A room that wants heat out
          of season stays idle.</p>

          <p><b>It decides on an average, not a reading.</b> Outdoor temperature
          swings ten degrees between afternoon and dawn, and a threshold on the
          reading would put the heating on every night and take it off every
          afternoon. What is watched is a
          <b>${house.damping_hours}-hour average</b> — slow enough that one warm day
          does not end the season and one cold night does not start it.</p>

          <p><b>The limit is where your house stops heating itself.</b> Above about
          ${limit} °C outside, sun and cooking and bodies cover what the house loses,
          and a room that is a degree down is on its way up anyway. Below it, the
          room genuinely cannot get there alone. Heating leaves the season once the
          average passes <b>${back} °C</b> and comes back below <b>${limit} °C</b> —
          two thresholds, so a day sitting exactly on the line cannot flip it back
          and forth.</p>

          <p><b>And a change has to last ${house.season_dwell_hours} hours.</b> A
          mild autumn dips under the limit for a few hours every night even after
          the averaging. Without the wait, the season would turn over before dawn
          and back by mid-morning; with it, nothing counts until it has held.</p>

          <p><b>Cooling is judged differently, on purpose.</b> It follows the live
          reading rather than the average, because one sunny afternoon in an
          otherwise cold week genuinely overheats a room that afternoon. The air
          conditioner stops below <b>${cool} °C</b> outside and returns above
          <b>${coolBack} °C</b>.</p>

          <p><b>Two things overrule all of it.</b> If a room drifts more than
          ${number(house.heat_override)} K below its setpoint the heating runs
          anyway — the weather is a guess and the room's own thermometer is not. And
          frost protection, set per room, heats whatever the mode and whatever the
          season: a thermostat switched off must not be able to freeze a pipe.</p>
        </div>
      </div>
    </div>`;
  }

  // --- writing ------------------------------------------------------------

  housePayload() {
    const draft = { ...(this.draftHouse || {}) };
    if (draft.outdoor_sensor !== undefined && !String(draft.outdoor_sensor ?? "").trim()) {
      // Clearing it is how seasons are switched off, so a null has to travel.
      draft.outdoor_sensor = null;
    }
    for (const key of Object.keys(draft)) {
      if (key !== "outdoor_sensor" && draft[key] !== null) draft[key] = Number(draft[key]);
    }
    return draft;
  }

  async saveHouse() {
    this.busy = true;
    this.renderBody();
    try {
      await this.call({ type: "room_thermostat/house/update", house: this.housePayload() });
      this.draftHouse = null;
      this.busy = false;
      await this.load();
    } catch (err) {
      this.error = err?.message || "Could not save the house";
      this.busy = false;
      this.renderBody();
    }
  }

  roomPayload() {
    const draft = { ...this.draft };
    draft.heaters = (draft.heaters || []).filter(Boolean);
    for (const key of ["humidity_sensor", "cooler"]) {
      if (draft[key] === "") draft[key] = null;
    }
    if (draft.frost_temperature !== undefined) {
      draft.frost_temperature = Number(draft.frost_temperature);
    }
    return draft;
  }

  async saveRoom() {
    this.busy = true;
    this.problems = {};
    this.renderBody();
    const payload = this.roomPayload();
    try {
      if (payload.id) {
        await this.call({
          type: "room_thermostat/rooms/update", room_id: payload.id, room: payload,
        });
      } else {
        await this.call({ type: "room_thermostat/rooms/create", room: payload });
      }
      this.busy = false;
      await this.load();
      this.go("#rooms");
    } catch (err) {
      // The server names the field; the page puts the message beside it.
      this.problems = err?.problems || err?.error?.problems || {};
      if (!Object.keys(this.problems).length) {
        this.error = err?.message || "Could not save that room";
      }
      this.busy = false;
      this.renderBody();
    }
  }

  async deleteRoom() {
    const name = this.draft?.name || "this room";
    if (!window.confirm(`Delete ${name}? Its thermostat, its sensors and its device go with it.`)) return;
    this.busy = true;
    this.renderBody();
    try {
      await this.call({ type: "room_thermostat/rooms/delete", room_id: this.draft.id });
      this.busy = false;
      await this.load();
      this.go("#rooms");
    } catch (err) {
      this.error = err?.message || "Could not delete that room";
      this.busy = false;
      this.renderBody();
    }
  }

  /** A field's value, into whichever draft is open. */
  take(field) {
    if (!field?.name) return;
    const value = field.type === "checkbox" ? field.checked : field.value;
    if (this.tab === "house" && !this.editing) {
      this.draftHouse = { ...(this.draftHouse || this.house), [field.name]: value };
    } else {
      this.draft = { ...(this.draft || {}), [field.name]: value };
      this.draftDirty = true;
    }
    this.renderChrome();
  }

  /** What a picker chose, into whichever draft is open. */
  chose(name, entityId) {
    if (name === "heaters") {
      const current = this.draft?.heaters || [];
      if (!current.includes(entityId)) {
        this.draft = { ...this.draft, heaters: [...current, entityId] };
        this.draftDirty = true;
      }
    } else if (this.tab === "house" && !this.editing) {
      this.draftHouse = { ...(this.draftHouse || this.house), [name]: entityId };
    } else {
      this.draft = { ...(this.draft || {}), [name]: entityId };
      this.draftDirty = true;
    }
    this.picking = null;
    this.renderBody();
  }

  // --- history ------------------------------------------------------------

  async loadHistory() {
    try {
      this.history = await this.call({ type: "room_thermostat/history", span: this.span });
      this.error = "";
    } catch (err) {
      this.error = err?.message || "Could not read the history";
    }
    if (this.tab === "history") this.renderBody();
  }

  /** What each room was set to, which the record does not keep. */
  setpointOf(roomId) {
    const room = this.rooms.find((item) => item.id === roomId);
    const live = room ? this.liveOf(room) : null;
    const target = live?.target;
    return typeof target === "number" ? target : null;
  }

  /**
   * Everything the three lanes and the tables are drawn from.
   *
   * Computed here rather than asked for: the answer already carries the
   * outdoor series, the average, the season spans and each room's demand, and
   * every number below is arithmetic over those.
   */
  lanes() {
    const data = this.history;
    const house = this.house;
    const limit = Number(house.heat_limit);
    const hysteresis = Number(house.heat_limit_hysteresis);
    const count = data.buckets;
    const hours = (data.end - data.start) / 3600;
    const perBucket = hours / count;

    const inSeason = Array.from({ length: count }, (_, index) => {
      const at = data.start + ((data.end - data.start) * (index + 0.5)) / count;
      return data.seasons.some(([from, to]) => at >= from && at < to);
    });

    const rooms = Object.entries(data.series.rooms).map(([id, room], index) => {
      const setpoint = this.setpointOf(id);
      // A room switched off is not being held back by the season; it is off
      // because somebody turned it off. Counting that as what the rule cost
      // would paint the whole lane red on a house with the heating away.
      const asking = ["heat", "heat_cool"].includes(
        this.liveOf(this.rooms.find((item) => item.id === id) || {}).mode);
      const demand = data.demand[id] || [];
      const ran = demand.map((value) => Boolean(value));
      const readings = room.points;
      // Below setpoint while nothing ran: what the season rule cost.
      const left = readings.map((value, i) =>
        asking && value !== null && setpoint !== null && !ran[i] && value < setpoint - 0.15);
      let ranHours = 0;
      let leftHours = 0;
      let degreeHours = 0;
      readings.forEach((value, i) => {
        if (ran[i]) ranHours += perBucket;
        if (left[i]) {
          leftHours += perBucket;
          degreeHours += Math.abs(value - setpoint) * perBucket;
        }
      });
      const seen = readings.filter((value) => value !== null);
      return {
        id, name: room.name, points: readings, setpoint, ran, left, asking,
        colour: ROOM_COLOURS[index % ROOM_COLOURS.length],
        ranHours, leftHours, degreeHours,
        low: seen.length ? Math.min(...seen) : null,
        high: seen.length ? Math.max(...seen) : null,
        ranShare: count ? Math.round((ran.filter(Boolean).length / count) * 100) : 0,
      };
    });

    return { data, limit, hysteresis, count, hours, perBucket, inSeason, rooms };
  }

  /** The same window replayed against other limits, with the dwell ignored. */
  whatIf(model) {
    const damped = model.data.series.damped;
    const known = damped.filter((value) => value !== null && value !== undefined);
    if (!known.length) return [];
    const current = model.limit;
    const candidates = [current - 2, current - 1, current, current + 1, current + 2];
    return candidates.map((limit) => {
      const inSeason = damped.map((value) => value !== null && value < limit);
      const share = Math.round((inSeason.filter(Boolean).length / model.count) * 100);
      let run = 0;
      let cold = 0;
      model.rooms.forEach((room) => {
        room.points.forEach((value, index) => {
          if (value === null || room.setpoint === null) return;
          const below = value < room.setpoint - 0.15;
          if (below && inSeason[index]) run += model.perBucket;
          if (below && !inSeason[index]) cold += model.perBucket;
        });
      });
      return {
        limit,
        inSeason: `${share} %`,
        run: `${run.toFixed(1)} h`,
        cold: `${cold.toFixed(1)} h`,
        current: Math.abs(limit - current) < 0.01,
        note: Math.abs(limit - current) < 0.01
          ? "what you have now"
          : limit > current ? "warmer, and the equipment runs more"
          : "colder, and it runs less",
      };
    });
  }

  laneOne(model) {
    const { data } = model;
    const width = 1000;
    const height = 230;
    const outs = [...data.series.outdoor, ...data.series.damped]
      .filter((value) => value !== null && value !== undefined);
    if (!outs.length) return { svg: `<p class="muted">Nothing recorded over this span yet.</p>`, top: "—", bottom: "—", limitTop: "50%" };
    const low = Math.min(...outs, model.limit - 2.4) - 0.6;
    const high = Math.max(...outs, model.limit + 2.4) + 0.6;
    const y = (value) => ((high - value) / (high - low)) * height;
    const x = (index) => (index / Math.max(1, model.count - 1)) * width;
    const line = (points) => {
      const parts = [];
      let open = false;
      points.forEach((value, index) => {
        if (value === null || value === undefined) { open = false; return; }
        parts.push(`${open ? "L" : "M"}${x(index).toFixed(1)},${y(value).toFixed(1)}`);
        open = true;
      });
      return parts.join(" ");
    };
    const spans = [];
    let from = -1;
    model.inSeason.forEach((on, index) => {
      if (on && from < 0) from = index;
      if ((!on || index === model.count - 1) && from >= 0) {
        spans.push([from, on ? index : index - 1]);
        from = -1;
      }
    });
    return {
      top: number(high, 0), bottom: number(low, 0),
      limitTop: `${((y(model.limit) / height) * 100).toFixed(1)}%`,
      series: [
        { label: "Outdoor", colour: "#5A6470", points: data.series.outdoor },
        { label: `${this.house.damping_hours} h average`, colour: "var(--accent)", points: data.series.damped },
      ],
      svg: `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none"
                 style="height:230px" data-lane data-height="${height}"
                 data-low="${low}" data-high="${high}">
        ${spans.map(([a, b]) =>
          `<rect x="${x(a).toFixed(1)}" y="0" width="${Math.max(1, x(b) - x(a)).toFixed(1)}"
                 height="${height}" fill="${LANE.season}"></rect>`).join("")}
        <rect x="0" y="${y(model.limit + model.hysteresis).toFixed(1)}" width="${width}"
              height="${Math.max(1, y(model.limit) - y(model.limit + model.hysteresis)).toFixed(1)}"
              fill="${LANE.band}"></rect>
        <line x1="0" y1="${y(model.limit).toFixed(1)}" x2="${width}" y2="${y(model.limit).toFixed(1)}"
              stroke="var(--accent-ink)" stroke-width="1" stroke-dasharray="7 6"
              vector-effect="non-scaling-stroke"></line>
        <path d="${line(data.series.outdoor)}" fill="none" stroke="#5A6470" stroke-width="1.5"
              vector-effect="non-scaling-stroke"></path>
        <path d="${line(data.series.damped)}" fill="none" stroke="var(--accent)" stroke-width="3"
              vector-effect="non-scaling-stroke"></path>
        <line class="crosshair" data-crosshair y1="0" y2="${height}" hidden
              vector-effect="non-scaling-stroke"></line>
      </svg>`,
    };
  }

  laneTwo(model) {
    const width = 1000;
    const height = 170;
    const shown = model.rooms.filter((room) => !this.hiddenSeries.has(room.id));
    const values = shown.flatMap((room) =>
      [...room.points.filter((value) => value !== null), room.setpoint])
      .filter((value) => value !== null && value !== undefined);
    if (!values.length) return { svg: `<p class="muted">No room readings over this span.</p>`, top: "—", bottom: "—" };
    const low = Math.min(...values) - 0.8;
    const high = Math.max(...values) + 0.8;
    const y = (value) => ((high - value) / (high - low)) * height;
    const x = (index) => (index / Math.max(1, model.count - 1)) * width;

    // A run of buckets, closed back along the setpoint, so the gap between a
    // room and what it was asked for is an area rather than a guess.
    const runs = (flags) => {
      const out = [];
      let from = -1;
      flags.forEach((on, index) => {
        if (on && from < 0) from = index;
        if (from >= 0 && (!on || index === flags.length - 1)) {
          const to = on ? index : index - 1;
          if (to - from >= 1) out.push([from, to]);
          from = -1;
        }
      });
      return out;
    };
    const area = (room, [from, to]) => {
      const up = [];
      for (let i = from; i <= to; i += 1) up.push(`${x(i).toFixed(1)},${y(room.points[i]).toFixed(1)}`);
      const back = [];
      for (let i = to; i >= from; i -= 1) back.push(`${x(i).toFixed(1)},${y(room.setpoint).toFixed(1)}`);
      return [...up, ...back].join(" ");
    };

    return {
      top: number(high, 0), bottom: number(low, 0),
      series: shown.map((room) => ({ label: room.name, colour: room.colour, points: room.points })),
      svg: `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" style="height:170px"
                 data-lane data-height="${height}" data-low="${low}" data-high="${high}">
        ${shown.filter((room) => room.setpoint !== null).flatMap((room) => [
          ...runs(room.left).map((run) =>
            `<polygon points="${area(room, run)}" fill="${LANE.deficit}"></polygon>`),
          ...runs(room.ran).map((run) =>
            `<polygon points="${area(room, run)}" fill="${LANE.ran}"></polygon>`),
        ]).join("")}
        ${shown.filter((room) => room.setpoint !== null).map((room) =>
          `<line x1="0" y1="${y(room.setpoint).toFixed(1)}" x2="${width}" y2="${y(room.setpoint).toFixed(1)}"
                 stroke="${room.colour}" stroke-width="1" stroke-dasharray="3 5" opacity="0.55"
                 vector-effect="non-scaling-stroke"></line>`).join("")}
        ${shown.map((room) => {
          const parts = [];
          let open = false;
          room.points.forEach((value, index) => {
            if (value === null || value === undefined) { open = false; return; }
            parts.push(`${open ? "L" : "M"}${x(index).toFixed(1)},${y(value).toFixed(1)}`);
            open = true;
          });
          return `<path d="${parts.join(" ")}" fill="none" stroke="${room.colour}"
                        stroke-width="2" vector-effect="non-scaling-stroke"></path>`;
        }).join("")}
        <line class="crosshair" data-crosshair y1="0" y2="${height}" hidden
              vector-effect="non-scaling-stroke"></line>
      </svg>`,
    };
  }

  /*
   * Forty-eight blocks per row, whatever the span, and every one of them
   * drawn.
   *
   * Only marking the blocks where something ran left an empty row that read
   * as a chart that had failed rather than as a week in which nothing ran —
   * which, in September, is the answer.
   */
  blocksOf(flags, count) {
    const total = 48;
    const per = count / total;
    return Array.from({ length: total }, (_, block) => {
      let on = false;
      for (let i = Math.floor(block * per); i < Math.floor((block + 1) * per); i += 1) {
        if (flags[i]) on = true;
      }
      return { x: (block * 20.83).toFixed(1), fill: on ? "#8A4A16" : "#1A1F24" };
    });
  }

  strips(model) {
    const share = (hours) => Math.round((hours / Math.max(0.01, model.hours)) * 100);
    const seasonHours = model.inSeason.filter(Boolean).length * model.perBucket;
    return [
      {
        label: "Heating season",
        blocks: this.blocksOf(model.inSeason, model.count),
        share: share(seasonHours),
      },
      ...model.rooms.map((room) => ({
        label: room.name,
        blocks: this.blocksOf(room.ran, model.count),
        share: share(room.ranHours),
      })),
    ];
  }

  stripNote(model) {
    const each = model.hours / 48;
    const size = each < 1
      ? `One block = ${Math.round(each * 60)} min.`
      : `One block = ${each.toFixed(1).replace(".0", "")} h.`;
    const ran = model.rooms.reduce((total, room) => total + room.ranHours, 0);
    return ran < 1
      ? `${size} Nothing ran — the season held everything idle.`
      : `${size} Filled means the room called for heat; the top row is the season itself.`;
  }

  historyTab() {
    const ranges = ["24h", "7d", "30d", "90d"];
    const picker = `<div class="ranges">${ranges.map((span) =>
      `<button data-span="${span}" class="${span === this.span ? "primary" : ""}">${span}</button>`).join("")}</div>`;
    if (!this.history) {
      return `<div class="page stack">
        <div class="page-head"><div class="grow"><h1>History</h1></div></div>
        ${picker}<p class="muted">Reading the history…</p></div>`;
    }
    const model = this.lanes();
    const one = this.laneOne(model);
    const two = this.laneTwo(model);
    // Kept for the pointer, which reads values out of the same arrays the
    // paths were drawn from rather than out of the DOM.
    this.plots = [one.series || [], two.series || []];
    this.plotWindow = { start: model.data.start, end: model.data.end, count: model.count };
    const damped = this.dampedNow();
    const ranHours = model.rooms.reduce((total, room) => total + room.ranHours, 0);
    const leftHours = model.rooms.reduce((total, room) => total + room.leftHours, 0);
    const degreeHours = model.rooms.reduce((total, room) => total + room.degreeHours, 0);
    const inSeasonNow = this.seasonSensor()?.state === "on";
    const margin = damped === null ? "no reading yet"
      : `${number(Math.abs(damped - model.limit))} K ${damped > model.limit ? "above" : "below"} the limit`;

    return `<div class="page stack">
      <div class="page-head"><div class="grow"><h1>History</h1>
        <p>Three lanes on one time axis: the weather and the season decision it drives,
        what each room did about it, and when equipment actually ran. The band is the
        hysteresis around the heating limit — the average has to cross the whole of it
        to change the season. Read it downwards: the limit at the top decides everything
        below it.</p></div></div>

      ${picker}

      <div class="summary">
        <div><div class="cap">Outdoor average now</div>
          <div class="big">${number(damped)}<span>°C</span></div>
          <div class="under">${margin}</div></div>
        <div><div class="cap">Season</div>
          <div class="big">${inSeasonNow ? "Heating" : "Out of season"}</div>
          <div class="under">${inSeasonNow ? `leaves above ${number(model.limit + model.hysteresis)} °C` : `returns below ${number(model.limit)} °C`}</div></div>
        <div><div class="cap">Equipment ran</div>
          <div class="big">${ranHours.toFixed(1)}<span>h</span></div>
          <div class="under">all rooms, this window</div></div>
        <div><div class="cap">Off target, left alone</div>
          <div class="big">${leftHours.toFixed(1)}<span>h</span></div>
          <div class="under">${degreeHours.toFixed(0)} K·h — what the season rule cost</div></div>
      </div>

      <div class="lanes">
        <div class="lane-cap">1 · The season decision
          <span class="aside">a change must last ${this.house.season_dwell_hours} hours</span></div>
        <div class="lane">
          <div class="gutter" style="height:230px">
            <span style="top:0">${one.top} °C</span>
            <span style="top:${one.limitTop};transform:translateY(-50%);color:var(--accent-ink);font-weight:600">${number(model.limit)}</span>
            <span style="bottom:0">${one.bottom} °C</span>
          </div>
          <div class="plot">${one.svg}<div class="readout" data-readout hidden></div></div>
        </div>
        <div class="lane-key">
          <span><i style="width:14px;height:2px;background:#5A6470"></i>outdoor reading</span>
          <span><i style="width:14px;height:3px;background:var(--accent)"></i>${this.house.damping_hours} h average — the decision follows this</span>
          <span><i style="width:14px;height:10px;background:${LANE.band}"></i>hysteresis, ${number(model.limit)} to ${number(model.limit + model.hysteresis)}</span>
          <span><i style="width:14px;height:10px;background:${LANE.season}"></i>season in effect</span>
        </div>

        <div class="lane-cap">2 · What the rooms did about it
          <span class="aside">shading is distance from setpoint</span></div>
        <div class="lane">
          <div class="gutter" style="height:170px">
            <span style="top:0">${two.top} °C</span>
            <span style="bottom:0">${two.bottom} °C</span>
          </div>
          <div class="plot">${two.svg}<div class="readout" data-readout hidden></div></div>
        </div>
        <div class="lane-key">
          <span><i style="width:14px;height:10px;background:${LANE.deficit}"></i>below setpoint, nothing ran</span>
          <span><i style="width:14px;height:10px;background:${LANE.ran}"></i>below setpoint, equipment ran</span>
          <span><i style="width:14px;height:0;border-top:1px dashed var(--muted)"></i>setpoint</span>
        </div>

        <div class="lane-cap">3 · When it ran
          <span class="aside">${escapeHtml(this.stripNote(model))}</span></div>
        ${this.strips(model).map((strip) => `<div class="strip">
          <span class="naming"><b>${escapeHtml(strip.label)}</b><small>${strip.share} %</small></span>
          <span class="plot"><svg viewBox="0 0 1000 16" preserveAspectRatio="none" style="height:16px">
            ${strip.blocks.map((block) =>
              `<rect x="${block.x}" y="0" width="18" height="16" fill="${block.fill}"></rect>`).join("")}
          </svg></span>
        </div>`).join("")}

        <div class="axis-row">
          <div>${when(model.data.start, this.span)}</div>
          <div>${when((model.data.start + model.data.end) / 2, this.span)}</div>
          <div>${when(model.data.end, this.span)}</div>
        </div>

        <div class="legend-row">
          ${model.rooms.map((room) =>
            `<button data-series="${room.id}" style="color:${this.hiddenSeries.has(room.id) ? "var(--disabled)" : "var(--ink)"}">
              <i style="background:${room.colour}"></i>${escapeHtml(room.name)}
            </button>`).join("")}
        </div>
      </div>

      <div class="section">
        <h2>Where the limit would sit</h2>
        <p>The same window replayed against other heating limits, dwell ignored. Raising
        the limit buys comfort by running the equipment more; lowering it does the
        reverse. Pick the row where the cold hours stop bothering you.</p>
        <div class="grid-table what-if">
          <div class="th">Heating limit</div><div class="th num">In season</div>
          <div class="th num">Would run</div><div class="th num">Cold hours</div><div class="th"></div>
          ${this.whatIf(model).map((row) => `
            <div class="td mono" style="${row.current ? "color:var(--accent-ink)" : ""}">${number(row.limit)} °C</div>
            <div class="td num">${row.inSeason}</div>
            <div class="td num">${row.run}</div>
            <div class="td num">${row.cold}</div>
            <div class="td quiet">${row.note}</div>`).join("")}
        </div>
        <p class="after">Computed from this window only. A limit is a property of the house,
        not of a week — check it again over 30 and 90 days before you move it on
        <a class="link" data-go="#house">House</a>.</p>
      </div>

      ${this.signature(model)}

      <div class="section">
        <div class="grid-table rooms-table">
          <div class="th">Room</div><div class="th num">Ran</div><div class="th num">Coldest</div>
          <div class="th num">Warmest</div><div class="th num">Swing</div><div class="th num">Off target</div>
          ${model.rooms.map((room) => `
            <div class="td">${escapeHtml(room.name)}</div>
            <div class="td num">${room.ranHours.toFixed(1)} h</div>
            <div class="td num">${number(room.low)}</div>
            <div class="td num">${number(room.high)}</div>
            <div class="td num">${room.low === null ? "—" : number(room.high - room.low)}</div>
            <div class="td num quiet">${room.leftHours.toFixed(1)} h</div>`).join("")}
        </div>
        <p class="after">Swing is warmest minus coldest — a wide swing is a room the sensor
        and the equipment disagree about.</p>
      </div>
    </div>`;
  }

  signature(model) {
    const days = model.data.daily || [];
    const limit = model.limit;
    const measured = model.data.balance_point;
    const width = 640;
    const height = 220;
    const box = { x: [44, 628], y: [6, 186] };
    const heatDays = days.filter((day) => day.hours > 0.25).length;
    const note = measured === null || measured === undefined
      ? `It needs a few weeks of heating weather before it can say anything;
         ${heatDays} ${heatDays === 1 ? "day" : "days"} with heating in this window.`
      : `Fitted over ${days.length} days: the balance point lands at ${number(measured)} °C
         against your limit of ${number(limit)} °C.`;

    let plot = `<text x="336" y="90" text-anchor="middle" fill="var(--disabled)"
      font-family="var(--font)" font-size="13">not enough heating weather to fit a line</text>`;
    let top = "—";
    let mid = "—";
    let from = "—";
    let to = "—";
    if (days.length) {
      const temps = days.map((day) => day.temp ?? day.outdoor);
      const lowT = Math.min(...temps) - 1;
      const highT = Math.max(...temps) + 1;
      const maxHours = Math.max(4, ...days.map((day) => day.hours)) * 1.2;
      const sx = (value) => box.x[0] + ((value - lowT) / Math.max(0.5, highT - lowT)) * (box.x[1] - box.x[0]);
      const sy = (value) => box.y[1] - (value / maxHours) * (box.y[1] - box.y[0]);
      top = `${maxHours.toFixed(0)} h`;
      mid = `${(maxHours / 2).toFixed(0)} h`;
      from = `${number(lowT, 0)} °C`;
      to = `${number(highT, 0)} °C`;
      const fit = measured === null || measured === undefined ? "" : (() => {
        const used = days.filter((day) => day.hours > 0);
        const count = used.length;
        const meanX = used.reduce((total, day) => total + (day.temp ?? day.outdoor), 0) / count;
        const meanY = used.reduce((total, day) => total + day.hours, 0) / count;
        const covariance = used.reduce((total, day) =>
          total + ((day.temp ?? day.outdoor) - meanX) * (day.hours - meanY), 0);
        const variance = used.reduce((total, day) =>
          total + ((day.temp ?? day.outdoor) - meanX) ** 2, 0);
        const slope = variance ? covariance / variance : 0;
        const at = (value) => Math.max(0, meanY + slope * (value - meanX));
        return `<line x1="${sx(lowT).toFixed(1)}" y1="${sy(at(lowT)).toFixed(1)}"
                      x2="${sx(highT).toFixed(1)}" y2="${sy(at(highT)).toFixed(1)}"
                      stroke="var(--accent-ink)" stroke-width="1.5" stroke-dasharray="6 5"></line>
                <line x1="${sx(measured).toFixed(1)}" y1="6" x2="${sx(measured).toFixed(1)}" y2="186"
                      stroke="var(--accent)" stroke-width="1"></line>`;
      })();
      plot = `${fit}${days.map((day) =>
        `<circle cx="${sx(day.temp ?? day.outdoor).toFixed(1)}" cy="${sy(day.hours).toFixed(1)}"
                 r="4" fill="var(--accent)"></circle>`).join("")}`;
    }

    return `<div class="section">
      <h2>Energy signature</h2>
      <p>One dot per day: hours of heating against that day's mean outdoor temperature.
      Where the line reaches zero is this house's balance point — the outdoor temperature
      above which it holds itself, which is what the heating limit of ${number(limit)} °C is
      meant to be and is currently a figure out of a book.</p>
      <div class="signature-split">
        <div class="signature-plot"><div class="holder">
          <div class="ytick" style="top:2.7%">${top}</div>
          <div class="ytick" style="top:43.6%">${mid}</div>
          <div class="ytick" style="top:84.5%">0</div>
          <svg viewBox="0 0 ${width} ${height}" style="display:block;width:100%;height:auto">
            <line x1="44" y1="6" x2="44" y2="186" stroke="var(--line)" stroke-width="1"></line>
            <line x1="44" y1="186" x2="628" y2="186" stroke="var(--line)" stroke-width="1"></line>
            ${plot}
          </svg>
          <div class="xrow"><div>${from}</div><div>mean outdoor temperature</div><div>${to}</div></div>
        </div></div>
        <div class="note">${note} Until the fit is stable the limit stays the figure you
          typed on <a class="link" data-go="#house">House</a>.</div>
      </div>
    </div>`;
  }

  // --- listeners ----------------------------------------------------------

  bind(root) {
    this.bindChrome(root);
    root.querySelectorAll("[data-add-room]").forEach((node) =>
      node.addEventListener("click", () => this.go("#rooms/new")));
    root.querySelectorAll("[data-history]").forEach((node) =>
      node.addEventListener("click", () => {
        this.hiddenSeries = new Set(
          this.rooms.filter((room) => room.id !== node.dataset.history).map((room) => room.id));
        this.go("#history");
      }));
    root.querySelectorAll("[data-mode]").forEach((node) =>
      node.addEventListener("change", () => this.setMode(node.dataset.mode, node.value)));
    root.querySelectorAll("[data-target]").forEach((node) =>
      node.addEventListener("change", () => this.setTarget(node.dataset.target, node.value)));
    root.querySelectorAll("[data-span]").forEach((node) =>
      node.addEventListener("click", () => {
        this.span = node.dataset.span;
        this.history = null;
        this.renderBody();
        this.loadHistory();
      }));
    root.querySelectorAll("[data-series]").forEach((node) =>
      node.addEventListener("click", () => {
        const key = node.dataset.series;
        if (this.hiddenSeries.has(key)) this.hiddenSeries.delete(key);
        else this.hiddenSeries.add(key);
        this.renderBody();
      }));
    root.querySelectorAll("[data-delete]").forEach((node) =>
      node.addEventListener("click", () => this.deleteRoom()));
    root.querySelectorAll("[data-drop-heater]").forEach((node) =>
      node.addEventListener("click", () => {
        this.draft = {
          ...this.draft,
          heaters: (this.draft.heaters || []).filter((entity) => entity !== node.dataset.dropHeater),
        };
        this.renderBody();
      }));
    root.querySelectorAll("[data-pick]").forEach((node) =>
      node.addEventListener("click", () => {
        this.picking = node.dataset.pick;
        this.renderBody();
        this.shadowRoot.querySelector("[data-entity-search]")?.focus();
      }));
    root.querySelectorAll("[data-clear]").forEach((node) =>
      node.addEventListener("click", () => this.chose(node.dataset.clear, null)));

    this.bindPicker(root);
    this.bindLanes(root);

    root.querySelectorAll("input[name], select[name]").forEach((field) => {
      field.addEventListener("input", () => this.take(field));
      field.addEventListener("change", () => this.take(field));
    });
  }

  /**
   * A crosshair and the readings under it.
   *
   * The design is a still picture and cannot draw a pointer; a chart you
   * cannot interrogate is one you look at once.
   */
  bindLanes(root) {
    const window = this.plotWindow;
    if (!window) return;
    root.querySelectorAll("[data-lane]").forEach((svg, laneIndex) => {
      const series = (this.plots || [])[laneIndex] || [];
      const line = svg.querySelector("[data-crosshair]");
      const readout = svg.parentElement.querySelector("[data-readout]");
      const height = Number(svg.dataset.height);
      const low = Number(svg.dataset.low);
      const high = Number(svg.dataset.high);

      const hide = () => {
        line?.setAttribute("hidden", "");
        readout?.setAttribute("hidden", "");
      };

      const show = (event) => {
        const box = svg.getBoundingClientRect();
        const fraction = (event.clientX - box.left) / box.width;
        const index = Math.round(fraction * (window.count - 1));
        if (!Number.isFinite(index) || index < 0 || index >= window.count) return hide();
        const at = (index / Math.max(1, window.count - 1)) * 1000;
        line?.setAttribute("x1", at.toFixed(1));
        line?.setAttribute("x2", at.toFixed(1));
        line?.removeAttribute("hidden");

        const moment = window.start + ((window.end - window.start) * index) / Math.max(1, window.count - 1);
        const rows = series
          .map((one) => ({ one, value: one.points[index] }))
          .filter((row) => row.value !== null && row.value !== undefined);
        readout.innerHTML = `<p class="when">${momentLabel(moment)}</p>
          ${rows.length ? rows.map((row) =>
            `<p><span class="swatch" style="background:${row.one.colour}"></span>
               ${escapeHtml(row.one.label)}<strong>${number(row.value)} °C</strong></p>`).join("")
            : `<p class="muted">Nothing recorded here.</p>`}`;
        // Inside the plot: a readout that follows the pointer off the right
        // edge widens the page.
        const side = fraction > 0.5 ? "left" : "right";
        readout.dataset.side = side;
        readout.style.left = side === "right" ? `${(fraction * 100).toFixed(2)}%` : "auto";
        readout.style.right = side === "left" ? `${(100 - fraction * 100).toFixed(2)}%` : "auto";
        readout.removeAttribute("hidden");
      };

      svg.addEventListener("pointermove", show);
      svg.addEventListener("pointerdown", show);
      svg.addEventListener("pointerleave", hide);
    });
  }

  bindPicker(root) {
    const picker = root.querySelector("[data-picker]");
    if (!picker) return;
    const name = picker.dataset.picker;
    const search = picker.querySelector("[data-entity-search]");
    const results = picker.querySelectorAll("[data-entity-option]");
    search?.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      let shown = 0;
      results.forEach((option) => {
        // Capped: a house has thousands of entities, and a list that long is
        // slower to draw than it is to scroll.
        const visible = (!query || option.dataset.entityTerms.includes(query)) && shown < 60;
        option.toggleAttribute("hidden", !visible);
        if (visible) shown += 1;
      });
    });
    search?.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        this.picking = null;
        this.renderBody();
      }
    });
    results.forEach((option) =>
      option.addEventListener("click", () => this.chose(name, option.dataset.entityOption)));
  }
}

/*
 * Home Assistant instantiates `ha-panel-<component_name>` for a panel
 * registered from an integration, so that is the name that has to exist. The
 * bare name is defined too, for anyone embedding the element directly.
 */
if (!customElements.get("ha-panel-room-thermostat-page")) {
  customElements.define("ha-panel-room-thermostat-page", RoomThermostatPage);
}
if (!customElements.get("room-thermostat-page")) {
  customElements.define("room-thermostat-page", class extends RoomThermostatPage {});
}
