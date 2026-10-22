
import ast
import operator
from typing import Tuple, Union

import streamlit as st

st.set_page_config(page_title="Math Genie", page_icon="🧮")
st.title("🧮 Math Genie")
st.write("Your simple step-by-step math tutor")

level = st.sidebar.selectbox(
    "Choose difficulty",
    ["Beginner", "Regular", "Challenging"]
)

examples = {
    "Addition": "145 + 278",
    "Multiplication": "25 * 16",
    "Algebra": "2*x + 5 = 15",
    "Simple equation": "x + 7 = 12"
}

example = st.sidebar.selectbox("Try an example", list(examples))
if st.sidebar.button("Use example"):
    st.session_state.problem = examples[example]

if "history" not in st.session_state:
    st.session_state.history = []

ops = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg
}

def calculate(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Expression):
        return calculate(node.body)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
        return ops[type(node.op)](calculate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in ops:
        a, b = calculate(node.left), calculate(node.right)
        if isinstance(node.op, ast.Pow) and abs(b) > 10:
            raise ValueError("Power is too large.")
        result = ops[type(node.op)](a, b)
        if abs(result) > 1e100:
            raise ValueError("Result is too large.")
        return result
    raise ValueError("Use numbers and basic operations only.")

def linear(node: ast.AST) -> Tuple[Union[int, float], Union[int, float]]:
    if isinstance(node, ast.Expression):
        return linear(node.body)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return (0, node.value)
    if isinstance(node, ast.Name) and node.id == "x":
        return (1, 0)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        a, b = linear(node.operand)
        return -a, -b
    if isinstance(node, ast.BinOp):
        a, b = linear(node.left)
        c, d = linear(node.right)
        if isinstance(node.op, ast.Add):
            return a + c, b + d
        if isinstance(node.op, ast.Sub):
            return a - c, b - d
        if isinstance(node.op, ast.Mult) and not (a and c):
            return a * d + c * b, b * d
        if isinstance(node.op, ast.Div) and c == 0 and d != 0:
            return a / d, b / d
    raise ValueError("Use a linear equation with one variable, x.")

def solve(problem):
    if "=" in problem:
        left, right = problem.split("=")
        a, b = linear(ast.parse(left.strip(), mode="eval"))
        c, d = linear(ast.parse(right.strip(), mode="eval"))
        coefficient, constant = a - c, d - b
        if coefficient == 0:
            return "Infinitely many solutions." if constant == 0 else "No solution."
        x = constant / coefficient
        return (
            f"Step 1: {problem}\n\n"
            f"Step 2: Collect x terms: {coefficient:g}x = {constant:g}\n\n"
            f"Step 3: Divide both sides by {coefficient:g}.\n\n"
            f"Final answer: x = {x:g}"
        )
    result = calculate(ast.parse(problem, mode="eval"))
    tip = "Follow the order of operations.\n\n" if level == "Beginner" else ""
    return f"{tip}Problem: {problem}\n\nFinal answer: {result:g}"

problem = st.text_area("Enter your math problem", key="problem")

if st.button("Solve", type="primary"):
    try:
        if not problem.strip() or len(problem) > 150:
            raise ValueError("Enter a problem under 150 characters.")
        answer = solve(problem.lower().replace("×", "*").replace("÷", "/"))
        st.session_state.history.append((problem, answer))
        st.subheader("Solution")
        st.markdown(answer.replace("\n", "  \n"))
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError):
        st.error("Invalid problem. Try an example from the sidebar.")

st.subheader("Conversation History")
for question, answer in reversed(st.session_state.history):
    with st.expander(question):
        st.markdown(answer.replace("\n", "  \n"))

if st.session_state.history:
    text = "\n\n".join(
        f"Problem: {q}\nSolution: {a}"
        for q, a in st.session_state.history
    )
    st.download_button("Export history", text, "math_history.txt")
    if st.button("Clear history"):
        st.session_state.history = []
        st.rerun()