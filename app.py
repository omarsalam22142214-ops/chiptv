import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
# السماح للمشغل بتاعك (حتى لو مرفوع على جيت هاب) يتصل بالسيرفر المحلي
CORS(app)

@app.route('/get_stream', methods=['GET'])
def get_stream():
    page_url = request.args.get('url')
    if not page_url:
        return jsonify({"success": False, "error": "لازم تبعت رابط الصفحة!"}), 400

    try:
        with sync_playwright() as p:
            # فتح متصفح مرئي (عشان تتخطى الإعلانات بنفسك)
            browser = p.chromium.launch(headless=False)
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()

            m3u8_link = None

            # مراقبة الشبكة لاصطياد الرابط
            def handle_response(response):
                nonlocal m3u8_link
                if ".m3u8" in response.url.lower():
                    m3u8_link = response.url
                    print(f"\n[!] تم اصطياد الرابط بنجاح: {m3u8_link}")

            page.on("response", handle_response)

            print(f"\n[+] جاري فتح الصفحة: {page_url}")
            page.goto(page_url, timeout=60000, wait_until="domcontentloaded")
            
            print("[+] المتصفح فتح قدامك! معاك 40 ثانية عشان تدوس Play وتقفل أي إعلان...")
            
            # الكود هيستنى 40 ثانية كحد أقصى، بس لو اصطاد الرابط هيقفل في ساعتها
            for _ in range(40):
                if m3u8_link:
                    break
                page.wait_for_timeout(1000)

            browser.close()

            if m3u8_link:
                return jsonify({"success": True, "stream_url": m3u8_link})
            else:
                print("[-] الوقت خلص ومفيش رابط ظهر.")
                return jsonify({"success": False, "error": "الوقت خلص (40 ثانية) ومقدرناش نصطاد الرابط. جرب تاني وخليك أسرع في تشغيل الفيديو."}), 404

    except Exception as e:
        print(f"[-] خطأ: {str(e)}")
        return jsonify({"success": False, "error": f"حصل خطأ أثناء الاستخراج: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)