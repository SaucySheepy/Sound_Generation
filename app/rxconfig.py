import reflex as rx

config = rx.Config(
    app_name="app",
    api_url="http://192.168.3.205:8000",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)