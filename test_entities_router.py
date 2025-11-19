from kg.api.entities_router import entities_router

print("Entities router prefix:", entities_router.prefix)
print("Number of routes in entities_router:", len(entities_router.routes))

for route in entities_router.routes:
    print(f"Route path: {route.path}")
    print(f"Methods: {route.methods}")
    # In FastAPI, route.path already includes the router's prefix
    print(f"Actual full path: {route.path}")
    print("---")