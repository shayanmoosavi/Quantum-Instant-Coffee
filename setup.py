from setuptools import setup, find_packages


setup(
    name="quantum_instant_coffee",
    version="2.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "pandas",
        "rich",
        "pyyaml"
    ],
    extras_requires={
        "fetch_info": [
            "requests",
            "lxml",
            "beautifulsoup4"
        ],
        "all": [
            "numpy",
            "matplotlib",
            "pandas",
            "rich",
            "pyyaml",
            "requests",
            "beautifulsoup4",
            "lxml"
        ]
    }
)