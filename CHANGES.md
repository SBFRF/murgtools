# Changes: normalize package name to lowercase (murgtools)

This branch was created to normalize any remaining textual references to the package name from "murgTools" (capital T) to "murgtools" (lowercase).

What I did:
- Performed a case-insensitive search for the string "murgTools" across the repository and inspected the top-matching files. The search results did not find any in-repo file contents containing the exact camel-case substring "murgTools" that needed editing. The repository files already appear to use the lowercase `murgtools` package name.
- Because there were no literal matches to replace, I did not modify existing source files to avoid introducing unnecessary changes.

References:
- Code search used: https://github.com/SBFRF/murgtools/search?q=murgTools&type=code

If you want me to make broader edits (for example, run a case-insensitive replace of variations, update CI badges, or update any URLs found in history), tell me and I will prepare those changes in this branch.

Signed-off-by: GitHub Copilot <copilot@github.com>