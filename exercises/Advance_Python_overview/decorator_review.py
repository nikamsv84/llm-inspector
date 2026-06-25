import time
import functools
from typing import Callable, Any


# =====================================================================
# ۱. تعریف دکوراتور پیشرفته با تایپ هینتینگ و حفظ هویت تابع
# =====================================================================
def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    این دکوراتور زمان اجرای هر تابعی را محاسبه و چاپ می‌کند.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time: float = time.time()  # ثبت زمان دقیق شروع

        # اجرای تابع اصلی و ذخیره خروجی آن (هر چه که باشد)
        result: Any = func(*args, **kwargs)

        end_time: float = time.time()  # ثبت زمان دقیق پایان
        execution_time: float = end_time - start_time

        # چاپ نام تابع اصلی و زمان اجرای آن تا ۶ رقم اعشار
        print(f"[TIMER] Function '{func.__name__}' took {execution_time:.6f} seconds to execute.")

        return result  # بازگرداندن نتیجه تابع اصلی به برنامه

    return wrapper


# =====================================================================
# ۲. تعریف توابع مختلف و اعمال دکوراتور @timer روی آن‌ها
# =====================================================================

@timer
def heavy_loop(n: int) -> int:
    """این تابع یک حلقه سنگین برای محاسبه مجموع اعداد اجرا می‌کند."""
    print(f"\n-> Starting heavy loop with n={n}...")
    total: int = 0
    for i in range(n):
        total += i
    return total


@timer
def simulate_network_delay(url: str) -> str:
    """این تابع یک تأخیر مصنوعی ۱.۲ ثانیه‌ای (مثل دانلود از شبکه) ایجاد می‌کند."""
    print(f"\n-> Simulating network request to '{url}'...")
    time.sleep(1.2)  # خواباندن برنامه به مدت ۱.۲ ثانیه
    return "Data package successfully downloaded!"


@timer
def simple_greeting(name: str, age: int) -> str:
    """یک تابع خیلی سریع و ساده برای خوش‌آمدگویی."""
    print(f"\n-> Processing greeting for {name}...")
    return f"Hello {name}, you are {age} years old."


# =====================================================================
# ۳. اجرای تست و چاپ خروجی‌ها
# =====================================================================
if __name__ == "__main__":
    print("=== STARTING DECORATOR TESTING ===")

    # تست تابع اول: حلقه سنگین (با ورودی پوزیشنی)
    loop_result = heavy_loop(5_000_000)
    print(f"Result of heavy_loop: {loop_result}")

    # تست تابع دوم: شبیه‌سازی تاخیر شبکه (با ورودی کی‌ورد)
    network_result = simulate_network_delay(url="https://api.github.com/users")
    print(f"Result of network_delay: {network_result}")

    # تست تابع سوم: یک تابع بسیار سریع با چند ورودی مختلف
    greeting_result = simple_greeting("Ali", 24)
    print(f"Result of simple_greeting: {greeting_result}")

    print("\n=== TESTING FUNCTION IDENTITY ===")
    # تست جادوی functools.wraps (آیا نام و مستندات تابع اصلی حفظ شده‌اند؟)
    print(f"Real Function Name: {heavy_loop.__name__}")
    print(f"Real Function Docstring: '{heavy_loop.__doc__}'")

    print("\n=== TESTING FINISHED ===")