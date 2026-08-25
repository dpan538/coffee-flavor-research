# Randomization Audit

The frozen schedule contains 192 session slots and 1,512 blinded presentation
slots. Twelve reference slots each receive six sessions of eleven samples (792
presentations); sixty ordinary-user slots each receive two sessions of six
samples (720 presentations).

Every planned sample appears exactly six times in the reference schedule and
five or six times in the ordinary-user schedule. No session repeats a sample,
sequence positions are contiguous, and blinded codes are unique within a
session. Each ordinary-user presentation has one mandatory Q1 slot and four
conditional Q2–Q5 slots.

```text
RANDOMIZATION_SHA256=eb7aa3fbfa6daf2d94819c007c42cdb43efcbbe4540335f231907b0b4a6edb4b
QUESTION_ASSIGNMENT_SHA256=3e48c83feff27767cf68792f6a9e4c51e80c21aabf0cb419a1cfb02261a528e9
RANDOMIZATION_VALIDATION_PASS=true
QUESTION_ASSIGNMENT_SLOT_COUNT=3600
```
