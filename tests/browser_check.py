"""Browser acceptance checks against a running app. Uses synthetic sample replay only."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("APP_URL", "http://127.0.0.1:8018")
OUT = Path("test-results")
OUT.mkdir(exist_ok=True)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="msedge")
        context = browser.new_context(viewport={"width":1440,"height":1000},device_scale_factor=1)
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_role("heading",name="Every conversation. A little more clarity.")).to_be_visible()
        page.get_by_role("heading",name="More context. Better conversations.").scroll_into_view_if_needed()
        expect(page.locator('.intelligence-copy')).to_have_css('opacity','1')
        page.get_by_role("heading",name="From the first word to the next best step.").scroll_into_view_if_needed()
        expect(page.locator('.process-grid article').first).to_have_css('opacity','1')
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        page.screenshot(path=str(OUT/"landing-desktop.png"),full_page=True,animations="disabled")
        page.get_by_role("link",name="Analyze a call",exact=True).click()
        expect(page.get_by_role("heading",name="Find the signal.")).to_be_visible()
        page.screenshot(path=str(OUT/"workspace-desktop.png"),full_page=True)
        # Validate file picker feedback without making an AI call.
        page.get_by_label("Call file").set_input_files({"name":"bad.exe","mimeType":"application/octet-stream","buffer":b"invalid"})
        expect(page.get_by_role("alert")).to_contain_text("Choose an MP3")
        page.get_by_role("button",name="Dismiss error").click()
        page.get_by_label("Call file").set_input_files({"name":"call.txt","mimeType":"text/plain","buffer":b"Customer: I need help.\nAgent: I can help."})
        expect(page.get_by_role("button",name="Analyze conversation")).to_be_enabled()
        page.get_by_role("button",name="Explore a sample",exact=True).click()
        page.get_by_label("Choose a conversation").select_option("billing-refund")
        page.get_by_label("Demonstrate model fallback").check()
        page.get_by_role("button",name="Replay sample",exact=True).click()
        expect(page.get_by_text("Sample replay · Curated example results, not live AI analysis.")).to_be_visible()
        expect(page.get_by_role("heading",name="Duplicate subscription charge")).to_be_visible(timeout=20000)
        page.get_by_role("tab",name="Quality score").click()
        expect(page.get_by_role("heading",name="empathy",exact=True)).to_be_visible(timeout=20000)
        page.screenshot(path=str(OUT/"quality-desktop.png"),full_page=True)
        page.get_by_role("button",name="View transcript segment 2",exact=True).first.click()
        expect(page.locator("#segment-2")).to_be_focused()
        expect(page.locator("#segment-2")).to_contain_text("sorry for the confusion")
        page.get_by_role("tab",name="Activity",exact=True).click()
        expect(page.get_by_text("SIMULATION: switching to fallback fixture",exact=True)).to_be_visible()
        with page.expect_download() as download:
            page.get_by_role("link",name="Export JSON").click()
        download.value.save_as(str(OUT/"export.json"))
        exported=json.loads((OUT/"export.json").read_text())
        assert exported["demo"] and exported["status"]=="completed"
        call_url=page.url
        page.reload();page.wait_for_load_state("networkidle")
        expect(page.get_by_role("heading",name="The duplicate charge",exact=True)).to_be_visible()
        page.get_by_role("tab",name="Summary",exact=True).click()
        page.screenshot(path=str(OUT/"result-desktop.png"),full_page=True)
        # Exercise the upload UI response path with a mocked network result.
        page.get_by_role("button",name="New analysis",exact=True).click()
        page.get_by_label("Call file").set_input_files({"name":"synthetic.txt","mimeType":"text/plain","buffer":b"Agent: Test upload."})
        page.route("**/api/calls",lambda route:route.fulfill(status=202,json=exported) if route.request.method=="POST" else route.continue_())
        page.get_by_role("button",name="Analyze conversation",exact=True).click()
        expect(page.get_by_role("heading",name="The duplicate charge",exact=True)).to_be_visible()
        page.unroute("**/api/calls")
        # Mobile and reduced-motion checks use the same real saved result.
        page.emulate_media(reduced_motion="reduce")
        page.set_viewport_size({"width":375,"height":812})
        page.goto(BASE);page.wait_for_load_state("networkidle")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert page.locator(".wave-bars i").first.evaluate("e=>getComputedStyle(e).animationName")=="none"
        page.screenshot(path=str(OUT/"landing-mobile.png"),full_page=True)
        page.goto(call_url);page.wait_for_load_state("networkidle")
        expect(page.get_by_role("heading",name="The duplicate charge",exact=True)).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.get_by_role("button",name="Open history",exact=True).click()
        expect(page.locator(".sidebar-open")).to_be_visible()
        page.keyboard.press('Escape')
        expect(page.get_by_role("button",name="Open history",exact=True)).to_be_focused()
        page.screenshot(path=str(OUT/"result-mobile.png"),full_page=True)
        page.set_viewport_size({"width":812,"height":375})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert not errors, errors
        print("PASS: landing, file validation, replay, quality, evidence focus, fallback, export, history reload, mocked upload, mobile, reduced motion, no JS errors")
        context.close();browser.close()


if __name__ == "__main__":
    run()
