from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.readlines()

setup(
    name="depthai_pipeline_graph",
    version="0.0.2",
    packages=[*find_packages()],
    entry_points={
        'console_scripts': [
            'pipeline_graph = depthai_pipeline_graph.pipeline_graph:main'
        ]
    },
    author="geaxgx",
    include_package_data=True,
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    description="Tool to create graphs oh DepthAI pipelines",


    python_requires=">=3.6",
    install_requires=list(open("requirements.txt")),
)
