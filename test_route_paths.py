from fastapi import FastAPI, APIRouter
from kg.api.entities_router import entities_router
from kg.api import router as main_router

# Create a test app
test_app = FastAPI()

# Include the main router (which includes all sub-routers) with the API prefix
test_app.include_router(main_router, prefix="/api/v1")

print("=== Testing Actual Route Paths in App ===")
print(f"Entities router prefix: {entities_router.prefix}")
print()

# Check routes through entities_router
print("Routes through entities_router:")
for route in entities_router.routes:
    print(f"Route path: {route.path}")
    print(f"Methods: {route.methods}")
    # The route.path already includes the router's prefix
    print(f"Actual full path: {route.path}")  # In FastAPI, route.path includes the router prefix
    print("---")

print()
print("=== Testing App-Level Routes ===")
# Check all routes in the app
total_routes = 0
for route in test_app.routes:
    if hasattr(route, "path"):
        print(f"Path: {route.path}")
        total_routes += 1

print(f"Total routes in app: {total_routes}")