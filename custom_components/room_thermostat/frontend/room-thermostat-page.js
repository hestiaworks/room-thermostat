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

/* 8 ── ROOMS ──────────────────────────────────────────────── */

/* Wider than the panel manager's workspace, which was three narrow columns.
   This page is cards and charts, and 1180px of it left half a large screen
   empty. */
.page { padding:var(--s5) var(--page-inset) var(--s6); max-width:1680px; margin:0 auto; }
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
.room-card .controls .select-wrap { flex:1; min-width:0; }
.room-card .controls select { width:100%; }
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


/* 9 ── PICKERS ────────────────────────────────────────────── */

.entity-picker { position:relative; }
.entity-results { position:absolute; left:0; right:0; z-index:5;
  border:1px solid var(--line); border-top:0; margin-top:-1px; max-height:280px;
  overflow:auto; overflow-x:hidden; background:var(--canvas); }
.entity-results button { display:flex; flex-direction:column; align-items:flex-start;
  justify-content:center; gap:2px; width:100%; height:52px; border:0; border-radius:0;
  background:transparent; padding:0 var(--s3); text-align:left; }
.entity-results button + button { border-top:1px solid var(--line); }
.entity-results b, .entity-results small { max-width:100%; overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap; }
.entity-results button:hover { background:var(--surface-raised); }
.entity-results b { font:400 14px/1.2 var(--font); }
.entity-results small { font:500 12px/1.3 var(--mono); color:var(--muted); }
.entity-results .none { padding:var(--s3); color:var(--muted); font:400 13px/1.4 var(--font); }
.entity-chosen { font:500 12px/1.3 var(--mono); color:var(--muted); }


/* 10 ── EDITOR ────────────────────────────────────────────── */

.editor { max-width:720px; display:flex; flex-direction:column; gap:var(--s4); }
/* A band label names the group beneath it and separates it from the one
   above with a rule, which is how this design separates anything. */
.band-label { font:500 12px/1 var(--font); letter-spacing:.08em; text-transform:uppercase;
  color:var(--muted); padding-top:var(--s4); border-top:1px solid var(--line); }
.editor > .band-label:first-child { padding-top:0; border-top:0; }
.editor .field { display:flex; flex-direction:column; gap:var(--s2); }
.editor .field > span { font:500 14px/1 var(--font); }
.editor .field small { color:var(--muted); font:400 12px/1.5 var(--font); }
.editor .field > span { font:500 14px/1 var(--font); }
.entity-list { display:flex; flex-direction:column; gap:var(--s2); }
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


/* 11 ── HISTORY ───────────────────────────────────────────── */

.history { display:flex; flex-direction:column; gap:var(--s5); }
.spans { display:flex; gap:var(--s2); }
.spans button.active { background:var(--surface-raised); color:var(--ink); }

.chart { background:var(--surface); border:1px solid var(--line); padding:var(--s4);
  overflow-x:auto; position:relative; }
.chart svg[data-timeline] { touch-action:none; }

line.crosshair { stroke:var(--ink); stroke-width:1; opacity:.5; }
circle.crosshair-dot { stroke:var(--canvas); stroke-width:1.5; }
circle.crosshair-dot.outdoor { fill:var(--muted); }
circle.crosshair-dot.damped { fill:var(--accent); }
circle.crosshair-dot.room-1 { fill:#6FB1D9; }
circle.crosshair-dot.room-2 { fill:#9AD96F; }
circle.crosshair-dot.room-3 { fill:#D98FBF; }

/* The readings under the pointer. Home Assistant puts these in a floating
   card; so does this, and it stays inside the chart rather than widening the
   page at the right-hand edge. */
.readout { position:absolute; top:var(--s4); z-index:4; pointer-events:none;
  background:var(--surface-raised); border:1px solid var(--line);
  padding:var(--s3); min-width:190px; }
.readout[data-side=right] { margin-left:var(--s3); }
.readout[data-side=left] { margin-right:var(--s3); }
.readout p { display:flex; align-items:center; gap:var(--s2);
  font:400 13px/1.6 var(--font); white-space:nowrap; }
.readout p strong { margin-left:auto; font-variant-numeric:tabular-nums; }
.readout .when { font:500 12px/1.4 var(--mono); color:var(--muted);
  padding-bottom:var(--s2); margin-bottom:var(--s2); border-bottom:1px solid var(--line); }
.readout .swatch { display:inline-block; width:10px; height:10px; flex:none;
  background:var(--muted); }
.readout .swatch.damped { background:var(--accent); }
.readout .swatch.room-1 { background:#6FB1D9; }
.readout .swatch.room-2 { background:#9AD96F; }
.readout .swatch.room-3 { background:#D98FBF; }
.chart svg { display:block; width:100%; height:auto; min-width:320px; }

/* A wash, not a block. The season is context behind the lines, and at full
   strength it read as the most important thing on the chart. */
.demand-row.season .bars i { background:var(--muted); }
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
text.measured-label { fill:var(--accent-ink); }
line.fit { stroke:var(--ink); stroke-width:1.5; }
line.measured { stroke:var(--accent); stroke-width:1; stroke-dasharray:3 3; }

.legend { display:flex; flex-wrap:wrap; gap:var(--s2); list-style:none; margin:var(--s3) 0 0;
  padding:0; }
.legend button { font:400 12px/1 var(--font); padding:var(--s2) var(--s3); }
.legend button.off { color:var(--disabled); }
.legend .swatch { display:inline-block; width:12px; height:2px; margin-right:6px;
  vertical-align:middle; background:var(--muted); }
.legend .swatch.damped { background:var(--accent); height:3px; }
.legend .swatch.room-1 { background:#6FB1D9; }
.legend .swatch.room-2 { background:#9AD96F; }
.legend .swatch.room-3 { background:#D98FBF; }

.demand { display:flex; flex-direction:column; gap:var(--s2); }
.demand-row { display:flex; align-items:center; gap:var(--s3); min-width:0; }
.demand-name { width:9em; flex:none; color:var(--muted); font:400 13px/1 var(--font);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
/* One bar per bucket, and there can be 168 of them. The row clips rather
   than pushes: a bar a pixel too wide would otherwise widen the page. */
.bars { display:flex; gap:1px; flex:1; min-width:0; height:18px; overflow:hidden; }
.bars i { flex:1 1 0; background:var(--accent); min-width:0; }

.signature h3 { font:600 16px/1.2 var(--font); margin:0 0 var(--s3); }
.signature p { margin:var(--s3) 0 0; max-width:62ch; }

.rooms-table { width:100%; border-collapse:collapse; font:400 14px/1.4 var(--font); }
.rooms-table th { text-align:left; font:500 12px/1 var(--font); color:var(--muted);
  text-transform:uppercase; letter-spacing:.06em; padding:0 var(--s3) var(--s2) 0; }
.rooms-table td { padding:var(--s3) var(--s3) var(--s3) 0; border-top:1px solid var(--line);
  font-variant-numeric:tabular-nums; }


/* 12 ── RESPONSIVE ────────────────────────────────────────── */

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

/**
 * A moment on the time axis, at the resolution the span deserves.
 *
 * A 24-hour chart wants a clock and a 90-day one wants a date; both on both
 * is noise.
 */
/** A moment in full, for the readout: the day and the time, both. */
const moment_label = (timestamp) => {
  const at = new Date(timestamp * 1000);
  return `${at.toLocaleDateString([], { day: "numeric", month: "short" })} ${at.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

const when = (timestamp, span) => {
  const at = new Date(timestamp * 1000);
  return span === "24h"
    ? at.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : at.toLocaleDateString([], { day: "numeric", month: "short" });
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
          ${this.editing
            ? `<button class="back" data-cancel aria-label="Back to rooms">←</button>
               <a class="link" href="#rooms">Rooms</a>
               <span class="sep">/</span>
               <span class="here">${escapeHtml(this.draft?.name || "New room")}</span>`
            : `<span class="here">Room Thermostat</span>`}
        </nav>
        <span class="spacer"></span>
        ${this.error ? `<span class="save-state dirty">${escapeHtml(this.error)}</span>` : ""}
      </header>
      ${this.editing ? "" : `<nav class="tabs">
        ${TABS.map(([key, label]) =>
          `<button data-tab="${key}" class="${key === this.tab ? "active" : ""}">${label}</button>`).join("")}
      </nav>`}
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
    root.querySelectorAll("[data-revert]").forEach((button) => {
      button.addEventListener("click", () => {
        this.draftHouse = null;
        this.render();
      });
    });
    root.querySelectorAll("[data-cancel]").forEach((button) => {
      button.addEventListener("click", () => this.go("#rooms"));
    });
    root.querySelectorAll("[data-delete]").forEach((button) => {
      button.addEventListener("click", () => this.deleteRoom());
    });

    this.bindPickers(root);
    this.bindTimeline(root);

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
        <div class="select-wrap">
          <select data-mode="${room.id}" aria-label="Mode">
            ${live.modes.map((mode) =>
              `<option value="${mode}" ${mode === live.mode ? "selected" : ""}>${MODES[mode] || mode}</option>`).join("")}
          </select>
        </div>
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

  entityLabel(state) {
    return `${state.attributes?.friendly_name || state.entity_id} · ${state.entity_id}`;
  }

  /**
   * An entity chosen by searching, rather than typed from memory.
   *
   * The hidden input carries the entity id, which is what the record wants;
   * the visible one carries a name somebody recognises. Typing clears the
   * hidden one, so a half-typed search can never be saved as an entity id.
   */
  entityPicker(name, label, selected, domains, hint = "", deviceClass = null) {
    const states = Object.values(this._hass?.states || {})
      .filter((state) => domains.includes(state.entity_id.split(".")[0]))
      .filter((state) =>
        !deviceClass || state.attributes?.device_class === deviceClass ||
        state.entity_id.startsWith("input_number.") || state.entity_id.startsWith("number."))
      .sort((first, second) => this.entityLabel(first).localeCompare(this.entityLabel(second)));
    const chosen = selected ? this._hass?.states?.[selected] : null;
    const display = chosen ? this.entityLabel(chosen) : selected || "";
    const problem = this.problems[name];
    return `<label class="field ${problem ? "invalid" : ""}">
      <span>${escapeHtml(label)}</span>
      <div class="entity-picker">
        <input type="hidden" name="${name}" value="${escapeHtml(selected || "")}">
        <input class="entity-search" data-entity-search type="search" autocomplete="off"
               value="${escapeHtml(display)}" placeholder="Search entities…"
               aria-label="${escapeHtml(label)}">
        <div class="entity-results" hidden>
          ${states.length ? states.map((state) => {
            const option = this.entityLabel(state);
            return `<button type="button" data-entity-option="${escapeHtml(state.entity_id)}"
                      data-entity-label="${escapeHtml(option)}"
                      data-entity-terms="${escapeHtml(option.toLowerCase())}">
                      <b>${escapeHtml(state.attributes?.friendly_name || state.entity_id)}</b>
                      <small>${escapeHtml(state.entity_id)}</small>
                    </button>`;
          }).join("") : `<p class="none">Nothing of that kind in this house.</p>`}
        </div>
      </div>
      ${problem ? `<small class="problem">${escapeHtml(PROBLEMS[problem] || problem)}</small>` : ""}
      ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
    </label>`;
  }

  /** Several entities of one kind, each picked the same way. */
  entityList(name, label, selected, domains, hint = "") {
    const values = [...(selected || []), ""];
    return `<div class="field"><span>${escapeHtml(label)}</span>
      <div class="entity-list" data-entity-list="${name}">
        ${values.map((value, index) => {
          const state = value ? this._hass?.states?.[value] : null;
          const display = state ? this.entityLabel(state) : value || "";
          const states = Object.values(this._hass?.states || {})
            .filter((item) => domains.includes(item.entity_id.split(".")[0]))
            .sort((first, second) => this.entityLabel(first).localeCompare(this.entityLabel(second)));
          return `<div class="entity-picker">
            <input type="hidden" data-list-value="${name}" value="${escapeHtml(value)}">
            <input class="entity-search" data-entity-search type="search" autocomplete="off"
                   value="${escapeHtml(display)}"
                   placeholder="${index === values.length - 1 ? "Add another…" : "Search entities…"}"
                   aria-label="${escapeHtml(label)}">
            <div class="entity-results" hidden>
              ${states.length ? states.map((item) => {
                const option = this.entityLabel(item);
                return `<button type="button" data-entity-option="${escapeHtml(item.entity_id)}"
                          data-entity-label="${escapeHtml(option)}"
                          data-entity-terms="${escapeHtml(option.toLowerCase())}">
                          <b>${escapeHtml(item.attributes?.friendly_name || item.entity_id)}</b>
                          <small>${escapeHtml(item.entity_id)}</small>
                        </button>`;
              }).join("") : `<p class="none">Nothing of that kind in this house.</p>`}
            </div>
          </div>`;
        }).join("")}
      </div>
      ${hint ? `<small>${escapeHtml(hint)}</small>` : ""}
    </div>`;
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
        ${this.entityPicker("temperature_sensor", "Temperature sensor", draft.temperature_sensor,
          ["sensor", "input_number", "number"],
          "The reason this integration exists: the room is controlled against this, never against the air conditioner's own sensor.",
          "temperature")}
        ${this.entityPicker("humidity_sensor", "Humidity sensor", draft.humidity_sensor,
          ["sensor", "input_number", "number"], "", "humidity")}
        ${this.entityPicker("cooler", "Air conditioner", draft.cooler, ["climate"],
          "Any climate entity. Its fan, swing and preset lists are mirrored rather than replaced.")}
        ${this.entityList("heaters", "Heaters", draft.heaters, ["valve", "switch", "input_boolean"],
          "A radiator valve is a valve entity, not a switch. A room may have several, and they open together.")}
        <label class="field"><span>Cooling strategy</span>
          <div class="select-wrap">
            <select name="cooling_strategy">
              <option value="passthrough" ${draft.cooling_strategy !== "gated" ? "selected" : ""}>Pass the setpoint to the unit</option>
              <option value="gated" ${draft.cooling_strategy === "gated" ? "selected" : ""}>Park the unit and gate it on the room's sensor</option>
            </select>
          </div>
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

  /** The heating season sensor, which is the only thing that knows the average. */
  seasonSensor() {
    return Object.values(this._hass?.states || {}).find(
      (state) =>
        state.entity_id?.startsWith("binary_sensor.") &&
        state.attributes?.damped !== undefined,
    ) || null;
  }

  /**
   * What the numbers on this page currently mean, in a sentence.
   *
   * A threshold whose far side you cannot see is what went wrong with bright
   * and dark on the panel: the setting was right and nobody could tell.
   */
  seasonExplainer() {
    const house = this.draftHouse || this.house;
    if (!house.outdoor_sensor) {
      return `<div class="foot">No outdoor temperature is set, so nothing is held
        back: every room heats and cools exactly as it would have before.</div>`;
    }
    const sensor = this.seasonSensor();
    const damped = sensor ? Number(sensor.attributes.damped) : null;
    if (damped === null || Number.isNaN(damped)) {
      return `<div class="foot">Waiting for a first reading from
        <strong>${escapeHtml(house.outdoor_sensor)}</strong>. Until one arrives
        nothing is held back.</div>`;
    }
    const limit = Number(house.heat_limit);
    const hysteresis = Number(house.heat_limit_hysteresis);
    const inSeason = sensor.state === "on";
    const next = inSeason
      ? `Heating is <strong>in season</strong>, and leaves once the average passes
         ${(limit + hysteresis).toFixed(1)} °C.`
      : `Heating is <strong>out of season</strong>, so a room below its setpoint stays
         idle. It comes back once the average falls below ${limit.toFixed(1)} °C.`;
    return `<div class="foot">The outdoor average is
      <strong>${damped.toFixed(1)} °C</strong> against a limit of ${limit.toFixed(1)}.
      ${next} A change has to last ${house.season_dwell_hours} hours — the dwell —
      before it counts, because a mild autumn dips below the limit for a few hours
      every night.</div>`;
  }

  houseTab() {
    const house = this.draftHouse || this.house;
    const dirty = this.draftHouse !== null;
    return `<div class="page-head">
        <h1>House</h1>
        <p>Decided once for the whole house, from an outdoor temperature. Rooms
        obey this; they have no seasonal settings of their own.</p>
      </div>
      <form class="editor house">
        <div class="band-label">Outdoor</div>
        ${this.entityPicker("outdoor_sensor", "Outdoor temperature", house.outdoor_sensor,
          ["sensor", "weather", "input_number", "number"],
          "A sensor or a weather entity. Put a sensor in shade: one in afternoon sun reads far too warm and would hold the heating off on a cold day. Leave it empty and nothing is held back at all.")}
        ${this.seasonExplainer()}

        <div class="band-label">Heating season</div>
        ${this.number("heat_limit", "Heating stops above", house.heat_limit, "°C",
          "The outdoor average above which the house heats itself — sun, cooking, bodies. Around 16 for an insulated house, higher for an old one.")}
        ${this.number("heat_limit_hysteresis", "Heating restarts this far below", house.heat_limit_hysteresis, "K")}
        ${this.number("damping_hours", "Averaging time", house.damping_hours, "hours",
          "The heating decision follows an average rather than the reading, so one warm afternoon does not end the season. Longer suits a heavy masonry house.")}
        ${this.number("season_dwell_hours", "A change must last", house.season_dwell_hours, "hours",
          "A mild autumn dips below the limit for a few hours every night. Nothing changes until it has lasted this long.")}

        <div class="band-label">Cooling season</div>
        ${this.number("cool_limit", "Cooling stops below", house.cool_limit, "°C",
          "Judged on the live reading rather than the average: a sunny afternoon in an otherwise cold week still overheats a room that afternoon.")}
        ${this.number("cool_limit_hysteresis", "Cooling restarts this far above", house.cool_limit_hysteresis, "K")}

        <div class="band-label">When the weather is wrong</div>
        ${this.number("heat_override", "Heat anyway this far below setpoint", house.heat_override, "K",
          "The weather is a guess and the room's own thermometer is not. Keep this well below your setpoint, or it will heat on the very evenings the limit exists to prevent.")}
        ${this.number("cool_override", "Cool anyway this far above setpoint", house.cool_override, "K")}

        <div class="actions">
          <button class="primary" type="submit" ${this.busy || !dirty ? "disabled" : ""}>Save the house</button>
          ${dirty ? `<button type="button" data-revert>Revert</button>` : `<span class="save-state">No unsaved changes</span>`}
        </div>
      </form>`;
  }

  async loadHistory() {
    this.history = null;
    this.render();
    try {
      this.history = await this.call({
        type: "room_thermostat/history",
        span: this.span,
      });
      this.error = "";
    } catch (err) {
      this.error = err?.message || "Could not read the history";
    }
    this.render();
  }

  /**
   * A path through bucketed values, broken wherever there is a gap.
   *
   * A sensor that was offline did not read zero, so joining across a gap
   * draws a plunge that never happened. Each run of real values is its own
   * move-and-line.
   */
  path(points, x, y) {
    let d = "";
    let open = false;
    points.forEach((value, index) => {
      if (value === null || value === undefined) {
        open = false;
        return;
      }
      d += `${open ? "L" : "M"}${x(index).toFixed(1)},${y(value).toFixed(1)} `;
      open = true;
    });
    return d.trim();
  }

  timelineSeries(data) {
    const rooms = Object.entries(data.series.rooms);
    return [
      { key: "outdoor", label: "Outdoor", points: data.series.outdoor, className: "outdoor" },
      { key: "damped", label: "Outdoor average", points: data.series.damped, className: "damped" },
      ...rooms.map(([id, room], index) => ({
        key: id,
        label: room.name,
        points: room.points,
        className: `room room-${(index % 3) + 1}`,
      })),
    ];
  }

  timeline(data) {
    const width = 960;
    const height = 280;
    const pad = { left: 40, right: 14, top: 14, bottom: 26 };
    const house = this.house;
    const limit = Number(house.heat_limit);
    const hysteresis = Number(house.heat_limit_hysteresis);
    const shown = this.timelineSeries(data).filter((line) => !this.hiddenSeries.has(line.key));
    const values = shown
      .flatMap((line) => line.points)
      .filter((value) => value !== null && value !== undefined);
    if (!values.length) {
      return `<div class="chart"><p class="muted">Nothing recorded over this span yet.</p></div>`;
    }
    const low = Math.floor(Math.min(limit - 2, ...values));
    const high = Math.ceil(Math.max(limit + hysteresis + 2, ...values));
    const x = (index) =>
      pad.left + (index / Math.max(1, data.buckets - 1)) * (width - pad.left - pad.right);
    const y = (value) =>
      pad.top + (1 - (value - low) / Math.max(1, high - low)) * (height - pad.top - pad.bottom);
    // Everything the crosshair needs to answer a hover, kept beside the
    // drawing rather than recomputed from the DOM.
    this.plot = { data, shown, width, height, pad, low, high };

    return `<div class="chart">
      <svg viewBox="0 0 ${width} ${height}" role="img" data-timeline
           aria-label="Outdoor and indoor temperatures against the heating limit">
        <rect class="hysteresis-band" x="${pad.left}" y="${y(limit + hysteresis).toFixed(1)}"
              width="${width - pad.left - pad.right}"
              height="${Math.max(1, y(limit) - y(limit + hysteresis)).toFixed(1)}"></rect>
        <line class="limit" x1="${pad.left}" x2="${width - pad.right}"
              y1="${y(limit).toFixed(1)}" y2="${y(limit).toFixed(1)}"></line>
        ${shown.map((line) =>
          `<path class="line ${line.className}" d="${this.path(line.points, x, y)}"></path>`).join("")}
        <text class="axis" x="4" y="${(y(high) + 8).toFixed(1)}">${high}</text>
        <text class="axis" x="4" y="${y(limit).toFixed(1)}">${limit.toFixed(0)}</text>
        <text class="axis" x="4" y="${y(low).toFixed(1)}">${low}</text>
        <text class="axis" x="${pad.left}" y="${height - 6}">${when(data.start, this.span)}</text>
        <text class="axis" text-anchor="end" x="${width - pad.right}" y="${height - 6}">${when(data.end, this.span)}</text>
        <line class="crosshair" data-crosshair y1="${pad.top}" y2="${height - pad.bottom}" hidden></line>
        <g data-crosshair-dots hidden></g>
      </svg>
      <div class="readout" data-readout hidden></div>
      <ul class="legend">
        ${this.timelineSeries(data).map((line) =>
          `<li><button data-series="${line.key}" class="${this.hiddenSeries.has(line.key) ? "off" : ""}">
            <span class="swatch ${line.className}"></span>${escapeHtml(line.label)}
          </button></li>`).join("")}
      </ul>
    </div>`;
  }

  /** The season spans as one value per bucket, to sit under the same axis. */
  seasonBuckets(data) {
    const width = (data.end - data.start) / data.buckets;
    return Array.from({ length: data.buckets }, (_, index) => {
      const at = data.start + (index + 0.5) * width;
      return data.seasons.some(([from, to]) => at >= from && at < to) ? 1 : 0;
    });
  }

  /**
   * Which bucket a pointer is over, and what every line reads there.
   *
   * A chart you cannot interrogate is a picture. The numbers are the reason
   * to open it.
   */
  bindTimeline(root) {
    const svg = root.querySelector("[data-timeline]");
    const plot = this.plot;
    if (!svg || !plot) return;
    const line = svg.querySelector("[data-crosshair]");
    const dots = svg.querySelector("[data-crosshair-dots]");
    const readout = root.querySelector("[data-readout]");
    const { data, shown, width, height, pad, low, high } = plot;
    const x = (index) =>
      pad.left + (index / Math.max(1, data.buckets - 1)) * (width - pad.left - pad.right);
    const y = (value) =>
      pad.top + (1 - (value - low) / Math.max(1, high - low)) * (height - pad.top - pad.bottom);

    const hide = () => {
      line.setAttribute("hidden", "");
      dots.setAttribute("hidden", "");
      readout.setAttribute("hidden", "");
    };

    const show = (event) => {
      const box = svg.getBoundingClientRect();
      // The viewBox scales: a pointer's pixel is not the chart's unit.
      const at = ((event.clientX - box.left) / box.width) * width;
      const index = Math.round(
        ((at - pad.left) / Math.max(1, width - pad.left - pad.right)) * (data.buckets - 1));
      if (index < 0 || index >= data.buckets) return hide();

      line.setAttribute("x1", x(index).toFixed(1));
      line.setAttribute("x2", x(index).toFixed(1));
      line.removeAttribute("hidden");

      const readings = shown
        .map((series) => ({ series, value: series.points[index] }))
        .filter((row) => row.value !== null && row.value !== undefined);
      dots.innerHTML = readings.map((row) =>
        `<circle class="crosshair-dot ${row.series.className}" r="3"
                 cx="${x(index).toFixed(1)}" cy="${y(row.value).toFixed(1)}"></circle>`).join("");
      dots.removeAttribute("hidden");

      const moment = data.start + ((data.end - data.start) * index) / Math.max(1, data.buckets - 1);
      readout.innerHTML = `<p class="when">${moment_label(moment)}</p>
        ${readings.map((row) =>
          `<p><span class="swatch ${row.series.className}"></span>
             ${escapeHtml(row.series.label)}
             <strong>${row.value.toFixed(1)} °C</strong></p>`).join("")
          || `<p class="muted">Nothing recorded here.</p>`}`;
      // Kept inside the chart: a readout that follows the pointer off the
      // right-hand edge widens the page.
      const side = index > data.buckets / 2 ? "left" : "right";
      readout.dataset.side = side;
      readout.style.left = side === "right"
        ? `${((x(index) / width) * 100).toFixed(2)}%`
        : "auto";
      readout.style.right = side === "left"
        ? `${(100 - (x(index) / width) * 100).toFixed(2)}%`
        : "auto";
      readout.removeAttribute("hidden");
    };

    svg.addEventListener("pointermove", show);
    svg.addEventListener("pointerdown", show);
    svg.addEventListener("pointerleave", hide);
  }

  demandRows(data) {
    const rooms = Object.entries(data.demand);
    // The season goes here rather than as a wash behind the chart: a block
    // that size was the loudest thing on a plot of thin lines, and down here
    // it sits under the same axis and says its own name.
    const season = `<div class="demand-row season">
      <span class="demand-name">Heating season</span>
      <span class="bars">${this.seasonBuckets(data).map((value) =>
        `<i style="opacity:${value ? 1 : 0.06}"></i>`).join("")}</span>
    </div>`;
    if (!rooms.length) return `<div class="demand">${season}</div>`;
    return `<div class="demand">
      ${season}
      ${rooms.map(([roomId, points]) => {
        const name = data.series.rooms[roomId]?.name || roomId;
        return `<div class="demand-row">
          <span class="demand-name">${escapeHtml(name)}</span>
          <span class="bars">${points.map((value) =>
            `<i style="opacity:${value === null || value === undefined ? 0 : Math.max(0.06, value).toFixed(2)}"></i>`).join("")}</span>
        </div>`;
      }).join("")}
    </div>`;
  }

  /** The fitted line's height at an outdoor temperature, for drawing it. */
  hoursAt(days, outdoor) {
    const used = days.filter((day) => day.hours > 0);
    if (used.length < 3) return 0;
    const count = used.length;
    const meanX = used.reduce((total, day) => total + day.outdoor, 0) / count;
    const meanY = used.reduce((total, day) => total + day.hours, 0) / count;
    const covariance = used.reduce(
      (total, day) => total + (day.outdoor - meanX) * (day.hours - meanY), 0);
    const variance = used.reduce((total, day) => total + (day.outdoor - meanX) ** 2, 0);
    if (!variance) return meanY;
    return Math.max(0, meanY + (covariance / variance) * (outdoor - meanX));
  }

  /**
   * One dot per day: hours of heating against that day's mean outdoor
   * temperature. Every heated building draws this line, and where it reaches
   * zero is the balance point — the temperature above which the house holds
   * itself, measured from days actually lived through rather than estimated.
   */
  signature(data) {
    const days = data.daily || [];
    const limit = Number(this.house.heat_limit);
    if (days.length < 10) {
      return `<section class="signature">
        <h3>Energy signature</h3>
        <p class="muted">One dot per day: hours of heating against that day's
        mean outdoor temperature. Where the line reaches zero is this house's
        balance point — the outdoor temperature above which it holds itself,
        which is what the heating limit of ${limit.toFixed(1)} °C is meant to be
        and is currently a figure out of a book. It needs a few weeks of heating
        weather before it can say anything; ${days.length}
        day${days.length === 1 ? "" : "s"} so far.</p>
      </section>`;
    }
    const width = 560;
    const height = 280;
    const pad = { left: 44, right: 16, top: 16, bottom: 30 };
    const maxHours = Math.max(6, ...days.map((day) => day.hours));
    const measured = data.balance_point;
    const outs = days.map((day) => day.outdoor);
    const minOut = Math.floor(Math.min(...outs));
    const maxOut = Math.ceil(Math.max(...outs, measured ?? -Infinity, limit));
    const x = (value) =>
      pad.left + ((value - minOut) / Math.max(1, maxOut - minOut)) * (width - pad.left - pad.right);
    const y = (value) =>
      pad.top + (1 - value / maxHours) * (height - pad.top - pad.bottom);

    const fit = measured === null || measured === undefined
      ? ""
      : `<line class="fit" x1="${x(minOut).toFixed(1)}" y1="${y(this.hoursAt(days, minOut)).toFixed(1)}"
               x2="${x(measured).toFixed(1)}" y2="${y(0).toFixed(1)}"></line>
         <line class="measured" x1="${x(measured).toFixed(1)}" x2="${x(measured).toFixed(1)}"
               y1="${pad.top}" y2="${y(0).toFixed(1)}"></line>`;

    const verdict = measured === null || measured === undefined
      ? `<p class="muted">Not enough days that used heat to draw a line through yet.</p>`
      : `<p>Measured balance point <strong>${measured.toFixed(1)} °C</strong>, against a
         heating limit of ${limit.toFixed(1)}. ${
          Math.abs(measured - limit) < 0.5
            ? "Your limit is where this house says it should be."
            : measured < limit
              ? `The house holds itself ${(limit - measured).toFixed(1)} °C colder than the
                 limit assumes, so heating runs on days it need not.`
              : `The house wants heat ${(measured - limit).toFixed(1)} °C warmer than the
                 limit allows, so it is held back on days it would use it.`}</p>`;

    return `<section class="signature">
      <h3>Energy signature</h3>
      <div class="chart">
        <svg viewBox="0 0 ${width} ${height}" role="img"
             aria-label="Heating hours per day against that day's mean outdoor temperature">
          <line class="limit" x1="${x(limit).toFixed(1)}" x2="${x(limit).toFixed(1)}"
                y1="${pad.top}" y2="${y(0).toFixed(1)}"></line>
          <text class="axis" text-anchor="middle" x="${x(limit).toFixed(1)}" y="${(pad.top + 10).toFixed(1)}">limit</text>
          ${fit}
          ${days.map((day) =>
            `<circle class="day" cx="${x(day.outdoor).toFixed(1)}" cy="${y(day.hours).toFixed(1)}" r="3"></circle>`).join("")}
          <line class="axis-line" x1="${pad.left}" x2="${width - pad.right}"
                y1="${y(0).toFixed(1)}" y2="${y(0).toFixed(1)}"></line>
          <text class="axis" x="4" y="${(y(maxHours) + 8).toFixed(1)}">${maxHours.toFixed(0)} h</text>
          <text class="axis" x="4" y="${y(0).toFixed(1)}">0</text>
          <text class="axis" x="${x(minOut).toFixed(1)}" y="${height - 8}">${minOut} °C</text>
          <text class="axis" text-anchor="end" x="${x(maxOut).toFixed(1)}" y="${height - 8}">${maxOut} °C</text>
          ${measured === null || measured === undefined ? "" :
            `<text class="axis measured-label" text-anchor="middle" x="${x(measured).toFixed(1)}" y="${height - 8}">${measured.toFixed(1)}</text>
             <text class="axis measured-label" text-anchor="middle" x="${x(measured).toFixed(1)}" y="${(pad.top + 10).toFixed(1)}">measured</text>`}
        </svg>
      </div>
      ${verdict}
    </section>`;
  }

  /**
   * The rooms against each other. Counting, not modelling — and it points at
   * which room is the problem without pretending to know why.
   */
  roomTable(data) {
    const rows = Object.entries(data.demand).map(([roomId, points]) => {
      const room = data.series.rooms[roomId];
      const ran = points.filter((value) => value).length;
      const readings = (room?.points || []).filter((value) => value !== null && value !== undefined);
      const low = readings.length ? Math.min(...readings) : null;
      const high = readings.length ? Math.max(...readings) : null;
      return {
        name: room?.name || roomId,
        ran: Math.round((ran / Math.max(1, data.buckets)) * 100),
        low, high,
        swing: low === null ? null : high - low,
      };
    }).sort((first, second) => second.ran - first.ran);
    if (!rows.length) return "";
    return `<table class="rooms-table">
      <thead><tr><th>Room</th><th>Ran</th><th>Coldest</th><th>Warmest</th><th>Swing</th></tr></thead>
      <tbody>${rows.map((row) => `<tr>
        <td>${escapeHtml(row.name)}</td>
        <td>${row.ran} %</td>
        <td>${row.low === null ? "—" : row.low.toFixed(1)}</td>
        <td>${row.high === null ? "—" : row.high.toFixed(1)}</td>
        <td>${row.swing === null ? "—" : row.swing.toFixed(1)}</td>
      </tr>`).join("")}</tbody>
    </table>`;
  }

  historyTab() {
    const spans = `<nav class="spans">
      ${["24h", "7d", "30d", "90d"].map((span) =>
        `<button data-span="${span}" class="${span === this.span ? "active" : ""}">${span}</button>`).join("")}
    </nav>`;
    if (!this.history) {
      return `<div class="page-head"><h1>History</h1></div>${spans}
        <p class="muted">Reading the history…</p>`;
    }
    const data = this.history;
    return `<div class="page-head">
        <h1>History</h1>
        <p>One time axis: what it was like outside, what each room read, and
        when the heating ran. The band is the hysteresis around the heating
        limit — the average has to cross the whole of it to change the season.</p>
      </div>
      <div class="history">
        ${spans}
        ${this.timeline(data)}
        ${this.demandRows(data)}
        ${this.signature(data)}
        ${this.roomTable(data)}
      </div>`;
  }

  /** The draft as the record wants it: lists as lists, numbers as numbers. */
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

  /** The draft as the record wants it: numbers as numbers, an empty source
   *  as null, because clearing it is how seasons are switched off. */
  housePayload() {
    const draft = { ...(this.draftHouse || {}) };
    if (draft.outdoor_sensor !== undefined && !String(draft.outdoor_sensor).trim()) {
      draft.outdoor_sensor = null;
    }
    for (const key of Object.keys(draft)) {
      if (key !== "outdoor_sensor" && draft[key] !== null) draft[key] = Number(draft[key]);
    }
    return draft;
  }

  async saveHouse() {
    this.busy = true;
    this.render();
    try {
      await this.call({
        type: "room_thermostat/house/update",
        house: this.housePayload(),
      });
      this.draftHouse = null;
      this.busy = false;
      await this.load();
    } catch (err) {
      this.error = err?.message || "Could not save the house";
      this.busy = false;
      this.render();
    }
  }

  bindPickers(root) {
    root.querySelectorAll("[data-entity-search]").forEach((input) => {
      const picker = input.closest(".entity-picker");
      const results = picker?.querySelector(".entity-results");
      const hidden = picker?.querySelector("input[type=hidden]");

      const filter = (query = input.value.trim().toLowerCase()) => {
        let shown = 0;
        results?.querySelectorAll("[data-entity-option]").forEach((option) => {
          // Capped: a house has thousands of entities and a list that long is
          // slower to draw than it is to scroll.
          const visible = (!query || option.dataset.entityTerms.includes(query)) && shown < 60;
          option.toggleAttribute("hidden", !visible);
          if (visible) shown += 1;
        });
        if (results) results.hidden = false;
      };

      /*
       * Opening shows everything and selects what is there, rather than
       * filtering by the name already chosen. Filtering by it offers one
       * result — the thing you already have — which is the least useful list
       * possible when what you want is to change it.
       */
      const open = () => {
        input.select();
        filter("");
      };
      // Focus is how a keyboard reaches it; click is how a pointer does, and
      // a pointer clicking an already-focused field expects the list back.
      input.addEventListener("focus", open);
      input.addEventListener("click", open);
      input.addEventListener("input", () => {
        // Typing invalidates the choice. A half-typed search must never be
        // saved as though it were an entity id.
        if (hidden) {
          hidden.value = "";
          this.takePicker(hidden);
        }
        filter();
      });

      results?.querySelectorAll("[data-entity-option]").forEach((option) => {
        option.addEventListener("click", () => {
          if (hidden) {
            hidden.value = option.dataset.entityOption;
            this.takePicker(hidden);
          }
          input.value = option.dataset.entityLabel;
          results.hidden = true;
          // A list gains an empty row as soon as its last one is filled.
          if (hidden?.dataset.listValue) this.render();
        });
      });
    });

    // Clicking anywhere else closes whichever list is open.
    root.addEventListener("pointerdown", (event) => {
      const inside = event.composedPath().find(
        (node) => node?.classList?.contains("entity-picker"));
      root.querySelectorAll(".entity-results:not([hidden])").forEach((results) => {
        if (results.closest(".entity-picker") !== inside) results.hidden = true;
      });
    }, true);
  }

  /** A picker's hidden input, written into whichever draft is open. */
  takePicker(hidden) {
    const list = hidden.dataset.listValue;
    if (list) {
      const values = [...this.shadowRoot.querySelectorAll(`[data-list-value="${list}"]`)]
        .map((input) => input.value)
        .filter(Boolean);
      this.draft = { ...(this.draft || {}), [list]: values };
      return;
    }
    this.take(hidden);
  }

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
