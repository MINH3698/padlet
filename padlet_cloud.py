import asyncio
import os
import random
import sys
import time
from playwright.async_api import async_playwright

# Lấy cấu hình từ biến môi trường của GitHub Actions
URL = os.getenv("PADLET_URL", "https://padlet.com/tamgiacmach232781/bang-c-tuan-le-hoc-tap-suot-oi-s023lmwy9guiiwlr88od/wish/J24jale5yg34Q0A1")
TARGET_LIKES = int(os.getenv("TARGET_LIKES", "50"))
VM_ID = os.getenv("VM_ID", "1")
CONCURRENCY = int(os.getenv("CONCURRENCY", "2"))

HO_LIST = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Đoàn", "Mai"
]

DEM_LIST = [
    "Văn", "Thị", "Đức", "Hoàng", "Ngọc", "Thanh", "Minh", "Đình", "Quốc",
    "Hữu", "Tuấn", "Thảo", "Gia", "Bảo", "Xuân", "Phương", "Hải", "Khánh"
]

TEN_LIST = [
    "Anh", "Bình", "Cường", "Dũng", "Đạt", "Giang", "Hà", "Hải", "Hưng",
    "Huy", "Khánh", "Linh", "Long", "Minh", "Nam", "Nghĩa", "Phong", "Phúc",
    "Quân", "Sơn", "Thắng", "Thịnh", "Tiến", "Trung", "Tuấn", "Tùng", "Việt",
    "Vy", "Trang", "Mai", "Lan", "Nga", "Hương", "Hạnh", "Ngân", "Quỳnh",
    "Thảo", "Trâm", "Yến", "Châu", "Duyên", "Hoa", "Loan", "My", "Nhung"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
]

def tao_ten():
    return f"{random.choice(HO_LIST)} {random.choice(DEM_LIST)} {random.choice(TEN_LIST)}"

async def thuc_hien_mot_luot(browser, url, ten):
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1280, "height": 800},
        locale="vi-VN"
    )
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        dialog = page.locator("[role='dialog']")
        await dialog.wait_for(state="visible", timeout=30000)
        
        reaction_btn = dialog.locator(
            "[data-testid='surfacePostReactionEmojiAccumulatedReactionsButton-2764'], button[aria-label*='heart'], button[aria-label*='tim']"
        ).first
        await reaction_btn.wait_for(state="visible", timeout=12000)
        await reaction_btn.scroll_into_view_if_needed()
        await reaction_btn.click()
        
        name_input = page.locator("input[aria-label='Your name'], input[aria-label='Tên của bạn'], input[placeholder*='name']")
        try:
            await name_input.wait_for(state="visible", timeout=3000)
            await name_input.fill(ten)
            done_btn = page.locator("button[data-testid='surfaceGuestIdModalDoneButton']")
            if await done_btn.is_visible():
                await done_btn.click()
            else:
                await name_input.press("Enter")
        except Exception:
            pass
            
        await asyncio.sleep(2.5)
        try:
            so_tim = await reaction_btn.inner_text()
        except Exception:
            so_tim = "Đã tăng"
        return True, so_tim
    except Exception as e:
        return False, str(e).split('\n')[0]
    finally:
        try:
            await page.close()
        except Exception:
            pass
        try:
            await context.close()
        except Exception:
            pass

async def worker(w_id, browser, stats, lock, stop_event):
    while not stop_event.is_set():
        async with lock:
            if stats["da_nhan"] >= TARGET_LIKES:
                break
            stats["da_nhan"] += 1
            idx = stats["da_nhan"]
            
        ten = tao_ten()
        t0 = time.time()
        ok, res = await thuc_hien_mot_luot(browser, URL, ten)
        dur = round(time.time() - t0, 1)
        
        async with lock:
            stats["da_chay"] += 1
            if ok:
                stats["thanh_cong"] += 1
                msg = f"-> ĐÃ TĂNG TIM! (Tổng: {res}) ({dur}s)"
            else:
                msg = f"-> Thất bại! ({res}) ({dur}s)"
            print(f"[Máy ảo {VM_ID}] [Tab {w_id}] [{idx}/{TARGET_LIKES}] Tên: {ten:<20} {msg}")
            
        await asyncio.sleep(random.uniform(1.2, 2.5))

async def main():
    print("=" * 65)
    print(f"  MÁY ẢO GITHUB ACTIONS #{VM_ID} ĐANG CHẠY")
    print(f"  - Mục tiêu: {TARGET_LIKES} lượt tim")
    print(f"  - Số tab song song: {CONCURRENCY} tabs")
    print("=" * 65)
    
    stats = {"da_nhan": 0, "da_chay": 0, "thanh_cong": 0}
    lock = asyncio.Lock()
    stop_event = asyncio.Event()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        tasks = [asyncio.create_task(worker(i, browser, stats, lock, stop_event)) for i in range(1, CONCURRENCY + 1)]
        await asyncio.gather(*tasks)
        await browser.close()
        
    print(f"\n[✓] MÁY ẢO #{VM_ID} HOÀN THÀNH: Thành công {stats['thanh_cong']}/{TARGET_LIKES} lượt tim!")

if __name__ == "__main__":
    asyncio.run(main())
