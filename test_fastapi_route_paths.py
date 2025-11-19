from fastapi import APIRouter

# Create a router with prefix
router = APIRouter(prefix="/test")

# Register routes
@router.post("", tags=["test"], summary="Create test")
def create_test():
    pass

@router.get("/{item_id}", tags=["test"], summary="Get test")
def get_test(item_id: str):
    pass

@router.get("", tags=["test"], summary="Get all tests")
def get_all_tests():
    pass

# Print route information
print("Router prefix:", router.prefix)
print("Number of routes:", len(router.routes))
for i, route in enumerate(router.routes):
    print(f"\nRoute {i+1}:")
    print(f"  Path: {route.path}")
    print(f"  Methods: {route.methods}")
    print(f"  Tags: {route.tags}")
    print(f"  Summary: {route.summary}")

# Check the full path
print(f"\n\nFull path for create_test: {router.prefix}{router.routes[0].path}")