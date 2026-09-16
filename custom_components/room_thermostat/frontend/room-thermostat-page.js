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

main { max-width:var(--content-max); margin:0 auto; padding:var(--page-inset); }
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

/* 8 ── ROOMS ──────────────────────────────────────────────── */

.page { padding:var(--s5) var(--page-inset) var(--s6); }
.page-head { margin-bottom:var(--s5); }
.page-head h1 { font:700 24px/1.2 var(--font); margin:0 0 var(--s2); }
.page-head p { margin:0; color:var(--muted); max-width:62ch; }

.room-grid { display:grid; gap:var(--s4);
  grid-template-columns:repeat(auto-fill, minmax(min(100%, 260px), 1fr)); }

.room-card { background:var(--surface); border:1px solid var(--line);
  display:flex; flex-direction:column; gap:var(--s3); padding:var(--s4); min-width:0; }
.room-card header { font:600 16px/1.2 var(--font); display:flex; align-items:center;
  gap:var(--s2); min-width:0; }
.room-card header .name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.room-card .reading { font:500 28px/1 var(--font); margin:0; display:flex;
  align-items:baseline; gap:var(--s2); }
.room-card .reading small { font:400 13px/1 var(--font); color:var(--muted); }
.room-card .controls { display:flex; gap:var(--s2); }
.room-card .controls select { flex:1; min-width:0; }
.room-card .controls .setpoint { position:relative; flex:none; width:6.5em; }
.room-card .controls .setpoint input { width:100%; padding-right:2.2em; }
.room-card .controls .setpoint span { position:absolute; right:var(--s3); top:50%;
  transform:translateY(-50%); color:var(--muted); font:400 13px/1 var(--font);
  pointer-events:none; }
.room-card footer { margin-top:auto; display:flex; align-items:center; gap:var(--s3); }

/* State is a fill, never an outline colour. */
.doing { display:inline-flex; align-items:center; gap:var(--s2); font:500 13px/1 var(--font);
  padding:var(--s2) var(--s3); background:var(--surface-raised); color:var(--muted); }
.doing::before { content:""; width:8px; height:8px; flex:none; background:var(--disabled); }
.doing.heating { color:var(--ink); } .doing.heating::before { background:var(--accent); }
.doing.cooling { color:var(--ink); } .doing.cooling::before { background:var(--info, #5B9DD9); }
.doing .why { color:var(--muted); font-weight:400; margin-left:var(--s2); }

.add-card { border:1px dashed var(--line); background:transparent; color:var(--muted);
  min-height:120px; }
.add-card:hover { color:var(--ink); background:var(--surface); }

.empty { text-align:center; padding:var(--s6) var(--s4); border:1px dashed var(--line); }
.empty h2 { font:700 18px/1.2 var(--font); margin:0 0 var(--s2); }
.empty p { color:var(--muted); margin:0 0 var(--s4); }


/* 9 ── EDITOR ─────────────────────────────────────────────── */

.editor { max-width:720px; display:flex; flex-direction:column; gap:var(--s4); }
.editor .field { display:flex; flex-direction:column; gap:var(--s2); }
.editor .field > span { font:500 14px/1 var(--font); }
.editor .field small { color:var(--muted); font:400 12px/1.5 var(--font); }
.editor .field .problem { color:var(--danger); }
.editor .field.invalid input, .editor .field.invalid select { border-color:var(--danger); }
.editor .row { display:flex; gap:var(--s3); align-items:flex-end; }
.editor .row .field { flex:1; min-width:0; }
/* A number is a few characters wide; a field the width of the form invites
   somebody to type a sentence into it. */
.editor .row input[type=number] { width:8em; flex:none; }
.editor .unit { color:var(--muted); font:400 13px/1 var(--font); padding-bottom:10px; }
.editor .actions { display:flex; align-items:center; gap:var(--s3); margin-top:var(--s3);
  padding-top:var(--s4); border-top:1px solid var(--line); flex-wrap:wrap; }
.editor .actions .danger { margin-left:auto; }
.foot { color:var(--muted); font:400 13px/1.6 var(--font); background:var(--surface);
  border-left:2px solid var(--line); padding:var(--s3) var(--s4); }
.foot strong { color:var(--ink); }


/* 10 ── HISTORY ───────────────────────────────────────────── */

.history { display:flex; flex-direction:column; gap:var(--s5); }
.spans { display:flex; gap:var(--s2); }
.spans button.active { background:var(--surface-raised); color:var(--ink); }

.chart { background:var(--surface); border:1px solid var(--line); padding:var(--s4);
  overflow-x:auto; }
.chart svg { display:block; width:100%; height:auto; min-width:320px; }

.season-band { fill:var(--accent-wash); }
.hysteresis-band { fill:var(--surface-raised); }
.limit { stroke:var(--muted); stroke-width:1; stroke-dasharray:4 4; }
.axis-line { stroke:var(--line); stroke-width:1; }
.line { fill:none; stroke-width:1.5; stroke-linejoin:round; }
.line.outdoor { stroke:var(--muted); }
.line.damped { stroke:var(--accent); stroke-width:2; }
.line.room { stroke:var(--ink); opacity:.75; }
.line.room-1 { stroke:#6FB1D9; } .line.room-2 { stroke:#9AD96F; } .line.room-3 { stroke:#D98FBF; }
text.axis { fill:var(--muted); font:400 11px/1 var(--font-mono); }
circle.day { fill:var(--accent); }
line.fit { stroke:var(--ink); stroke-width:1.5; }
line.measured { stroke:var(--accent); stroke-width:1; stroke-dasharray:3 3; }

.legend { display:flex; flex-wrap:wrap; gap:var(--s2); list-style:none; margin:var(--s3) 0 0;
  padding:0; }
.legend button { font:400 12px/1 var(--font); padding:var(--s2) var(--s3); }
.legend button.off { color:var(--disabled); }
.legend .swatch { display:inline-block; width:10px; height:2px; margin-right:6px;
  vertical-align:middle; }

.demand { display:flex; flex-direction:column; gap:var(--s2); }
.demand-row { display:flex; align-items:center; gap:var(--s3); min-width:0; }
.demand-name { width:9em; flex:none; color:var(--muted); font:400 13px/1 var(--font);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bars { display:flex; gap:1px; flex:1; min-width:0; height:18px; }
.bars i { flex:1; background:var(--accent); min-width:1px; }

.signature h3 { font:600 16px/1.2 var(--font); margin:0 0 var(--s3); }
.signature p { margin:var(--s3) 0 0; max-width:62ch; }

.rooms-table { width:100%; border-collapse:collapse; font:400 14px/1.4 var(--font); }
.rooms-table th { text-align:left; font:500 12px/1 var(--font); color:var(--muted);
  text-transform:uppercase; letter-spacing:.06em; padding:0 var(--s3) var(--s2) 0; }
.rooms-table td { padding:var(--s3) var(--s3) var(--s3) 0; border-top:1px solid var(--line);
  font-variant-numeric:tabular-nums; }


/* 11 ── RESPONSIVE ────────────────────────────────────────── */

@media (max-width:600px) {
  :host { --page-inset:var(--s3); }
  .page { padding:var(--s4) var(--page-inset) var(--s6); }
  .page-head h1 { font-size:20px; }
  .room-grid { grid-template-columns:minmax(0,1fr); }
  .editor .row { flex-direction:column; align-items:stretch; }
  .editor .actions .danger { margin-left:0; }
  .demand-name { width:6em; }
  /* A phone's keyboard zooms a field whose text is under 16px. */
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

/** What a room is doing, in words rather than identifiers. */
const ACTIONS = {
  idle: "Idle", heating: "Heating", cooling: "Cooling",
  drying: "Drying", fan: "Fan", off: "Off",
};

/** Home Assistant's mode names, in words rather than identifiers. */
const MODES = {
  off: "Off", heat: "Heat", cool: "Cool", heat_cool: "Auto",
  dry: "Dry", fan_only: "Fan",
};

const TABS = [
  ["rooms", "Rooms"],
  ["house", "House"],
  ["history", "History"],
];

class RoomThermostatPage extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.rooms = [];
    this.house = {};
    this.loaded = false;
    this.loading = true;
    this.busy = false;
    this.error = "";
    this.tab = "rooms";
    /** The id of the room being edited, "new" for one that is not saved yet. */
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
    else if (this.loaded) this.renderLive();
  }

  set narrow(value) { this.toggleAttribute("narrow", Boolean(value)); }
  set panel(value) { this._panel = value; }

  connectedCallback() {
    installFonts();
    window.addEventListener("hashchange", this.routeHandler);
    this.readRoute();
    this.render();
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
    this.draft = id
      ? id === "new"
        ? { name: "", cooling_strategy: "passthrough" }
        : { ...this.rooms.find((room) => room.id === id) }
      : null;
  }

  restoreRoute() {
    this.readRoute();
    this.render();
    if (this.tab === "history" && !this.history) this.loadHistory();
  }

  go(hash) {
    window.location.hash = hash;
  }

  async call(message) {
    if (!this._hass) throw new Error("Home Assistant is not ready");
    return this._hass.connection.sendMessagePromise(message);
  }

  async load() {
    this.loading = true;
    this.render();
    try {
      const record = await this.call({ type: "room_thermostat/rooms/list" });
      this.rooms = record.rooms;
      this.house = record.house;
      this.loaded = true;
      this.error = "";
    } catch (err) {
      this.error = err.message || "Could not read the record";
    }
    this.loading = false;
    this.restoreRoute();
  }

  /**
   * Redraw, but not while somebody is typing.
   *
   * Live values arrive constantly, and re-rendering the editor under a caret
   * moves it to the end of the field.
   */
  renderLive() {
    if (this.editing || this.tab === "house") return;
    this.render();
  }

  render() {
    if (!this.shadowRoot) return;
    this.shadowRoot.innerHTML = `<style>${STYLES}</style>${this.chrome()}`;
    this.bind();
  }

  chrome() {
    if (this.loading) return `<div class="page"><p class="muted">Reading the record…</p></div>`;
    const body = this.editing
      ? this.roomEditor()
      : this.tab === "house"
        ? this.houseTab()
        : this.tab === "history"
          ? this.historyTab()
          : this.roomsTab();
    return `
      <header class="app-bar">
        <span class="mark"></span>
        <nav class="crumbs">
          <a class="link" href="#rooms">Room Thermostat</a>
          ${this.editing ? `<span class="sep">/</span><span class="here">${escapeHtml(this.draft?.name || "New room")}</span>` : ""}
        </nav>
        <span class="spacer"></span>
        ${this.error ? `<span class="save-state dirty">${escapeHtml(this.error)}</span>` : ""}
      </header>
      <nav class="tabs">
        ${TABS.map(([key, label]) =>
          `<button data-tab="${key}" class="${key === this.tab && !this.editing ? "active" : ""}">${label}</button>`).join("")}
      </nav>
      <main class="page">${body}</main>`;
  }

  bind() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-tab]").forEach((button) => {
      button.addEventListener("click", () => this.go(`#${button.dataset.tab}`));
    });
    root.querySelectorAll("[data-mode]").forEach((select) => {
      select.addEventListener("change", () => this.setMode(select.dataset.mode, select.value));
    });
    root.querySelectorAll("[data-target]").forEach((input) => {
      input.addEventListener("change", () => this.setTarget(input.dataset.target, input.value));
    });
    root.querySelectorAll("[data-open]").forEach((element) => {
      element.addEventListener("click", () => this.go(`#rooms/${element.dataset.open}`));
    });
    root.querySelectorAll("[data-add-room]").forEach((button) => {
      button.addEventListener("click", () => this.go("#rooms/new"));
    });
    root.querySelectorAll("[data-span]").forEach((button) => {
      button.addEventListener("click", () => {
        this.span = button.dataset.span;
        this.loadHistory();
      });
    });
    root.querySelectorAll("[data-series]").forEach((button) => {
      button.addEventListener("click", () => {
        const key = button.dataset.series;
        if (this.hiddenSeries.has(key)) this.hiddenSeries.delete(key);
        else this.hiddenSeries.add(key);
        this.render();
      });
    });
    root.querySelectorAll("[data-cancel]").forEach((button) => {
      button.addEventListener("click", () => this.go("#rooms"));
    });
    root.querySelectorAll("[data-delete]").forEach((button) => {
      button.addEventListener("click", () => this.deleteRoom());
    });

    const form = root.querySelector("form");
    if (!form) return;
    // Written straight into the draft without re-rendering: a redraw on every
    // keystroke puts the caret at the end of the field.
    form.addEventListener("input", (event) => this.take(event.target));
    form.addEventListener("change", (event) => this.take(event.target));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (this.tab === "house") this.saveHouse();
      else this.saveRoom();
    });
  }

  // --- the tabs, each arriving in its own turn -------------------------

  /**
   * The thermostat entity for a room.
   *
   * Matched on the room id it publishes, not on its name: two rooms may be
   * named alike, and a room being renamed would lose its card mid-edit.
   */
  climateOf(room) {
    return Object.values(this._hass?.states || {}).find(
      (state) =>
        state.entity_id?.startsWith("climate.") &&
        state.attributes?.room_id === room.id,
    ) || null;
  }

  liveOf(room) {
    const state = this.climateOf(room);
    if (!state) return { missing: true };
    const attributes = state.attributes || {};
    const action = attributes.hvac_action || "idle";
    // Why it is doing nothing. "idle" on its own is what made the season
    // lockout look like a fault rather than a decision.
    let why = "";
    if (action === "idle" && state.state === "heat" && attributes.heating_season === false) {
      why = "out of heating season";
    } else if (action === "idle" && state.state === "cool" && attributes.cooling_season === false) {
      why = "out of cooling season";
    }
    return {
      entityId: state.entity_id,
      mode: state.state,
      modes: attributes.hvac_modes || [],
      temperature: attributes.current_temperature,
      humidity: attributes.current_humidity,
      target: attributes.temperature,
      action,
      why,
    };
  }

  roomCard(room) {
    const live = this.liveOf(room);
    if (live.missing) {
      return `<article class="room-card">
        <header><span class="name">${escapeHtml(room.name)}</span></header>
        <p class="muted">No reading — this room's thermostat has not started.</p>
        <footer><button data-open="${room.id}">Settings</button></footer>
      </article>`;
    }
    const reading = live.temperature === undefined || live.temperature === null
      ? `<span class="muted">No reading</span>`
      : `${Number(live.temperature).toFixed(1)} °C`;
    const humidity = live.humidity === undefined || live.humidity === null
      ? ""
      : `<small>${Math.round(live.humidity)} %</small>`;
    return `<article class="room-card">
      <header><span class="name">${escapeHtml(room.name)}</span></header>
      <p class="reading">${reading} ${humidity}</p>
      <div class="controls">
        <select data-mode="${room.id}" aria-label="Mode">
          ${live.modes.map((mode) =>
            `<option value="${mode}" ${mode === live.mode ? "selected" : ""}>${MODES[mode] || mode}</option>`).join("")}
        </select>
        <label class="setpoint">
          <input type="number" step="0.5" data-target="${room.id}" aria-label="Setpoint"
                 value="${live.target ?? ""}" ${live.target === undefined || live.target === null ? "disabled" : ""}>
          <span>°C</span>
        </label>
      </div>
      <p class="doing ${live.action}">${ACTIONS[live.action] || live.action}${live.why ? `<span class="why">· ${live.why}</span>` : ""}</p>
      <footer><button data-open="${room.id}">Settings</button></footer>
    </article>`;
  }

  roomsTab() {
    if (!this.rooms.length) {
      return `<div class="empty">
        <h2>No rooms yet</h2>
        <p>A room is a temperature sensor and whatever heats or cools it.</p>
        <button class="primary" data-add-room>Add a room</button>
      </div>`;
    }
    return `<div class="page-head">
        <h1>Rooms</h1>
        <p>What each room reads, what it is set to, and what it is doing.</p>
      </div>
      <div class="room-grid">
        ${this.rooms.map((room) => this.roomCard(room)).join("")}
        <button class="add-card" data-add-room>+ Add a room</button>
      </div>`;
  }

  async setMode(roomId, mode) {
    // A command, not a setting: it takes effect now and is not drafted.
    const live = this.liveOf(this.rooms.find((room) => room.id === roomId) || {});
    if (!live.entityId) return;
    await this._hass.callService("climate", "set_hvac_mode", {
      entity_id: live.entityId,
      hvac_mode: mode,
    });
  }

  async setTarget(roomId, value) {
    const live = this.liveOf(this.rooms.find((room) => room.id === roomId) || {});
    if (!live.entityId || value === "" || Number.isNaN(Number(value))) return;
    await this._hass.callService("climate", "set_temperature", {
      entity_id: live.entityId,
      temperature: Number(value),
    });
  }

  field(name, label, value, hint = "") {
    const problem = this.problems[name];
    return `<label class="field ${problem ? "invalid" : ""}">
      <span>${escapeHtml(label)}</span>
      <input name="${name}" value="${escapeHtml(value ?? "")}">
      ${problem ? `<small class="problem">${escapeHtml(PROBLEMS[problem] || problem)}</small>` : ""}
      ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
    </label>`;
  }

  number(name, label, value, unit, hint = "") {
    return `<label class="field">
      <span>${escapeHtml(label)}</span>
      <div class="row">
        <input name="${name}" type="number" step="0.5" value="${escapeHtml(value ?? "")}">
        <span class="unit">${escapeHtml(unit)}</span>
      </div>
      ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
    </label>`;
  }

  roomEditor() {
    const draft = this.draft || {};
    const isNew = !draft.id;
    return `<div class="page-head">
        <h1>${isNew ? "New room" : escapeHtml(draft.name || "Room")}</h1>
        <p>A room is a temperature sensor and whatever heats or cools it.</p>
      </div>
      <form class="editor">
        ${this.field("name", "Name", draft.name,
          "What this room is called, here and in Home Assistant.")}
        ${this.field("temperature_sensor", "Temperature sensor", draft.temperature_sensor,
          "The reason this integration exists: the room is controlled against this, never against the air conditioner's own sensor.")}
        ${this.field("humidity_sensor", "Humidity sensor", draft.humidity_sensor)}
        ${this.field("cooler", "Air conditioner", draft.cooler,
          "Any climate entity. Its fan, swing and preset lists are mirrored rather than replaced.")}
        ${this.field("heaters", "Heaters", (draft.heaters || []).join(", "),
          "Valves or switches, separated by commas. A radiator valve is a valve entity, not a switch.")}
        <label class="field"><span>Cooling strategy</span>
          <select name="cooling_strategy">
            <option value="passthrough" ${draft.cooling_strategy !== "gated" ? "selected" : ""}>Pass the setpoint to the unit</option>
            <option value="gated" ${draft.cooling_strategy === "gated" ? "selected" : ""}>Park the unit and gate it on the room's sensor</option>
          </select>
          <small>Gated is for a unit whose sensor reads its own recirculated air and stops while the room is still warm.</small>
        </label>
        ${this.number("frost_temperature", "Frost protection", draft.frost_temperature ?? 5, "°C",
          "Heats whatever the mode, whatever the season. A thermostat switched off must not be able to freeze a pipe.")}
        ${this.problems.base ? `<p class="problem">${escapeHtml(PROBLEMS[this.problems.base] || this.problems.base)}</p>` : ""}
        <div class="actions">
          <button class="primary" type="submit" ${this.busy ? "disabled" : ""}>${isNew ? "Add room" : "Save room"}</button>
          <button type="button" data-cancel>Cancel</button>
          ${isNew ? "" : `<button type="button" class="danger" data-delete>Delete room</button>`}
        </div>
      </form>`;
  }

  houseTab() {
    return `<div class="page-head"><h1>House</h1></div>
      <p class="muted">The seasons arrive next.</p>`;
  }

  historyTab() {
    return `<div class="page-head"><h1>History</h1></div>
      <p class="muted">The charts arrive next.</p>`;
  }

  async loadHistory() {}

  /** The draft as the record wants it: lists as lists, numbers as numbers. */
  roomPayload() {
    const draft = { ...this.draft };
    draft.heaters = String(draft.heaters ?? "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
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
    this.render();
    const payload = this.roomPayload();
    try {
      if (payload.id) {
        await this.call({
          type: "room_thermostat/rooms/update",
          room_id: payload.id,
          room: payload,
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
      this.render();
    }
  }

  async deleteRoom() {
    const name = this.draft?.name || "this room";
    // Irreversible, and it takes the device and the entities with it.
    if (!window.confirm(`Delete ${name}? Its thermostat, its sensors and its device go with it.`)) return;
    this.busy = true;
    this.render();
    try {
      await this.call({
        type: "room_thermostat/rooms/delete",
        room_id: this.draft.id,
      });
      this.busy = false;
      await this.load();
      this.go("#rooms");
    } catch (err) {
      this.error = err?.message || "Could not delete that room";
      this.busy = false;
      this.render();
    }
  }

  async saveHouse() {}

  take(field) {
    if (!field?.name) return;
    const value = field.type === "checkbox" ? field.checked : field.value;
    if (this.tab === "house" && !this.editing) {
      this.draftHouse = { ...(this.draftHouse || this.house), [field.name]: value };
    } else {
      this.draft = { ...(this.draft || {}), [field.name]: value };
    }
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
