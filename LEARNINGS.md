# What I Learned

## 1. 3D Packing Problem

I learned that just checking the volume of a product is not enough to know if it will fit inside a box. I also have to check the length, width, and height of both the product and the box. Sometimes a product can have less volume than the box but still not fit because of its dimensions.

## 2. Algorithm Design

I learned that the 3D bin packing problem is more complicated than it looks because there can be different products, quantities, rotations, and weight limits. For this project, I used a deterministic heuristic approach because it is easier to implement, understand, and explain while still giving consistent results.

## 3. Edge Cases

While developing the project, I came across many edge cases that I had to handle. Some of them were:

* A product fitting only when it is rotated.
* Product weight being exactly equal to the box weight limit.
* Multiple quantities of the same product in an order.
* Products that fit individually but do not fit together in the same box.
* Product dimensions being larger than the box dimensions.

Handling these cases helped me understand why edge-case testing is important.

## 4. Testing

I learned how important it is to write test cases during development instead of waiting until the project is finished. I used tests to check the packing logic, validations, APIs, and different edge cases.

This also helped me find problems earlier and make changes without worrying about breaking existing functionality.

## 5. AI Usage

I used AI tools during the development process to help me understand concepts, find possible solutions, debug errors, and think about edge cases.

I did not just copy the generated code. I went
