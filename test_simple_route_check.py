from kg.api.entities_router import EntityRouter

# Create a router instance
router = EntityRouter()

# Print the router's prefix
print(f"Router prefix: {router.prefix}")

# Print each route's path
for route in router.router.routes:
    print(f"Route path: {route.path}")
    print(f"Full path: {router.prefix}{route.path}")
    print(f"Methods: {route.methods}")
    print("---")