from database import open_pool, release_intercepted_request, close_pool


def test_drop_latest():
    open_pool()
    try:
        # فرض می‌کنیم آی‌دی ریکویست جدیدت رو می‌دونی، یا آخرین ID رو می‌گیریم
        request_id = input("Enter request ID to DROP: ")

        released = release_intercepted_request(int(request_id), action="dropped")
        print(f"Drop Signal Sent: {released}")

    finally:
        close_pool()


if __name__ == "__main__":
    test_drop_latest()