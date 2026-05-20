/* ==========================================================================
 * chat_scroll.js — Auto-scroll chat containers during streaming.
 *
 * Behaviour
 * ---------
 * • While the user is within THRESHOLD px of the bottom, every DOM mutation
 *   (new token, new message element) triggers an instant scroll to the bottom.
 * • If the user manually scrolls up, auto-scroll pauses until they return to
 *   within THRESHOLD px of the bottom.
 * • Uses requestAnimationFrame to coalesce rapid successive mutation callbacks
 *   into a single scroll per animation frame — no performance cost during
 *   high-frequency streaming.
 *
 * Containers watched (by HTML id)
 * --------------------------------
 *   #chat-messages-main      → full-page /chat
 *   #chat-messages-floating  → floating chat popup (conditionally mounted)
 *
 * The polling loop handles the floating chat's conditional render: it
 * re-attaches the observer whenever the element re-appears in the DOM and
 * disconnects it cleanly when the element is removed.
 * ========================================================================== */

(function () {
  "use strict";

  /* ── config ────────────────────────────────────────────────────────────── */
  var IDS = [
    "chat-messages-main",
    "chat-messages-floating",
    "chat-messages-admin",
  ];
  var THRESHOLD = 80; /* px — distance from bottom considered "near bottom"  */
  var POLL_MS = 300; /* ms — interval for checking container presence       */

  /* ── per-container state ────────────────────────────────────────────────── */
  /*
   * state[id] = {
   *   el:         HTMLElement,
   *   observer:   MutationObserver,
   *   nearBottom: boolean,   // updated by the scroll listener
   *   rafPending: boolean,   // rAF dedup flag
   * }
   */
  var state = {};

  /* ── helpers ────────────────────────────────────────────────────────────── */

  function isNearBottom(el) {
    return el.scrollHeight - el.scrollTop - el.clientHeight < THRESHOLD;
  }

  function scrollToBottom(el) {
    /* Instant jump — smooth scroll lags behind fast streaming and feels wrong */
    el.scrollTop = el.scrollHeight;
  }

  /* ── setup / teardown ───────────────────────────────────────────────────── */

  function setup(id) {
    var el = document.getElementById(id);
    if (!el) return;

    /* Same element instance already observed → nothing to do */
    if (state[id] && state[id].el === el) return;

    /* Element was replaced (re-mount after conditional render) → clean up */
    teardown(id);

    var entry = {
      el: el,
      observer: null,
      nearBottom: true /* Assume user is at bottom when container first appears */,
      rafPending: false,
    };

    /* ── scroll listener: track user intent ── */
    el.addEventListener(
      "scroll",
      function () {
        entry.nearBottom = isNearBottom(el);
      },
      { passive: true },
    );

    /* ── MutationObserver: react to streaming / new messages ── */
    var observer = new MutationObserver(function () {
      /* Skip if user scrolled up OR a scroll is already queued this frame */
      if (!entry.nearBottom || entry.rafPending) return;

      entry.rafPending = true;
      requestAnimationFrame(function () {
        entry.rafPending = false;
        /* Re-check nearBottom: user might have scrolled during the frame */
        if (entry.nearBottom) {
          scrollToBottom(entry.el);
        }
      });
    });

    observer.observe(el, {
      childList: true /* New message elements being appended           */,
      subtree: true /* Changes anywhere inside the scroll container  */,
      characterData: true /* Text-node updates (streaming token by token)  */,
    });

    entry.observer = observer;
    state[id] = entry;
  }

  function teardown(id) {
    if (!state[id]) return;
    if (state[id].observer) state[id].observer.disconnect();
    delete state[id];
  }

  /* ── polling loop ───────────────────────────────────────────────────────── */
  /*
   * Runs every POLL_MS milliseconds.
   *
   * Why polling instead of a one-shot DOMContentLoaded call?
   *   1. The floating chat popup is conditionally rendered (rx.cond).
   *      Its container appears and disappears from the DOM as the user
   *      opens/closes the popup.  Polling detects both events.
   *   2. SPA navigation (Reflex/Next.js) swaps page content without a full
   *      reload, so a one-time setup would miss containers on other routes.
   */
  function poll() {
    IDS.forEach(function (id) {
      var el = document.getElementById(id);
      el ? setup(id) : teardown(id);
    });
    setTimeout(poll, POLL_MS);
  }

  /* ── bootstrap ──────────────────────────────────────────────────────────── */

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      poll();
    });
  } else {
    poll(); /* DOM already ready (script loaded with defer or at end of body) */
  }
})();
