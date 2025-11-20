from playwright.sync_api import sync_playwright

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Navigate to the app
            page.goto("http://localhost:8080")

            # 2. Wait for key elements
            # Check if main container exists and has correct class (slate-950)
            # Since NiceGUI might not expose classes directly in a simple way on body,
            # we look for the div we created.

            # We added a div with class "w-full h-screen flex flex-row overflow-hidden bg-slate-950"
            # Wait for it to be visible
            # page.wait_for_selector(".bg-slate-950") # This might be too generic, but let's try.

            # Check for "AUDIOPUB" label
            # It is in a label component.
            page.wait_for_selector("text=AUDIOPUB")

            # Check for "system_log.sh"
            page.wait_for_selector("text=system_log.sh")

            # Check for "NEURAL VOICE"
            page.wait_for_selector("text=NEURAL VOICE")

            # 3. Take screenshot
            page.screenshot(path="verification.png")
            print("Screenshot taken: verification.png")

        except Exception as e:
            print(f"Error: {e}")
            # Take screenshot anyway if possible
            try:
                page.screenshot(path="error_verification.png")
            except:
                pass
        finally:
            browser.close()

if __name__ == "__main__":
    verify_ui()
