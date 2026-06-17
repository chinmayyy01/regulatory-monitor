from backend.graph.graph import graph

config = {
    "configurable": {
        "thread_id": "demo-thread"
    }
}

print("QUESTION 1")
result = graph.invoke(
    {
        "question": "What changed in ECLGS?"
    },
    config=config,
)
print(result["answer"])

print()

print("QUESTION 2")
result = graph.invoke(
    {
        "question": "Who is affected?"
    },
    config=config,
)
print(result["answer"])