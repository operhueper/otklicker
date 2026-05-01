"""Generate 5 launch post images for @otklicker channel.

Run from repo root:
    python3 promo/images/launch/generate.py
"""

import sys
from pathlib import Path

# Allow import from marketing-engine/src
ENGINE_SRC = Path(__file__).resolve().parents[3] / "marketing-engine" / "src"
sys.path.insert(0, str(ENGINE_SRC))

from publisher.image_gen import generate_post_image  # noqa: E402

OUT = Path(__file__).resolve().parent


def main():
    posts = [
        # post-1-welcome.png — приветственный, шаблон feature
        # feature_tag=None убирает метку «Новая фича»: для приветственного поста она нерелевантна
        dict(
            filename="post-1-welcome.png",
            post_type="feature",
            headline="Привет, мы откликер",
            body_text="Telegram-бот для поиска работы через HH.ru. Резюме, отклики, ответы HR — всё в одном чате.",
            feature_tag=None,
        ),
        # post-2-how-it-works.png — как работает, шаблон tip
        # Полный body рендерится без обрезания по первому предложению
        dict(
            filename="post-2-how-it-works.png",
            post_type="career_tip",
            headline="Как работает откликер",
            body_text="Резюме голосом. Тиндер вакансий. AI-сопроводительные письма. Ответы HR прямо в Telegram.",
        ),
        # post-3-15-limit.png — потолок 15, шаблон number
        # Без em-dash в headline; eyebrow=None и footer_note=None убирают dbsales-подписи
        dict(
            filename="post-3-15-limit.png",
            post_type="numbers",
            headline="откликов в день, наш потолок",
            body_text="Не лимит HH. Это столько, сколько вытягивает один человек.",
            accent_number="15",
            eyebrow=None,
            footer_note=None,
        ),
        # post-4-cover-letter.png — сопроводительное, шаблон quote
        # Оборачиваем body в «кавычки» чтобы quote-экстрактор нашёл цитату
        dict(
            filename="post-4-cover-letter.png",
            post_type="hr_view",
            headline="Сопроводительное под каждую вакансию",
            body_text="«AI парсит вакансию, берёт ваш профиль, сшивает письмо на 4-6 предложений. Не шаблон.»",
        ),
        # post-5-pricing.png — тарифы, шаблон number
        # eyebrow=None и footer_note=None убирают «в цифрах» / «медиана по рынку, 2026»
        dict(
            filename="post-5-pricing.png",
            post_type="numbers",
            headline="рублей за 3 недели активного поиска",
            body_text="Бесплатный тариф 0 руб., активный 790 руб. Без подписки.",
            accent_number="790",
            eyebrow=None,
            footer_note=None,
        ),
    ]

    for post in posts:
        filename = post.pop("filename")
        out_path = OUT / filename
        result = generate_post_image(output_path=out_path, **post)
        size_kb = out_path.stat().st_size // 1024
        print(f"  {filename}  ({size_kb} KB)  -> {result}")

    print(f"\nДонe. 5 файлов в {OUT}")


if __name__ == "__main__":
    main()
