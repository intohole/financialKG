from kg.api.news_router import news_router

print("News router prefix:", news_router.prefix)
print("Number of routes in news_router:", len(news_router.routes))

for route in news_router.routes:
    print(f"Route path: {route.path}")
    print(f"Methods: {route.methods}")
    print("---")