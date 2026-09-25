"""Headless verification for prototype/index.html (acceptance of T2).

Run: $MIMO_PYTHON scripts/verify_prototype.py
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parent.parent / "prototype" / "index.html"
URL = HTML.as_uri()


def snap(page):
    return page.evaluate("window.__game.snapshot()")


def wait_head_move(page, prev, timeout=4.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = snap(page)
        h = s["snake"][0]
        if h["x"] != prev["x"] or h["y"] != prev["y"]:
            return s
        time.sleep(0.03)
    raise AssertionError(f"snake head did not move within {timeout}s (prev={prev})")


def wait_state(page, want, timeout=8.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = snap(page)
        if s["state"] == want:
            return s
        time.sleep(0.05)
    raise AssertionError(f"state != {want} within {timeout}s, last={snap(page)}")


def steer_to_food(page, max_steps=80):
    """Greedy two-axis navigation: align Y first, then X."""
    for _ in range(max_steps):
        s = snap(page)
        if s["state"] != "play":
            return s
        if s["score"] >= 10:
            return s
        h, f = s["snake"][0], s["food"]
        d = s["dir"]
        if h["y"] != f["y"]:
            want = "ArrowUp" if f["y"] < h["y"] else "ArrowDown"
            if (want == "ArrowDown" and d["y"] == -1) or (want == "ArrowUp" and d["y"] == 1):
                # would be a 180 reversal; sidestep horizontally first
                want = "ArrowRight" if h["x"] < f["x"] else "ArrowLeft"
                if (want == "ArrowRight" and d["x"] == -1) or (want == "ArrowLeft" and d["x"] == 1):
                    want = "ArrowLeft" if want == "ArrowRight" else "ArrowRight"
        else:
            want = "ArrowLeft" if f["x"] < h["x"] else ("ArrowRight" if f["x"] > h["x"] else None)
        prev = h
        if want:
            page.keyboard.press(want)
        wait_head_move(page, prev)
    raise AssertionError("did not reach food within step budget")


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        # pre-seed best to verify persistence read path deterministically
        page.goto(URL)
        page.evaluate("localStorage.clear(); localStorage.setItem('snake-best', '7')")
        page.reload()
        page.wait_for_load_state("load")
        page.wait_for_timeout(200)

        s = snap(page)
        assert s["state"] == "start", s
        assert s["best"] == 7, f"best not read from localStorage: {s}"
        print("PASS start state + best=7 loaded from localStorage")

        page.keyboard.press("Enter")
        s = wait_state(page, "play")
        h0 = s["snake"][0]
        s1 = wait_head_move(page, h0)
        assert s1["snake"][0]["x"] == h0["x"] + 1, f"snake should move right: {h0} -> {s1['snake'][0]}"
        print("PASS snake advances per tick")

        page.keyboard.press("ArrowDown")
        prev = s1["snake"][0]
        s2 = wait_head_move(page, prev)
        assert s2["dir"] == {"x": 0, "y": 1}, f"turn failed: {s2['dir']}"
        assert s2["snake"][0]["y"] == prev["y"] + 1, f"head should move down: {prev} -> {s2['snake'][0]}"

        page.keyboard.press("ArrowUp")  # 180° reversal must be ignored
        prev = s2["snake"][0]
        s3 = wait_head_move(page, prev)
        assert s3["dir"] == {"x": 0, "y": 1}, f"reversal not ignored: {s3['dir']}"
        assert s3["snake"][0]["y"] == prev["y"] + 1, "head should still move down"
        print("PASS turn + 180-degree reversal guard")

        steer_to_food(page)
        s = snap(page)
        assert s["score"] == 10, f"expected score 10 after eating food: {s}"
        assert s["tickMs"] == 196, f"tick should speed up after food: {s['tickMs']}"
        print("PASS food eaten: score=10, tick=196ms")

        # drive into the top wall to die
        deadline = time.time() + 12
        while snap(page)["state"] == "play" and time.time() < deadline:
            s = snap(page)
            d = s["dir"]
            if d["y"] == 1:            # moving down: cannot reverse, sidestep first
                key = "ArrowLeft" if d["x"] != -1 else "ArrowRight"
            else:                      # up or horizontal: head for the top wall
                key = "ArrowUp"
            page.keyboard.press(key)
            time.sleep(0.22)
        s = wait_state(page, "over", timeout=6)
        final_score = s["score"]
        assert final_score >= 10, s
        stored = page.evaluate("localStorage.getItem('snake-best')")
        assert stored == str(final_score), f"best not persisted: {stored} != {final_score}"
        print(f"PASS wall death -> game over, best={final_score} persisted")

        # restart from game over
        page.keyboard.press("Enter")
        s = wait_state(page, "play")
        assert s["score"] == 0 and s["best"] == final_score, s
        # pause via space
        page.keyboard.press(" ")
        s = snap(page)
        assert s["state"] == "pause", s
        page.keyboard.press(" ")
        s = snap(page)
        assert s["state"] == "play", s
        print("PASS restart + pause/resume")

        # reload: best survives
        page.reload()
        page.wait_for_load_state("load")
        page.wait_for_timeout(150)
        s = snap(page)
        assert s["state"] == "start" and s["best"] == final_score, s
        print(f"PASS best={final_score} survives reload")

        browser.close()

    if errors:
        print("FAIL page errors:", json.dumps(errors, ensure_ascii=False))
        sys.exit(1)
    print("PASS no JS/console errors")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
