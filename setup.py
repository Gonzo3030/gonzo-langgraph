from setuptools import setup, find_packages

setup(
    name="gonzo-langgraph",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langgraph>=0.0.1",
        "langsmith",
        "pydantic>=2.0.0",
        "numpy",
        "pytest",
        "pytest-asyncio",
    ],
    python_requires=">=3.9",
)