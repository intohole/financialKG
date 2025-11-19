from fastapi import FastAPI
from kg.api import router

# Create a test FastAPI app and include the main router
app = FastAPI()
app.include_router(router, prefix="/api/v1")

print("=== Application Routes ===")
print(f"Total routes: {len(app.routes)}")
print()

# Group routes by their tags
tagged_routes = {}
for route in app.routes:
    if hasattr(route, 'tags') and route.tags:
        tag = route.tags[0]
        if tag not in tagged_routes:
            tagged_routes[tag] = []
        tagged_routes[tag].append(route)

# Print routes grouped by tags
for tag, routes in tagged_routes.items():
    print(f"Tag: {tag}")
    for route in routes:
        methods = getattr(route, 'methods', ['GET'])
        path = route.path
        print(f"  {[m for m in methods]} {path}")
    print()

print("=== Checking for duplicate routes ===")
route_paths = {}
duplicates_found = False

for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = tuple(sorted(route.methods))
        path = route.path
        key = (methods, path)
        if key in route_paths:
            print(f"Duplicate route found: {methods} {path}")
            print(f"  Original: {route_paths[key]}")
            print(f"  Duplicate: {route}")
            duplicates_found = True
        else:
            route_paths[key] = route

if not duplicates_found:
    print("No duplicate routes found.")
