from setuptools import setup, find_packages

setup(
    name="gensearch",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "gensearch=gensearch.cli:main",
        ],
    },
    description="Multi-site genealogy search, tree analysis, and fact checking tool",
)
