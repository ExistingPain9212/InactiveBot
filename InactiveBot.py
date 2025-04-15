# CommitTest.py
import time

# Create a dummy file
with open("dummy.txt", "w") as f:
    f.write("This is a test file for commit check.\n")

print("🕐 Sleeping for 60 seconds to simulate runtime...")
time.sleep(60)
print("✅ Dummy file created and script completed.")
