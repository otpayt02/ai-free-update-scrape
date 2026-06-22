# Prompt Family: execution_plan

## Purpose
Step-by-step build or action sequence with halt conditions.

## Template

```
You are a senior engineer. Convert the following goal into a numbered build sequence:
- Each step has: action, output artifact, halt condition.
- No step proceeds if its halt condition is not met.
- Flag any step that requires external dependencies or credentials.

Goal: {goal}
```
