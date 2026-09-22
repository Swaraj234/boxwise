# AI Usage Log

## Tools Used

* **Claude (Anthropic)** — used for initial design discussions, reviewing an early version of the project, identifying potential issues, and helping prepare structured prompts for implementation.
* **ChatGPT (OpenAI)** — used during development to understand the assignment, discuss implementation decisions, troubleshoot issues, review test results, improve documentation, and prepare the project for submission.
* **Coding assistant** — used to apply selected code changes based on prompts and instructions that I reviewed and adapted.

I treated these tools as development assistants rather than as a replacement for understanding or testing the implementation.

## Prompts Given

The prompts were mainly focused on understanding the assignment and solving specific development problems.

Some examples include:

* Asked AI to break the assignment into smaller implementation steps before starting development.
* Asked for different approaches to the 3D box-packing problem, including their assumptions and limitations.
* Discussed important requirements such as units, product rotation, weight limits, duplicate SKUs, order size limits, and box-selection tie-breaking.
* Asked AI to review the implementation against the assignment requirements and identify missing or incorrect parts.
* Asked for help debugging Django, pytest, Git, configuration, and API issues.
* Asked AI to review test results and code coverage.
* Asked for help improving the README and other project documentation.
* Used targeted prompts for specific implementation issues instead of asking the AI to generate the entire project blindly.

## Output Accepted

I accepted AI suggestions when they matched the assignment requirements and made the implementation clearer or more reliable.

Examples include:

* Using a deterministic approach for the 3D packing problem.
* Considering all six rotations of an item.
* Performing weight, volume, and basic dimension checks before the geometric packing step.
* Keeping the packing logic independent from Django.
* Sorting feasible boxes by cost, then volume, then numeric box ID.
* Adding tests for edge cases such as exact fits, rotations, weight limits, geometry failures, duplicate SKUs, and deterministic behaviour.
* Replacing an unsafe `assert` used for a runtime validation with an explicit exception.
* Improving project documentation and explaining the design decisions more clearly.

I did not accept these suggestions automatically. I reviewed the changes and checked their effect on the existing code and tests.

## Output Rejected or Modified

Some AI-generated output was changed or rejected when it did not accurately represent the project.

For example:

* I modified documentation examples when they did not match the actual implementation.
* I did not use AI-generated explanations or reflections word-for-word when they were supposed to represent my own understanding.
* Some suggested implementation approaches were changed to better fit the assignment requirements and the existing project structure.
* I corrected suggestions when they introduced unnecessary complexity instead of solving the actual requirement.
* I did not accept generated test results or assume that a claimed fix had been applied without checking the files.

The final code was kept only after reviewing the actual changes and running the project locally.

## Mistakes AI Made

AI was useful during development, but it was not always correct.

One important example was a README worked example. An earlier version claimed that two books and a mug could fit inside a particular box. The height calculation was incorrect because the mug's smallest dimension was still too large for the remaining height. I caught this while reviewing the example and corrected the documentation.

There was also a tie-breaking issue where IDs could be treated as strings. In that situation, an ID such as `10` could be ordered before `2`, even though the required comparison was numeric. This was identified and corrected, and tests were added to cover the case.

Another issue was that an earlier coding-assistant response indicated that some requested changes had been completed, but the changes were not actually present in the project files. This reinforced the need to check the actual files and diffs instead of relying on the assistant's response.

These issues showed me that AI-generated output still needs to be reviewed and tested, especially when the result affects application behaviour.

## How I Verified the Final Code

I verified the final implementation locally instead of relying on AI-generated results.

I ran:

```text
python manage.py check
pytest
coverage run -m pytest
coverage report
ruff check .
ruff format --check .
```

The final test run produced:

* **44 tests passed**
* **0 tests failed**
* **Packing coverage: 92.57%**
* **Selection coverage: 100%**
* **Overall coverage: 95.21%**

The tests included API behaviour, model constraints, box selection, packing pre-checks, exact-fit boundaries, rotations, geometry failures, deterministic behaviour, performance with 200 items, and brute-force cross-checking.

I also reviewed the actual code changes and compared versions when applying fixes. For documentation, I checked the implementation and test results rather than assuming that an AI-generated example was correct.

## My Takeaway

AI saved time during the project, especially when I was trying to understand the packing problem, find edge cases, debug issues, and review the implementation.

However, I found that the most important part was verifying the suggestions myself. AI could suggest an approach or identify a possible problem, but I still had to understand the change, check whether it matched the assignment, run the code, and verify the result.

For this project, I used AI mainly as a **development and review assistant**, while keeping responsibility for the final implementation, testing, and technical decisions.
